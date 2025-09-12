"""
Session management controller.
Handles session info, cleanup, and related operations.
"""

from typing import Dict
from fastapi import APIRouter, Cookie
from fastapi.responses import JSONResponse

from container_manager import get_container_manager
from models import Message, SessionInformation, UserSession, SuccessMessage

router = APIRouter()

# These will be set by main.py through set_globals
user_sessions: Dict[str, UserSession] = {}


def set_globals(sessions):
    """Set global state variables for this controller."""
    global user_sessions
    user_sessions = sessions


@router.get(
    "/session/info",
    tags=["Session"],
    response_model=SessionInformation,
    responses={404: {"model": Message}},
)
async def get_session_info(session_id: str = Cookie(None)):
    """Get information about the current session."""
    if not session_id or session_id not in user_sessions:
        return JSONResponse(
            content=Message(
                message=f"No active session with id: {session_id}"
            ).model_dump(),
            status_code=404,
        )
    try:
        container_mgr = get_container_manager()
        container_info = container_mgr.get_session_info(session_id)
        session_info = user_sessions[session_id]
        return SessionInformation(
            session_id=session_id,
            session_created=session_info.created_at,
            session_last_used=session_info.last_used,
            container=container_info,
        )
    except Exception as e:
        return {"error": f"Failed to get session info: {str(e)}"}


@router.post(
    "/session/cleanup",
    tags=["Session"],
    response_model=SuccessMessage,
    responses={400: {"model": SuccessMessage}, 500: {"model": SuccessMessage}},
)
async def cleanup_session(session_id: str = Cookie(None)):
    """Clean up a session and its associated container."""
    if not session_id:
        return JSONResponse(
            content=SuccessMessage(
                success=False, message="No session ID provided"
            ).model_dump(),
            status_code=400,
        )
    try:
        container_mgr = get_container_manager()
        success = container_mgr.cleanup_session_container(session_id)
        if session_id in user_sessions:
            del user_sessions[session_id]
        return JSONResponse(
            content=SuccessMessage(
                success=success,
                message=(
                    "Session cleaned up successfully"
                    if success
                    else "Failed to clean up session"
                ),
            ).model_dump(),
            status_code=200 if success else 500,
        )
    except Exception as e:
        return JSONResponse(
            content=SuccessMessage(
                success=False,
                message=f"Error cleaning up session: {str(e)}",
            ).model_dump(),
            status_code=500,
        )
