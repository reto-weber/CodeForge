"""
Main code controller - combines all sub-controllers.
This is a refactored version that delegates to specialized controllers.
"""
from fastapi import APIRouter

from . import execution_controller
from . import session_controller
from . import examples_controller
from .library_controller import router as library_router
from .shared_utils import set_globals as set_shared_globals

# Main router that includes all sub-routers
router = APIRouter()

# Include all sub-routers
router.include_router(execution_controller.router)
router.include_router(session_controller.router)
router.include_router(examples_controller.router)
router.include_router(library_router)


def set_globals(processes, sessions, config, counter):
    """Set global state for all controllers."""
    # Set globals for shared utils
    set_shared_globals(processes, sessions, config, counter)
    # Set globals for execution controller
    execution_controller.set_globals(processes, config)
    # Set globals for session controller
    session_controller.set_globals(sessions)
    # Set globals for examples controller
    examples_controller.set_globals(config)


# Expose the set_globals function for main.py to use
__all__ = ["router", "set_globals"]
