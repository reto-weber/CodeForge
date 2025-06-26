"""
Session management controller.
Handles session info, cleanup, and related operations.
"""

from typing import Dict
from fastapi import APIRouter, Cookie
from fastapi.responses import JSONResponse
import time

from container_manager import get_container_manager
from models import UserSession

router = APIRouter()

# These will be set by main.py through set_globals
user_sessions: Dict[str, UserSession] = {}


def set_globals(sessions, config=None):
    """Set global state variables for this controller."""
    global user_sessions
    user_sessions = sessions


@router.get("/session/info", tags=["Session"])
async def get_session_info(session_id: str = Cookie(None)):
    """Get information about the current session."""
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
    """Clean up a session and its associated container."""
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


@router.post("/session/cleanup-on-language-change", tags=["Session"])
async def cleanup_on_language_change(session_id: str = Cookie(None)):
    """Clean up session when programming language is changed."""
    if not session_id:
        return JSONResponse(
            content={"success": False, "message": "No session ID provided"},
            status_code=400,
        )

    try:
        container_mgr = get_container_manager()
        # Clean up containers but keep the session for continuity
        success = container_mgr.cleanup_session_container(session_id)

        # Update session last used time
        if session_id in user_sessions:
            user_sessions[session_id].last_used = time.time()

        return JSONResponse(
            content={
                "success": success,
                "message": (
                    "Session containers cleaned up for language change"
                    if success
                    else "Failed to clean up session containers"
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


@router.post("/session/cleanup-on-refresh", tags=["Session"])
async def cleanup_on_refresh(session_id: str = Cookie(None)):
    """Clean up session when page is refreshed."""
    if not session_id:
        return JSONResponse(
            content={"success": False, "message": "No session ID provided"},
            status_code=400,
        )

    try:
        container_mgr = get_container_manager()
        # Clean up containers but keep the session for continuity
        success = container_mgr.cleanup_session_container(session_id)

        # Update session last used time
        if session_id in user_sessions:
            user_sessions[session_id].last_used = time.time()

        return JSONResponse(
            content={
                "success": success,
                "message": (
                    "Session containers cleaned up for page refresh"
                    if success
                    else "Failed to clean up session containers"
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
