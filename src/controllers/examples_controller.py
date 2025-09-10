"""
Examples controller.
Handles loading and serving code examples.
"""

import json
import os
import csv
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

# These will be set by main.py through set_globals
CONFIG: Optional[dict] = None


def set_globals(config):
    """Set global state variables for this controller."""
    global CONFIG
    CONFIG = config


def get_example_data():
    # Try relative to project root
    examples_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")
    if not os.path.exists(examples_path):
        # Try absolute path from workspace root
        abs_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../examples/")
        )
        print(f"Trying fallback abs_path: {abs_path}")
        examples_path = abs_path
    if not os.path.exists(examples_path):
        return JSONResponse(
            content={"error": f"Examples index not found at {examples_path}"},
            status_code=404,
        )

    examples = []
    for file_name in os.listdir(examples_path):
        file_path = os.path.join(examples_path, file_name)
        if os.path.isfile(file_path) and file_name.endswith(".csv"):
            examples.append(file_name)

    result = dict()
    for example in examples:
        with open(os.path.join(examples_path, example), "r", encoding="utf-8") as f:
            language_name = example.removesuffix("_examples.csv")
            reader = csv.reader(f)
            data = [x for x in reader][1:]
            result[language_name] = {row[0]: row[1] for row in data}
    return result


@router.get("/examples", tags=["Examples"])
async def get_examples():
    """Get the list of available code examples."""
    result = get_example_data()
    if isinstance(result, JSONResponse):
        return result
    return JSONResponse(content=result, status_code=200)


@router.get("/examples/{language}/{name}", tags=["Examples"])
async def get_example_code(language: str, name: str):
    """Get the source code of a specific example file."""
    try:
        examples = get_example_data()
        if isinstance(examples, JSONResponse):
            return examples
        return JSONResponse(
            content={
                "url": examples[language][name],
                "language": language,
                "filename": name,
            },
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
