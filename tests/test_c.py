"""
C language tests for the code compiler and runner API.
"""

from conftest import client, wait_for_execution_completion, create_session_client
from src.models import FileInfo


def test_compile_and_run_c():
    """Test C multi-file project with header and implementation."""
    files = [
        {
            "name": "hello_world.c",
            "content": """
#include <stdio.h>

int main() {
    printf("Hello, C!\\n");
    return 0;
}""",
        },
    ]

    session_id = "multifile_c"

    # Compile first
    compile_resp = client.post(
        "/compile",
        json={"language": "c", "files": files, "main_file": "hello_world.c"},
        cookies={"session_id": session_id},
    )

    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    assert compile_data["success"]

    # Run the compiled program
    run_resp = client.post(
        "/run",
        json={
            "language": "c",
            "files": files,
            "main_file": "hello_world.c",
            "timeout": 30,
        },
        cookies={"session_id": session_id},
    )

    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]

    # Wait for execution and check output
    execution_id = run_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    assert "Hello, C!" in status_data["output"]


def test_c_with_variables():
    """Test C multi-file project with header and implementation."""
    files = [
        {
            "name": "main.c",
            "content": """
#include <stdio.h>

int main() {
    int x = 5;
    int y = 10;
    int result = x + y;
    printf("Result: %d\\n", result);
    return 0;
}
""",
        },
    ]

    session_id = "multifile_c"

    # Compile first
    compile_resp = client.post(
        "/compile",
        json={"language": "c", "files": files, "main_file": "main.c"},
        cookies={"session_id": session_id},
    )

    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    assert compile_data["success"]

    # Run the compiled program
    run_resp = client.post(
        "/run",
        json={
            "language": "c",
            "files": files,
            "main_file": "main.c",
            "timeout": 30,
        },
        cookies={"session_id": session_id},
    )

    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["success"]

    # Wait for execution and check output
    execution_id = run_data["execution_id"]
    status_data = wait_for_execution_completion(execution_id)

    assert "Result: 15" in status_data["output"]
    print(f"C execution failed: {status_data['output']}")
    assert compile_data["success"]  # At least compilation worked
