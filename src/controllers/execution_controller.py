"""
Code execution controller.
Handles compile, run, verify, cancel, and status operations.
"""
import threading
import time
import sys
import os
from typing import Optional, Dict

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Cookie, Form, HTTPException, Request
from fastapi.responses import JSONResponse

from container_manager import get_container_manager
from language_executor.factory import get_executor_by_name
from models import ActiveProcess, CompilerConfig, UserSession
from .shared_utils import (
    get_or_create_session_id,
    update_session_activity,
    parse_request_data,
    increment_process_counter
)

router = APIRouter()

# These will be set by main.py through set_globals
active_processes: Dict[str, ActiveProcess] = {}
CONFIG: Optional[CompilerConfig] = None


def set_globals(processes, config):
    """Set global state variables for this controller."""
    global active_processes, CONFIG
    active_processes = processes
    CONFIG = config


@router.post("/compile", tags=["Code Execution"])
async def compile_code(
    request: Request,
    code: str = Form(None, description="Source code to compile"),
    language: str = Form(None, description="Programming language"),
    version: Optional[str] = Form(None),
    session_id: Optional[str] = Cookie(None),
):
    """Compile source code."""
    try:
        # Parse request data
        request_data = await parse_request_data(request)
        session_id = get_or_create_session_id(session_id)
        update_session_activity(session_id)

        if request_data["is_multi_file"]:
            # Multi-file request
            language = request_data["language"]
            files = request_data["files"]
            main_file = request_data["main_file"]

            # Convert Pydantic FileInfo models to executor FileInfo objects
            from language_executor.base import FileInfo as ExecutorFileInfo

            file_objects = [ExecutorFileInfo(f.name, f.content) for f in files]

            # Pass all files to the executor
            exec_version = version if version is not None else ""
            executor = get_executor_by_name(language, exec_version)
            success, output, output_path = executor.compile(
                file_objects, session_id, main_file
            )
        else:
            # Legacy form request
            if not code or not language:
                raise HTTPException(
                    status_code=400, detail="Code and language are required"
                )

            # Single file compilation (legacy)
            exec_version = version if version is not None else ""
            executor = get_executor_by_name(language, exec_version)
            success, output, output_path = executor.compile(code, session_id)

        response_data = {
            "success": success,
            "message": ("Compilation successful" if success else "Compilation failed"),
            "output": output,
            "file_path": None,
            "output_path": output_path,
        }

        response = JSONResponse(content=response_data, status_code=200)
        response.set_cookie(
            key="session_id", value=session_id, httponly=True, max_age=86400
        )
        return response
    except Exception as e:
        response_data = {
            "success": False,
            "message": f"Error during compilation: {str(e)}",
            "output": "",
            "file_path": None,
            "output_path": None,
        }
        response = JSONResponse(content=response_data, status_code=500)
        response.set_cookie(
            key="session_id", value=session_id, httponly=True, max_age=86400
        )
        return response


@router.post("/run", tags=["Code Execution"])
async def run_code(
    request: Request,
    code: str = Form(None),
    language: str = Form(None),
    timeout: int = Form(30),
    version: str = Form(None),
    session_id: str = Cookie(None),
):
    """Execute source code."""
    # Parse request data
    request_data = await parse_request_data(request)

    if request_data["is_multi_file"]:
        # Multi-file request
        language = request_data["language"]
        files = request_data["files"]
        main_file = request_data["main_file"]
        timeout = request_data.get("timeout", 30)

        # Find the main file content
        main_file_content = None
        for file_info in files:
            if file_info.name == main_file:
                main_file_content = file_info.content
                break

        if main_file_content is None:
            raise HTTPException(
                status_code=400, detail=f"Main file '{main_file}' not found"
            )

        code = main_file_content
    else:
        # Legacy form request
        if not code or not language:
            raise HTTPException(
                status_code=400, detail="Code and language are required"
            )
        files = None
        main_file = None

    session_id = get_or_create_session_id(session_id)
    execution_id = increment_process_counter()
    update_session_activity(session_id)
    
    if CONFIG is None or language not in CONFIG.compilers:
        print(f"DEBUG: CONFIG is None: {CONFIG is None}")
        if CONFIG is not None:
            print(f"DEBUG: CONFIG.compilers: {CONFIG.compilers}")
            print(f"DEBUG: language '{language}' in CONFIG.compilers: {language in CONFIG.compilers}")
        raise HTTPException(
            status_code=400, detail=f"Unsupported language: {language}"
        )
    
    active_processes[execution_id] = ActiveProcess(
        session_id=session_id,
        start_time=time.time(),
        cancelled=False,
        completed=False,
        timeout=timeout,
        language=language,
        operation_type="run",
    )

    def run_in_container():
        try:
            executor = get_executor_by_name(language, version)

            if request_data["is_multi_file"]:
                # Multi-file execution
                from language_executor.base import FileInfo as ExecutorFileInfo

                file_objects = [ExecutorFileInfo(f.name, f.content) for f in files]
                success, output, exit_code = executor.execute(
                    file_objects, session_id, timeout, main_file
                )
            else:
                # Legacy single file execution
                success, output, exit_code = executor.execute(code, session_id, timeout)

            if execution_id in active_processes:
                proc = active_processes[execution_id]
                proc.completed = True
                proc.success = success
                proc.output = output
                proc.exit_code = exit_code
                proc.message = "Execution complete" if success else "Execution failed"
        except Exception as e:
            if execution_id in active_processes:
                proc = active_processes[execution_id]
                proc.completed = True
                proc.success = False
                proc.output = str(e)
                proc.exit_code = -1
                proc.message = f"Error during execution: {str(e)}"

    thread = threading.Thread(target=run_in_container)
    thread.daemon = True
    thread.start()

    response_data = {
        "success": True,
        "message": "Execution started in container",
        "output": "",
        "execution_id": execution_id,
        "session_id": session_id,
        "started": True,
    }

    response = JSONResponse(content=response_data, status_code=200)
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, max_age=86400
    )
    return response


