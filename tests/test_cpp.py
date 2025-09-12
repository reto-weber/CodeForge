"""
C++ language tests for the code compiler and runner API.
"""

from conftest import client, wait_for_execution_completion


def test_compile_and_run_cpp():
    files = [
        {
            "name": "hello_world.cpp",
            "content": """
#include <iostream>

int main() {
    std::cout << "Hello, C++!" << std::endl;
    return 0;
}
""",
        },
    ]

    session_id = "multifile_cpp"

    # Compile first
    compile_resp = client.post(
        "/compile",
        json={"language": "cpp", "files": files, "main_file": "hello_world.cpp"},
        cookies={"session_id": session_id},
    )

    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    assert compile_data["success"]

    # Run the compiled program
    run_resp = client.post(
        "/run",
        json={
            "language": "cpp",
            "files": files,
            "main_file": "hello_world.cpp",
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

    assert "Hello, C++!" in status_data["output"]


def test_cpp_with_variables():
    files = [
        {
            "name": "calculator.cpp",
            "content": """
#include <iostream>

int main() {
    int x =  5;
    int y = 10;
    int result = x + y;
    std::cout << "Result: " << result << std::endl;
    return 0;
}
""",
        },
    ]

    session_id = "multifile_cpp"

    # Compile first
    compile_resp = client.post(
        "/compile",
        json={"language": "cpp", "files": files, "main_file": "calculator.cpp"},
        cookies={"session_id": session_id},
    )

    assert compile_resp.status_code == 200
    compile_data = compile_resp.json()
    assert compile_data["success"]

    # Run the compiled program
    run_resp = client.post(
        "/run",
        json={
            "language": "cpp",
            "files": files,
            "main_file": "calculator.cpp",
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
    assert compile_data["success"]
