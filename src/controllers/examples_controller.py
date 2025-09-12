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
from models import CodeExamples, Message, ProgrammingLanguages, SingleExample

router = APIRouter()

# These will be set by main.py through set_globals
CONFIG: Optional[dict] = None


def set_globals(config):
    """Set global state variables for this controller."""
    global CONFIG
    CONFIG = config


def get_example_data() -> CodeExamples:
    # Try relative to project root
    examples_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")
    if not os.path.exists(examples_path):
        # Try absolute path from workspace root
        abs_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../examples/")
        )
        print(f"Trying fallback abs_path: {abs_path}")
        examples_path = abs_path

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
    return CodeExamples(**result)


@router.get("/examples", tags=["Examples"], response_model=CodeExamples)
async def get_examples():
    """Get the list of available code examples."""
    result = get_example_data()
    return result


@router.get("/examples/{language}", tags=["Examples"])
async def get_examples_by_language(language: ProgrammingLanguages) -> list[str]:
    """Get the list of available code examples for a specific language."""
    result = getattr(get_example_data(), language.value).keys()
    return result


@router.get(
    "/examples/{language}/{name}",
    tags=["Examples"],
    response_model=SingleExample,
    responses={404: {"model": Message}},
)
async def get_example_code(language: ProgrammingLanguages, name: str):
    """Get the source code of a specific example file."""
    examples = getattr(get_example_data(), language.value)
    if name not in examples:
        return JSONResponse(
            status_code=404,
            content=Message(
                message=f"Example '{name}' not found. Available examples are: {list(examples.keys())}"
            ),
        )

    return SingleExample(
        url=examples[name],
        language=language.value,
        filename=name,
    )
