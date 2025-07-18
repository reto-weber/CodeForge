"""
Shared utilities for controllers.
"""

import uuid
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
from pydantic import ValidationError

from models import UserSession, MultiFileRequest


# Global state - will be set by main.py
active_processes: Dict[str, any] = {}
user_sessions: Dict[str, UserSession] = {}
CONFIG: Optional[any] = None
PROCESS_COUNTER = 0


def set_globals(processes, sessions, config, counter):
    """Set global state variables."""
    global active_processes, user_sessions, CONFIG, PROCESS_COUNTER
    active_processes = processes
    user_sessions = sessions
    CONFIG = config
    PROCESS_COUNTER = counter


def get_config():
    """Get the current CONFIG object."""
    return CONFIG


def get_active_processes():
    """Get the active_processes dictionary."""
    return active_processes


def get_user_sessions():
    """Get the user_sessions dictionary."""
    return user_sessions


def get_or_create_session_id(session_id: Optional[str] = None) -> str:
    """Get existing session ID or create a new one."""
    if session_id and session_id in user_sessions:
        return session_id
    new_session_id = str(uuid.uuid4())
    user_sessions[new_session_id] = UserSession(
        created_at=time.time(),
        last_used=time.time(),
    )
    return new_session_id


def update_session_activity(session_id: str):
    """Update the last used time for a session."""
    if session_id in user_sessions:
        user_sessions[session_id].last_used = time.time()


def safe_decode(val):
    """Safely decode bytes to string."""
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


def increment_process_counter() -> str:
    """Increment and return the next process counter value."""
    global PROCESS_COUNTER
    PROCESS_COUNTER += 1
    return str(PROCESS_COUNTER)
