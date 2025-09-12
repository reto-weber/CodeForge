"""
Library browser controller.
Handles Eiffel library class browsing functionality.
"""

from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import JSONResponse

from language_executor.factory import get_executor_by_name
from src.models import (
    EiffelLibraryNameMapping,
    EiffelLibraryNameMappingBase,
    LibraryInformation,
)
from .shared_utils import get_or_create_session_id, update_session_activity
from eiffel_mapping_manager import get_mapping_manager

router = APIRouter()


@router.get(
    "/eiffel/library/{class_name}",
    tags=["Eiffel Library"],
    response_model=LibraryInformation,
)
async def get_eiffel_library_class(
    class_name: str,
    session_id: str = Cookie(None),
):
    """
    Fetch the source code of an Eiffel library class using apb -short.
    Automatically applies class name mappings for legacy/deprecated names.
    Only available for Eiffel language.
    """
    session_id = get_or_create_session_id(session_id)
    update_session_activity(session_id)

    # Apply class name mapping if one exists
    mapping_manager = get_mapping_manager()
    original_class_name = class_name
    mapped_class_name = mapping_manager.apply_mapping(class_name)

    # Get Eiffel executor
    executor = get_executor_by_name("eiffel", "")

    # Check if the executor has the get_library_class method
    if not hasattr(executor, "get_library_class"):
        raise HTTPException(
            status_code=400,
            detail="Library class browsing not supported for this language",
        )

    # Use the mapped class name for fetching
    success, source_code = executor.get_library_class(mapped_class_name, session_id)

    # Prepare response message
    message = "Library class fetched successfully"
    if original_class_name != mapped_class_name:
        message += f" (mapped from {original_class_name} to {mapped_class_name})"

    response_data = LibraryInformation(
        success=success,
        class_name=original_class_name,  # Return the original name requested
        mapped_class_name=mapped_class_name,  # Include the mapped name
        source_code=source_code if success else "",
        language="eiffel",
        message=message if success else source_code,
    )

    response = JSONResponse(
        content=response_data.model_dump(), status_code=200 if success else 404
    )
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, max_age=86400
    )
    return response


@router.get("/eiffel/mappings", tags=["Eiffel Library"])
async def get_eiffel_mappings():
    """
    Get all available Eiffel class name mappings.
    """
    mapping_manager = get_mapping_manager()
    mappings = mapping_manager.get_all_mappings()

    response_data = EiffelLibraryNameMapping(
        success=True,
        mappings=mappings,
        count=len(mappings),
        message=f"Retrieved {len(mappings)} Eiffel class name mappings",
    )

    return JSONResponse(content=response_data.model_dump(), status_code=200)


@router.post("/eiffel/mappings/reload", tags=["Eiffel Library"])
async def reload_eiffel_mappings():
    """
    Reload Eiffel class name mappings from the XML configuration file.
    """
    try:
        mapping_manager = get_mapping_manager()
        mapping_manager.reload_mappings()
        mappings = mapping_manager.get_all_mappings()

        response_data = EiffelLibraryNameMappingBase(
            success=True,
            count=len(mappings),
            message=f"Successfully reloaded {len(mappings)} Eiffel class name mappings",
        )

        return JSONResponse(content=response_data.model_dump(), status_code=200)

    except Exception as e:
        response_data = EiffelLibraryNameMappingBase(
            success=False,
            count=0,
            message=f"Error reloading mappings: {str(e)}",
        )
        return JSONResponse(content=response_data.model_dump(), status_code=500)
