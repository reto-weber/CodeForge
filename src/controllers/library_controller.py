"""
Library browser controller.
Handles Eiffel library class browsing functionality.
"""
from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import JSONResponse

from language_executor.factory import get_executor_by_name
from .shared_utils import get_or_create_session_id, update_session_activity

router = APIRouter()


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
