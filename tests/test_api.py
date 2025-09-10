"""
API test suite for FastAPI code compiler and runner.
Covers all endpoints and tests compile-then-run workflow.
"""

import sys
import os
import time
import json
from fastapi.testclient import TestClient

from src.controllers.shared_utils import decompress_token

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app
from controllers.shared_utils import decompress_token

client = TestClient(app)


def wait_for_execution_completion(execution_id, expected_output=None, max_attempts=10):
    """
    Helper function to wait for execution completion and verify output.

    Args:
        execution_id: The execution ID to monitor
        expected_output: String that should be present in the output (optional)
        max_attempts: Maximum number of polling attempts

    Returns:
        status_data: The final status data when execution completes

    Raises:
        AssertionError: If execution doesn't complete or output doesn't match
    """
    for attempt in range(max_attempts):
        status_resp = client.get(f"/status/{execution_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        print(f"Status response (attempt {attempt + 1}): {status_data}")

        if status_data.get("completed", False):
            if expected_output and status_data.get("success", False):
                assert expected_output in status_data["output"]
            return status_data
        time.sleep(1)

    # If we get here, execution didn't complete in time
    assert False, f"Execution didn't complete after {max_attempts} attempts"


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "<html" in resp.text


def test_favicon():
    resp = client.get("/favicon.ico")
    assert resp.status_code in (200, 404)  # favicon may be missing


def test_status():
    resp = client.get("/status/testsession1")
    assert resp.status_code == 200


def test_session_info():
    # First create a session by running some code to ensure session exists
    code = "print('test')"
    session_id = "testsession_info"

    # Create session by running code
    run_resp = client.post(
        "/run",
        data={"language": "python", "code": code},
        cookies={"session_id": session_id},
    )
    assert run_resp.status_code == 200

    # Now check session info
    resp = client.get("/session/info", cookies={"session_id": session_id})
    assert resp.status_code == 200
    data = resp.json()
    assert "container" in data or "session_id" in data  # Check for session info


def test_session_cleanup():
    resp = client.post("/session/cleanup", cookies={"session_id": "testsession1"})
    assert resp.status_code == 200


def test_examples_list():
    resp = client.get("/examples")
    assert resp.status_code == 200
    data = resp.json()
    # Response contains language categories like 'python', 'java', etc.
    assert any(lang in data for lang in ["python", "java", "c", "cpp"])


def test_examples_file():
    resp = client.get("/examples/python/Hello%20World")
    assert resp.status_code == 200
    data = resp.json()
    data = json.loads(decompress_token(data["url"][4:]))
    assert len(data["files"]) == 1
    data = data["files"][0]
    assert "print" in data["content"]


def test_admin_get_config():
    resp = client.get("/admin/config", headers={"X-API-Key": "supersecretapikey"})
    assert resp.status_code == 200


def test_admin_update_config():
    resp = client.post(
        "/admin/config",
        json={"dummy": True},
        headers={"X-API-Key": "supersecretapikey"},
    )
    assert resp.status_code in (200, 400, 422)  # 400/422 if validation fails


def test_admin_get_stats():
    resp = client.get("/admin/containers", headers={"X-API-Key": "supersecretapikey"})
    assert resp.status_code == 200


def test_admin_restart():
    resp = client.post(
        "/admin/cleanup",
        data={"max_age_hours": "1"},  # String instead of int
        headers={"X-API-Key": "supersecretapikey"},
    )
    assert resp.status_code in (200, 503)  # 503 if not implemented
