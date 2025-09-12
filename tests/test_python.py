"""
Python language tests for the code compiler and runner API.
"""

from conftest import wait_for_execution_completion, create_session_client


def test_run_python():
    """Test direct Python code execution."""
    files = [{"name": "hello.py", "content": "print('hello')"}]
    session_client = create_session_client()
    resp = session_client.post(
        "/run",
        json={"language": "python", "files": files, "main_file": "hello.py"},
    )
    assert resp.status_code == 200
    data = resp.json()
    print(f"Run response: {data}")  # Debug output
    assert data["success"]
    assert "execution_id" in data

    # Wait for execution to complete and verify output
    execution_id = data["execution_id"]
    result = wait_for_execution_completion(execution_id)
    assert "hello" in result["output"]


def test_python_with_variables():
    """Test Python code with variables and calculations."""
    files = [
        {
            "name": "variables.py",
            "content": """
x = 5
y = 10
result = x + y
print(f"Result: {result}")
""",
        }
    ]
    session_client = create_session_client()
    resp = session_client.post(
        "/run",
        json={"language": "python", "files": files, "main_file": "variables.py"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"]
    assert "execution_id" in data

    # Wait for execution to complete and verify output
    execution_id = data["execution_id"]
    result = wait_for_execution_completion(execution_id)
    assert "Result: 15" in result["output"]


def test_compile_and_run_python():
    """Test Python compile-then-run workflow."""
    files = [{"name": "hello.py", "content": "print('hello from compile-run')"}]
    session_client = create_session_client()

    # Compile first
    compile_resp = session_client.post(
        "/compile",
        json={"language": "python", "files": files, "main_file": "hello.py"},
    )
    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    assert compile_data["success"]

    # Now run using the same session
    run_resp = session_client.post(
        "/run",
        json={"language": "python", "files": files, "main_file": "hello.py"},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]
    assert "execution_id" in run_data

    # Verify session consistency
    print(f"Session ID from run response: {run_data['session_id']}")

    # Wait for execution to complete
    execution_id = run_data["execution_id"]
    result = wait_for_execution_completion(execution_id)
    assert "hello from compile-run" in result["output"]
