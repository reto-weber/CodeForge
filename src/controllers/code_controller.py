import json
import threading
import os
import time
import uuid
from typing import Dict, Optional

from fastapi import APIRouter, Cookie, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from container_manager import get_container_manager
from language_executor.factory import get_executor_by_name
from models import ActiveProcess, CompilerConfig, UserSession, MultiFileRequest

router = APIRouter()

# These will be set by main.py
active_processes: Dict[str, ActiveProcess] = {}
user_sessions: Dict[str, UserSession] = {}
CONFIG: Optional[CompilerConfig] = None
PROCESS_COUNTER = 0


def set_globals(processes, sessions, config, counter):
    global active_processes, user_sessions, CONFIG, PROCESS_COUNTER
    active_processes = processes
    user_sessions = sessions
    CONFIG = config
    PROCESS_COUNTER = counter


def get_or_create_session_id(session_id: Optional[str] = None) -> str:
    if session_id and session_id in user_sessions:
        return session_id
    new_session_id = str(uuid.uuid4())
    user_sessions[new_session_id] = UserSession(
        created_at=time.time(),
        last_used=time.time(),
    )
    return new_session_id


def update_session_activity(session_id: str):
    if session_id in user_sessions:
        user_sessions[session_id].last_used = time.time()


def _safe_decode(val):
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    return val or ""


async def parse_request_data(request: Request) -> dict:
    """Parse request data from either JSON (multi-file) or Form (legacy) format."""
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # New multi-file format
        try:
            json_data = await request.json()
            multi_file_request = MultiFileRequest(**json_data)
            return {
                "is_multi_file": True,
                "language": multi_file_request.language,
                "files": multi_file_request.files,
                "main_file": multi_file_request.main_file,
                "timeout": getattr(multi_file_request, "timeout", 30),
                "file_path": getattr(multi_file_request, "file_path", None),
                "output_path": getattr(multi_file_request, "output_path", None),
            }
        except (ValidationError, ValueError) as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid JSON request: {str(e)}"
            )
    else:
        # Legacy form format - handled by FastAPI form parsing
        return {"is_multi_file": False}


@router.post("/compile", tags=["Code Execution"])
async def compile_code(
    request: Request,
    code: str = Form(None, description="Source code to compile"),
    language: str = Form(None, description="Programming language"),
    version: Optional[str] = Form(None),
    session_id: Optional[str] = Cookie(None),
):
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
    global PROCESS_COUNTER

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
    PROCESS_COUNTER += 1
    execution_id = str(PROCESS_COUNTER)
    update_session_activity(session_id)
    if CONFIG is None or language not in CONFIG.compilers:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
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
    global PROCESS_COUNTER

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
    PROCESS_COUNTER += 1
    execution_id = str(PROCESS_COUNTER)
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


@router.get("/session/info", tags=["Session"])
async def get_session_info(session_id: str = Cookie(None)):
    if not session_id or session_id not in user_sessions:
        return {"error": "No active session"}
    try:
        container_mgr = get_container_manager()
        container_info = container_mgr.get_session_info(session_id)
        session_info = user_sessions[session_id]
        return {
            "session_id": session_id,
            "session_created": session_info.created_at,
            "session_last_used": session_info.last_used,
            "container": container_info,
        }
    except Exception as e:
        return {"error": f"Failed to get session info: {str(e)}"}


@router.post("/session/cleanup", tags=["Session"])
async def cleanup_session(session_id: str = Cookie(None)):
    if not session_id:
        return JSONResponse(
            content={"success": False, "message": "No session ID provided"},
            status_code=400,
        )
    try:
        container_mgr = get_container_manager()
        success = container_mgr.cleanup_session_container(session_id)
        if session_id in user_sessions:
            del user_sessions[session_id]
        return JSONResponse(
            content={
                "success": success,
                "message": (
                    "Session cleaned up successfully"
                    if success
                    else "Failed to clean up session"
                ),
            },
            status_code=200 if success else 500,
        )
    except Exception as e:
        return JSONResponse(
            content={
                "success": False,
                "message": f"Error cleaning up session: {str(e)}",
            },
            status_code=500,
        )


@router.get("/examples", tags=["Examples"])
async def get_examples():
    try:
        # Try relative to project root
        examples_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "examples",
            "examples_index.json",
        )
        print(f"Trying examples_path: {examples_path}")
        if not os.path.exists(examples_path):
            # Try absolute path from workspace root
            abs_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "../../examples/examples_index.json"
                )
            )
            print(f"Trying fallback abs_path: {abs_path}")
            examples_path = abs_path
        if not os.path.exists(examples_path):
            return JSONResponse(
                content={"error": f"Examples index not found at {examples_path}"},
                status_code=404,
            )

        with open(examples_path, "r", encoding="utf-8") as f:
            examples = json.load(f)
        return JSONResponse(content=examples, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to load examples: {str(e)}"}, status_code=500
        )


@router.get("/examples/{language}/{filename}", tags=["Examples"])
async def get_example_code(language: str, filename: str):
    try:
        if CONFIG is None or language not in CONFIG.compilers:
            raise HTTPException(
                status_code=400, detail=f"Unsupported language: {language}"
            )
        examples_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "examples"
        )
        file_path = os.path.join(examples_dir, language, filename)
        print(f"Trying file_path: {file_path}")
        if not os.path.exists(file_path):
            abs_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), f"../../examples/{language}/{filename}"
                )
            )
            print(f"Trying fallback abs_path: {abs_path}")
            file_path = abs_path
        if not os.path.exists(file_path):
            return JSONResponse(
                content={"error": f"Example file not found at {file_path}"},
                status_code=404,
            )
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return JSONResponse(
            content={"code": code, "filename": filename, "language": language},
            status_code=200,
        )
    except FileNotFoundError:
        return JSONResponse(
            content={"error": "Example file not found (FileNotFoundError)"},
            status_code=404,
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to load example: {str(e)}"}, status_code=500
        )


@router.get("/eiffel/library/{class_name}", tags=["Eiffel Library"])
async def get_eiffel_library_class(
    class_name: str,
    session_id: str = Cookie(None),
):
    """
    Fetch the source code of an Eiffel library class using apb -short.
    Only available for Eiffel language.
    """
    try:
        session_id = get_or_create_session_id(session_id)
        update_session_activity(session_id)

        # Get Eiffel executor
        from language_executor.factory import get_executor_by_name

        executor = get_executor_by_name("eiffel", "")

        # Check if the executor has the get_library_class method
        if not hasattr(executor, "get_library_class"):
            raise HTTPException(
                status_code=400,
                detail="Library class browsing not supported for this language",
            )

        success, source_code = executor.get_library_class(class_name, session_id)

        response_data = {
            "success": success,
            "class_name": class_name,
            "source_code": source_code if success else "",
            "language": "eiffel",
            "message": "Library class fetched successfully" if success else source_code,
        }

        response = JSONResponse(
            content=response_data, status_code=200 if success else 500
        )
        response.set_cookie(
            key="session_id", value=session_id, httponly=True, max_age=86400
        )
        return response

    except Exception as e:
        response_data = {
            "success": False,
            "class_name": class_name,
            "source_code": "",
            "language": "eiffel",
            "message": f"Error fetching library class: {str(e)}",
        }

        response = JSONResponse(content=response_data, status_code=500)
        if session_id:
            response.set_cookie(
                key="session_id", value=session_id, httponly=True, max_age=86400
            )
        return response
