import os
import json
import subprocess
import tempfile
import threading
import time
import signal
import uuid
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, Form, HTTPException, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

try:
    from .container_manager import get_container_manager
except ImportError:
    # For direct execution
    from container_manager import get_container_manager


# Pydantic models for API documentation
class CompileRequest(BaseModel):
    """Request model for code compilation."""

    code: str = Field(..., description="Source code to compile")
    language: str = Field(..., description="Programming language")


class CompileResponse(BaseModel):
    """Response model for code compilation."""

    success: bool = Field(..., description="Whether compilation succeeded")
    message: str = Field(..., description="Compilation status message")
    output: str = Field(..., description="Compiler output")
    file_path: Optional[str] = Field(None, description="Path to source file")
    output_path: Optional[str] = Field(None, description="Path to compiled output")


class RunRequest(BaseModel):
    """Request model for code execution."""

    code: str = Field(..., description="Source code to execute")
    language: str = Field(..., description="Programming language")
    timeout: int = Field(30, description="Execution timeout in seconds")
    file_path: Optional[str] = Field(None, description="Pre-compiled file path")
    output_path: Optional[str] = Field(None, description="Pre-compiled output path")


class RunResponse(BaseModel):
    """Response model for code execution."""

    success: bool = Field(..., description="Whether execution started successfully")
    message: str = Field(..., description="Execution status message")
    started: bool = Field(..., description="Whether execution process started")
    execution_id: Optional[str] = Field(None, description="Unique execution ID")
    output: Optional[str] = Field(None, description="Execution output (if immediate)")


class StatusResponse(BaseModel):
    """Response model for execution status."""

    running: bool = Field(..., description="Whether execution is still running")
    completed: bool = Field(..., description="Whether execution completed")
    success: bool = Field(..., description="Whether execution was successful")
    message: str = Field(..., description="Status message")
    output: Optional[str] = Field(None, description="Execution output")
    exit_code: Optional[int] = Field(None, description="Process exit code")
    elapsed_time: float = Field(..., description="Elapsed time in seconds")


class SessionInfo(BaseModel):
    """Response model for session information."""

    session_id: str = Field(..., description="Unique session identifier")
    session_created: float = Field(..., description="Session creation timestamp")
    session_last_used: float = Field(..., description="Last activity timestamp")
    container: Optional[Dict[str, Any]] = Field(None, description="Container info")


class ExampleInfo(BaseModel):
    """Model for code example information."""

    title: str = Field(..., description="Example title")
    description: str = Field(..., description="Example description")
    code: str = Field(..., description="Example source code")


# Global variables for process management
active_processes = {}
user_sessions = {}  # Track user sessions
process_counter = 0

