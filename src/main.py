import json
import os
import time
import threading
import uuid
from typing import Dict, Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Home and favicon endpoints remain in main.py
from fastapi import Cookie, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from controllers.admin_controller import router as admin_router
from controllers.admin_controller import set_globals as set_admin_globals
from controllers.code_controller import router as code_router
from controllers.code_controller import set_globals as set_code_globals
from models import ActiveProcess, UserSession
from container_manager import get_container_manager

# Global variables for process management
active_processes: Dict[str, ActiveProcess] = {}
user_sessions: Dict[str, UserSession] = {}
PROCESS_COUNTER = 0


# Load configuration
def load_config() -> dict:
    config_dir = os.path.join(os.path.dirname(__file__), "config")
    config_path = os.path.join(config_dir, "languages.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        # Fallback to default config
        default_config = {
            "supported_languages": {
                "eiffel": {
                    "name": "Eiffel",
                    "executor_class": "EiffelExecutor",
                    "file_extension": ".e",
                    "description": "Eiffel programming language",
                    "enabled": True,
                },
            },
            "default_language": "eiffel",
            "timeout_limits": {"min": 5, "max": 300, "default": 30},
            "compiler_settings": {
                "max_file_size": "10MB",
                "temp_dir": "/tmp/code_execution",
            },
        }
        os.makedirs(config_dir, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return default_config


CONFIG = load_config()

app = FastAPI(
    title="CodeForge",
    description="""
    A comprehensive code compilation, execution and verification platform supporting multiple
    programming languages.

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

# Pass global state to controllers
set_code_globals(active_processes, user_sessions, CONFIG, PROCESS_COUNTER)
set_admin_globals(user_sessions, CONFIG)

# Include routers
app.include_router(code_router)
app.include_router(admin_router)


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request, session_id: Optional[str] = Cookie(None)):
    session_id = str(session_id) if session_id else None
    if session_id not in user_sessions:
        new_session_id = str(uuid.uuid4())
        user_sessions[new_session_id] = UserSession(
            created_at=time.time(),
            last_used=time.time(),
        )
        session_id = new_session_id
    else:
        user_sessions[session_id].last_used = time.time()
    languages = list(CONFIG["supported_languages"])
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "languages": CONFIG["supported_languages"],
            "default_language": CONFIG["default_language"],
        },
    )
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, max_age=86400
    )
    return response


@app.get("/favicon.ico")
async def get_favicon():
    favicon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.svg")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/svg+xml")
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")


def background_cleanup():
    container_mgr = get_container_manager()
    while True:
        try:
            container_mgr.cleanup_old_containers(max_age_hours=1)
        except Exception as e:
            print(f"[Cleanup] Error: {e}")
        time.sleep(600)  # Run every 10 minutes


# Start background cleanup thread
cleanup_thread = threading.Thread(target=background_cleanup, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
