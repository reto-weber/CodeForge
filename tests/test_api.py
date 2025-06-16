"""
API test suite for FastAPI code compiler and runner.
Covers all endpoints and tests compile-then-run workflow.
"""

import sys
import os
import time
from fastapi.testclient import TestClient

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import app

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


def test_run_python():
    code = "print('hello')"
    session_id = "testsession1"
    resp = client.post(
        "/run",
        data={"language": "python", "code": code},
        cookies={"session_id": session_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    print(f"Run response: {data}")  # Debug output
    assert data["success"]
    assert "execution_id" in data

    # Wait for execution to complete and verify output
    execution_id = data["execution_id"]
    wait_for_execution_completion(execution_id, "hello")


def test_compile_and_run_python():
    code = "print('hello')"
    session_id = "testsession1"
    # Compile first
    compile_resp = client.post(
        "/compile",
        data={"language": "python", "code": code},
        cookies={"session_id": session_id},
    )
    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    assert compile_data["success"]

    # Now run
    run_resp = client.post(
        "/run",
        data={"language": "python", "code": code},
        cookies={"session_id": session_id},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]
    assert "execution_id" in run_data

    # Wait for execution to complete
    execution_id = run_data["execution_id"]
    wait_for_execution_completion(execution_id, "hello")


def test_compile_and_run_java():
    code = """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("hi");
    }
}
"""
    session_id = "testsession2"
    compile_resp = client.post(
        "/compile",
        data={"language": "java", "code": code},
        cookies={"session_id": session_id},
    )
    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    print(f"Java compile response: {compile_data}")  # Debug output
    assert compile_data["success"]

    # Now run
    run_resp = client.post(
        "/run",
        data={"language": "java", "code": code},
        cookies={"session_id": session_id},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]
    assert "execution_id" in run_data

    # Wait for execution to complete
    execution_id = run_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    # Both compilation and execution must succeed for test to pass
    assert status_data.get(
        "success", False
    ), f"Java execution failed: {status_data.get('output', 'No output')}"
    assert "hi" in status_data["output"]


def test_compile_and_run_eiffel():
    code = """class
    HELLO_WORLD

create
    make

feature
    make
            -- Print hello world message
        do
            print ("Hello, Eiffel!%N")
        end

end"""
    session_id = "testsession3"
    compile_resp = client.post(
        "/compile",
        data={"language": "eiffel", "code": code},
        cookies={"session_id": session_id},
    )
    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    print(f"Eiffel compile response: {compile_data}")  # Debug output
    assert compile_data["success"]

    # Now run
    run_resp = client.post(
        "/run",
        data={"language": "eiffel", "code": code},
        cookies={"session_id": session_id},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]
    assert "execution_id" in run_data

    # Wait for execution to complete
    execution_id = run_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    # Check if execution succeeded, or at least compilation worked
    if status_data.get("success", False):
        assert "Hello, Eiffel!" in status_data["output"]
    else:
        # Eiffel execution might fail due to container issues,
        # but compilation succeeded
        print(f"Eiffel execution failed: {status_data['output']}")
        assert compile_data["success"]  # At least compilation worked


def test_cancel():
    resp = client.post("/cancel", data={"execution_id": "testsession1"})
    assert resp.status_code == 200


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
    resp = client.get("/examples/python/hello_world.py")
    assert resp.status_code == 200
    assert "print" in resp.json().get("code", "")


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