app = FastAPI(
    title="Code Compiler and Runner API",
    description="""
    A comprehensive code compilation and execution platform supporting multiple programming languages.
    
    ## Features
    
    * **Multi-language Support**: Compile and run Python, C, C++, and Java code
    * **Docker Integration**: Secure code execution in isolated containers
    * **Session Management**: Track user sessions and container states
    * **Real-time Execution**: Monitor code execution with real-time status updates
    * **Configuration Management**: Customizable compiler and runtime settings
    * **Example Library**: Pre-built code examples for each supported language
    
    ## API Endpoints
    
    The API provides endpoints for:
    - Code compilation and execution
    - Session and container management
    - Configuration management
    - Example code loading
    - Administrative functions
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "Code Compiler API Support",
        "url": "https://github.com/your-repo/code-compiler",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


# Load configuration
def load_config():
    try:
        config_path = os.path.join(
            os.path.dirname(__file__), "config", "compiler_config.json"
        )
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default config if file doesn't exist
        default_config = {
            "compilers": {
                "python": {
                    "compile_cmd": "",  # Python doesn't need compilation
                    "run_cmd": "python {file}",
                },
                "c": {"compile_cmd": "gcc {file} -o {output}", "run_cmd": "{output}"},
                "cpp": {"compile_cmd": "g++ {file} -o {output}", "run_cmd": "{output}"},
                "java": {"compile_cmd": "javac {file}", "run_cmd": "java {classname}"},
            },
            "default_language": "python",
        }
        # Create config directory and file with default settings
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "compiler_config.json")
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config


# Global variable to store config
CONFIG = load_config()


def get_or_create_session_id(session_id: str = None) -> str:
    """Get existing session ID or create a new one."""
    if session_id and session_id in user_sessions:
        return session_id

    new_session_id = str(uuid.uuid4())
    user_sessions[new_session_id] = {
        "created_at": time.time(),
        "last_used": time.time(),
    }
    return new_session_id


def update_session_activity(session_id: str):
    """Update the last activity time for a session."""
    if session_id in user_sessions:
        user_sessions[session_id]["last_used"] = time.time()


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request, session_id: str = Cookie(None)):
    """Render the home page with the code editor."""
    # Get or create session
    session_id = get_or_create_session_id(session_id)
    update_session_activity(session_id)

    languages = list(CONFIG["compilers"].keys())
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "languages": languages,
            "default_language": CONFIG["default_language"],
        },
    )

    # Set session cookie
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, max_age=86400
    )  # 24 hours
    return response


@app.get("/favicon.ico")
async def get_favicon():
    """Serve favicon for browsers that request it from root."""
    favicon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.svg")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/svg+xml")
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")


@app.post("/compile", response_model=CompileResponse, tags=["Code Execution"])
async def compile_code(
    code: str = Form(..., description="Source code to compile"),
    language: str = Form(
        ..., description="Programming language (python, c, cpp, java)"
    ),
):
    """
    Compile source code for the specified programming language.

    This endpoint compiles code for languages that require compilation (C, C++, Java).
    For interpreted languages like Python, it simply validates the request.

    - **code**: The source code to compile
    - **language**: The programming language (python, c, cpp, java)

    Returns compilation results including success status, messages, and file paths.
    """
    if language not in CONFIG["compilers"]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    compiler_config = CONFIG["compilers"][language]
    compile_cmd = compiler_config.get("compile_cmd")

    # If no compilation needed (like Python)
    if not compile_cmd:
        return CompileResponse(
            success=True,
            message="No compilation needed for this language",
            output="",
            file_path=None,
            output_path=None,
        )

    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(
        suffix=f".{language}", delete=False, mode="w"
    ) as temp_file:
        temp_file.write(code)
        temp_file_path = temp_file.name

    output_path = temp_file_path + ".out"

    # Format the compile command
    formatted_cmd = compile_cmd.format(file=temp_file_path, output=output_path)

    try:
        # Run the compilation
        process = subprocess.run(
            formatted_cmd, shell=True, capture_output=True, text=True
        )

        if process.returncode != 0:
            return CompileResponse(
                success=False,
                message="Compilation failed",
                output=process.stderr or process.stdout,
                file_path=temp_file_path,
                output_path=None,
            )

        return CompileResponse(
            success=True,
            message="Compilation successful",
            output=process.stdout,
            file_path=temp_file_path,
            output_path=output_path,
        )
    except Exception as e:
        return CompileResponse(
            success=False,
            message=f"Error during compilation: {str(e)}",
            output="",
            file_path=temp_file_path,
            output_path=None,
        )
        pass


@app.post("/run")
async def run_code(
    code: str = Form(...),
    language: str = Form(...),
    timeout: int = Form(30),
    session_id: str = Cookie(None),
):
    """Start running code in a Docker container."""
    global process_counter
    process_counter += 1
    execution_id = str(process_counter)

    # Get or create session
    session_id = get_or_create_session_id(session_id)
    update_session_activity(session_id)

    if language not in CONFIG["compilers"]:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

    # Get container manager
    try:
        container_mgr = get_container_manager()
    except RuntimeError as e:
        return {
            "success": False,
            "message": f"Docker not available: {str(e)}",
            "output": "",
            "execution_id": execution_id,
        }

    # Start the execution in background
    def run_in_container():
        try:
            print(
                f"Starting execution {execution_id} for session {session_id} in Docker container"
            )

            # Execute code in container
            success, output, exit_code = container_mgr.execute_code(
                session_id=session_id, code=code, language=language, timeout=timeout
            )

            print(
                f"Container execution completed: success={success}, exit_code={exit_code}"
            )

            # Update the process info with results
            if execution_id in active_processes:
                active_processes[execution_id].update(
                    {
                        "completed": True,
                        "success": success,
                        "output": output,
                        "exit_code": exit_code,
                        "message": (
                            "Execution complete" if success else "Execution failed"
                        ),
                    }
                )

        except Exception as e:
            print(f"Error during container execution: {str(e)}")
            # Update the process info with error
            if execution_id in active_processes:
                active_processes[execution_id].update(
                    {
                        "completed": True,
                        "success": False,
                        "output": str(e),
                        "exit_code": -1,
                        "message": f"Error during execution: {str(e)}",
                    }
                )

    # Initialize the process info
    active_processes[execution_id] = {
        "session_id": session_id,
        "start_time": time.time(),
        "cancelled": False,
        "completed": False,
        "timeout": timeout,
        "language": language,
    }

    # Start the execution in a background thread
    thread = threading.Thread(target=run_in_container)
    thread.daemon = True
    thread.start()

    # Return immediately with execution ID
    return {
        "success": True,
        "message": "Execution started in container",
        "output": "",
        "execution_id": execution_id,
        "session_id": session_id,
        "started": True,
    }


@app.post("/cancel")
async def cancel_execution(
    execution_id: str = Form(...), session_id: str = Cookie(None)
):
    """Cancel a running execution in Docker container."""
    print(f"Attempting to cancel execution with ID: {execution_id}")
    print(f"Active processes: {list(active_processes.keys())}")

    if execution_id not in active_processes:
        return {"success": False, "message": "Execution not found or already completed"}

    process_info = active_processes[execution_id]
    execution_session_id = process_info.get("session_id")

    # Verify session ownership
    if session_id and session_id != execution_session_id:
        return {"success": False, "message": "Not authorized to cancel this execution"}

    try:
        # Mark as cancelled
        process_info["cancelled"] = True

        # Update status to cancelled
        process_info.update(
            {
                "completed": True,
                "success": False,
                "output": "Execution was cancelled by user",
                "exit_code": -2,
                "message": "Execution cancelled",
            }
        )

        # Cancel execution in container
        if execution_session_id:
            try:
                container_mgr = get_container_manager()
                cancel_success = container_mgr.cancel_execution(execution_session_id)
                print(f"Container cancellation result: {cancel_success}")
            except Exception as e:
                print(f"Error cancelling in container: {e}")

        return {
            "success": True,
            "message": "Execution cancelled successfully",
            "execution_id": execution_id,
            "cancelled": True,
        }
    except Exception as e:
        print(f"Error cancelling execution: {str(e)}")
        return {"success": False, "message": f"Error cancelling execution: {str(e)}"}


@app.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get the status of a running execution."""
    if execution_id not in active_processes:
        return {"running": False, "message": "Execution not found or completed"}

    process_info = active_processes[execution_id]
    elapsed_time = time.time() - process_info["start_time"]

    # Check if execution completed
    if process_info.get("completed", False):
        # Remove from active processes and return final results
        final_result = {
            "running": False,
            "completed": True,
            "success": process_info.get("success", False),
            "message": process_info.get("message", "Execution completed"),
            "output": process_info.get("output", ""),
            "exit_code": process_info.get("exit_code"),
            "elapsed_time": round(elapsed_time, 2),
            "cancelled": process_info.get("cancelled", False),
        }

        # Clean up
        del active_processes[execution_id]
        return final_result

    return {
        "running": True,
        "completed": False,
        "elapsed_time": round(elapsed_time, 2),
        "timeout": process_info.get("timeout", 30),
        "cancelled": process_info.get("cancelled", False),
    }


@app.get("/session/info")
async def get_session_info(session_id: str = Cookie(None)):
    """Get information about the current session and its container."""
    if not session_id or session_id not in user_sessions:
        return {"error": "No active session"}

    try:
        container_mgr = get_container_manager()
        container_info = container_mgr.get_session_info(session_id)

        session_info = user_sessions[session_id]

        return {
            "session_id": session_id,
            "session_created": session_info["created_at"],
            "session_last_used": session_info["last_used"],
            "container": container_info,
        }
    except Exception as e:
        return {"error": f"Failed to get session info: {str(e)}"}


@app.post("/session/cleanup")
async def cleanup_session(session_id: str = Cookie(None)):
    """Clean up the current session's container."""
    if not session_id:
        return {"success": False, "message": "No session ID provided"}

    try:
        container_mgr = get_container_manager()
        success = container_mgr.cleanup_session_container(session_id)

        if session_id in user_sessions:
            del user_sessions[session_id]

        return {
            "success": success,
            "message": (
                "Session cleaned up successfully"
                if success
                else "Failed to clean up session"
            ),
        }
    except Exception as e:
        return {"success": False, "message": f"Error cleaning up session: {str(e)}"}


@app.get("/admin/containers")
async def list_containers():
    """List all active containers (admin endpoint)."""
    try:
        container_mgr = get_container_manager()
        containers = []

        for session_id in user_sessions:
            container_info = container_mgr.get_session_info(session_id)
            if container_info:
                containers.append(container_info)

        return {"containers": containers, "total": len(containers)}
    except Exception as e:
        return {"error": f"Failed to list containers: {str(e)}"}


@app.post("/admin/cleanup")
async def cleanup_old_containers(max_age_hours: int = Form(24)):
    """Clean up containers older than specified hours (admin endpoint)."""
    try:
        container_mgr = get_container_manager()
        cleaned_count = container_mgr.cleanup_old_containers(max_age_hours)

        # Also clean up old sessions
        current_time = time.time()
        old_sessions = []
        for session_id, session_info in user_sessions.items():
            age_hours = (current_time - session_info["last_used"]) / 3600
            if age_hours > max_age_hours:
                old_sessions.append(session_id)

        for session_id in old_sessions:
            del user_sessions[session_id]

        return {
            "success": True,
            "cleaned_containers": cleaned_count,
            "cleaned_sessions": len(old_sessions),
            "message": f"Cleaned up {cleaned_count} containers and {len(old_sessions)} sessions",
        }
    except Exception as e:
        return {"success": False, "message": f"Error during cleanup: {str(e)}"}


@app.get("/config")
async def get_config():
    """Return the current compiler configuration."""
    return CONFIG


@app.post("/config")
async def update_config(config: Dict[str, Any]):
    """Update the compiler configuration."""
    global CONFIG

    # Validate config structure
    if "compilers" not in config or not isinstance(config["compilers"], dict):
        raise HTTPException(
            status_code=400, detail="Invalid config: missing 'compilers' object"
        )

    if (
        "default_language" not in config
        or config["default_language"] not in config["compilers"]
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid config: missing or invalid 'default_language'",
        )

    # Update config
    CONFIG = config

    # Save to file
    config_path = os.path.join(
        os.path.dirname(__file__), "config", "compiler_config.json"
    )
    with open(config_path, "w") as f:
        json.dump(CONFIG, f, indent=4)

    return {"success": True, "message": "Configuration updated successfully"}


@app.get("/examples")
async def get_examples():
    """Return the list of available examples."""
    try:
        examples_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "examples",
            "examples_index.json",
        )
        with open(examples_path, "r") as f:
            examples = json.load(f)
        return examples
    except FileNotFoundError:
        return {"error": "Examples index not found"}
    except Exception as e:
        return {"error": f"Failed to load examples: {str(e)}"}


@app.get("/examples/{language}/{filename}")
async def get_example_code(language: str, filename: str):
    """Return the code for a specific example."""
    try:
        # Validate language
        if language not in CONFIG["compilers"]:
            raise HTTPException(
                status_code=400, detail=f"Unsupported language: {language}"
            )

        # Construct file path
        examples_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "examples"
        )
        file_path = os.path.join(examples_dir, language, filename)

        # Security check: ensure file is in examples directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(examples_dir)):
            raise HTTPException(status_code=400, detail="Invalid file path")

        # Read the file
        with open(file_path, "r") as f:
            code = f.read()

        return {"code": code, "filename": filename, "language": language}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Example file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load example: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
