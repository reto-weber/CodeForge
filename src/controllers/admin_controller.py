import os
import time
from fastapi import APIRouter, Form, HTTPException, Depends, status
from fastapi.security.api_key import APIKeyHeader
from container_manager import get_container_manager
from models import UserSession, CompilerConfig
from typing import Dict, Optional

router = APIRouter()

API_KEY = "supersecretapikey"  # TODO: Move to config/env in production
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )


user_sessions: Dict[str, UserSession] = {}
CONFIG: Optional[CompilerConfig] = None


def set_globals(sessions, config):
    global user_sessions, CONFIG
    user_sessions = sessions
    CONFIG = config


@router.get(
    "/admin/containers",
    tags=["Admin"],
    dependencies=[Depends(require_api_key)],
)
async def list_containers():
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


@router.post(
    "/admin/cleanup",
    tags=["Admin"],
    dependencies=[Depends(require_api_key)],
)
async def cleanup_old_containers(max_age_hours: int = Form(24)):
    try:
        container_mgr = get_container_manager()
        cleaned_count = container_mgr.cleanup_old_containers(max_age_hours)
        current_time = time.time()
        old_sessions = []
        for session_id, session_info in user_sessions.items():
            age_hours = (current_time - session_info.last_used) / 3600
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


@router.get(
    "/admin/config",
    tags=["Admin"],
    dependencies=[Depends(require_api_key)],
)
async def get_config():
    return CONFIG


@router.post(
    "/admin/config",
    tags=["Admin"],
    dependencies=[Depends(require_api_key)],
)
async def update_config(config: dict):
    global CONFIG
    try:
        new_config = CompilerConfig(**config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid config: {str(e)}")
    CONFIG = new_config
    config_path = os.path.join(
        os.path.dirname(__file__), "../config", "compiler_config.json"
    )
    with open(config_path, "w") as f:
        import json

        json.dump(CONFIG.dict(), f, indent=4)
    return {"success": True, "message": "Configuration updated successfully"}