@router.post("/verify", tags=["Code Execution"])
async def verify_code(
    request: Request,
    code: str = Form(None, description="Source code to verify"),
    language: str = Form(None, description="Programming language"),
    timeout: int = Form(30),
    version: str = Form(None),
    session_id: str = Cookie(None),
):
    """
    Verify code using AutoProof (currently only supported for Eiffel).
    """
    # Parse request data
    request_data = await parse_request_data(request)

    if request_data["is_multi_file"]:
        # Multi-file request
        language = request_data["language"]
        files = request_data["files"]
        main_file = request_data["main_file"]
        timeout = request_data.get("timeout", 30)

        # Find the main file content
        main_file_content = None
        for file_info in files:
            if file_info.name == main_file:
                main_file_content = file_info.content
                break

        if main_file_content is None:
            raise HTTPException(
                status_code=400, detail=f"Main file '{main_file}' not found"
            )

        code = main_file_content
    else:
        # Legacy form request
        if not code or not language:
            raise HTTPException(
                status_code=400, detail="Code and language are required"
            )

    session_id = get_or_create_session_id(session_id)
    execution_id = increment_process_counter()
    update_session_activity(session_id)

    # Currently only Eiffel supports verification
    if language != "eiffel":
        raise HTTPException(
            status_code=400,
            detail=f"Verification not supported for language: {language}",
        )

    if CONFIG is None or language not in CONFIG.compilers:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    active_processes[execution_id] = ActiveProcess(
        session_id=session_id,
        start_time=time.time(),
        cancelled=False,
        completed=False,
        timeout=timeout,
        language=language,
        operation_type="verify",
    )

    def verify_in_container():
        try:
            executor = get_executor_by_name(language, version)
            # Check if the executor supports verification
            if not hasattr(executor, "verify"):
                raise Exception(f"Verification not supported for {language}")

            # Use the verify method instead of execute
            success, output, exit_code = executor.verify(code, session_id, timeout)
            if execution_id in active_processes:
                proc = active_processes[execution_id]
                proc.completed = True
                proc.success = success
                proc.output = output
                proc.exit_code = exit_code
                proc.message = (
                    "Verification complete" if success else "Verification failed"
                )
        except Exception as e:
            if execution_id in active_processes:
                proc = active_processes[execution_id]
                proc.completed = True
                proc.success = False
                proc.output = str(e)
                proc.exit_code = -1
                proc.message = f"Error during verification: {str(e)}"

    thread = threading.Thread(target=verify_in_container)
    thread.daemon = True
    thread.start()

    response_data = {
        "success": True,
        "message": "Verification started in container",
        "output": "",
        "execution_id": execution_id,
        "session_id": session_id,
        "started": True,
    }

    response = JSONResponse(content=response_data, status_code=200)
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, max_age=86400
    )
    return response


@router.post("/cancel", tags=["Code Execution"])
async def cancel_execution(execution_id: str = Form(...)):
    """Cancel a running execution."""
    if execution_id not in active_processes:
        return JSONResponse(
            content={"success": False, "message": "Execution not found"},
            status_code=404,
        )
    proc = active_processes[execution_id]
    session_id = proc.session_id
    try:
        container_mgr = get_container_manager()
        cancelled = container_mgr.cancel_execution(session_id)
        proc.cancelled = True
        proc.completed = True
        proc.success = False
        proc.message = "Execution cancelled by user"
        return {"success": cancelled, "message": proc.message}
    except Exception as e:
        return {"success": False, "message": f"Error cancelling execution: {str(e)}"}


@router.get("/status/{execution_id}", tags=["Code Execution"])
async def get_execution_status(execution_id: str):
    """Get the status of a running execution."""
    if execution_id not in active_processes:
        return {"running": False, "message": "Execution not found or completed"}
    
    process_info = active_processes[execution_id]
    elapsed_time = time.time() - process_info.start_time
    
    if process_info.completed:
        final_result = {
            "running": False,
            "completed": True,
            "success": (
                process_info.success if process_info.success is not None else False
            ),
            "message": process_info.message or "Execution completed",
            "output": process_info.output or "",
            "exit_code": process_info.exit_code,
            "elapsed_time": round(elapsed_time, 2),
            "cancelled": process_info.cancelled,
            "operation_type": process_info.operation_type,
        }
        del active_processes[execution_id]
        return final_result
    
    return {
        "running": True,
        "completed": False,
        "elapsed_time": round(elapsed_time, 2),
        "timeout": process_info.timeout,
        "cancelled": process_info.cancelled,
    }
