import re
from typing import Optional, Tuple

from container_manager import get_container_manager

from .base import LanguageExecutor


class JavaExecutor(LanguageExecutor):
    def compile(self, code: str, session_id: str) -> Tuple[bool, str, Optional[str]]:
        print(f"Compiling Java code in session {session_id}")
        container_mgr = get_container_manager()
        filename = "code.java"
        if not container_mgr.create_session_container(session_id, "java"):
            return False, "Failed to create compilation container", None
        if not container_mgr.put_file_in_container(session_id, filename, code):
            return False, "Failed to copy code to container", None
        match = re.search(r"public\s+class\s+(\w+)", code)
        if match:
            class_name = match.group(1)
            java_filename = f"{class_name}.java"
            container_mgr.run_command_in_container(
                session_id, f"mv {filename} {java_filename}", 5
            )
            cmd = f"javac {java_filename}"
        else:
            class_name = "code"
            cmd = f"javac {filename}"
        exec_result = container_mgr.run_command_in_container(session_id, cmd, 30)
        if exec_result is None:
            return False, "Failed to compile code in container", None
        stdout = exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
        stderr = exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
        exit_code = exec_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        # Return class name for execution
        output_path = class_name if success else None
        return success, output, output_path

    def execute(
        self, code: str, session_id: str, timeout: int = 30
    ) -> Tuple[bool, str, int]:
        print(f"Executing Java code in session {session_id}")
        container_mgr = get_container_manager()
        # Extract class name
        match = re.search(r"public\s+class\s+(\w+)", code)
        if match:
            class_name = match.group(1)
        else:
            class_name = "code"
        run_cmd = f"java {class_name}"
        run_result = container_mgr.run_command_in_container(
            session_id, run_cmd, timeout
        )
        if run_result is None:
            return False, "Failed to execute class in container", -1
        stdout = run_result.output[0].decode("utf-8") if run_result.output[0] else ""
        stderr = run_result.output[1].decode("utf-8") if run_result.output[1] else ""
        exit_code = run_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        return success, output, exit_code
