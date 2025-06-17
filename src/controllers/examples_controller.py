"""
Examples controller.
Handles loading and serving code examples.
"""

import json
import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models import CompilerConfig

router = APIRouter()

# These will be set by main.py through set_globals
CONFIG: Optional[CompilerConfig] = None


def set_globals(config):
    """Set global state variables for this controller."""
    global CONFIG
    CONFIG = config


@router.get("/examples", tags=["Examples"])
async def get_examples():
    """Get the list of available code examples."""
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
    """Get the source code of a specific example file."""
    try:
        print(f"DEBUG: CONFIG is None: {CONFIG is None}")
        if CONFIG is not None:
            print(f"DEBUG: CONFIG.compilers: {CONFIG.compilers}")
            print(
                f"DEBUG: language '{language}' in CONFIG.compilers: {language in CONFIG.compilers}"
            )
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
