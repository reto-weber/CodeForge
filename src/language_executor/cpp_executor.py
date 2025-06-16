from .base import LanguageExecutor
from typing import Tuple, Optional
from container_manager import get_container_manager


class CppExecutor(LanguageExecutor):
    def compile(self, code: str, session_id: str) -> Tuple[bool, str, Optional[str]]:
        container_mgr = get_container_manager()
        filename = "code.cpp"
        if not container_mgr.create_session_container(session_id, "cpp"):
            return False, "Failed to create compilation container", None
        if not container_mgr.put_file_in_container(session_id, filename, code):
            return False, "Failed to copy code to container", None
        cmd = f"g++ {filename} -o code.out"
        exec_result = container_mgr.run_command_in_container(session_id, cmd, 30)
        if exec_result is None:
            return False, "Failed to compile code in container", None
        stdout = exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
        stderr = exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
        exit_code = exec_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        output_path = "code.out" if success else None
        return success, output, output_path

    def execute(
        self, code: str, session_id: str, timeout: int = 30
    ) -> Tuple[bool, str, int]:
        container_mgr = get_container_manager()
        run_cmd = "./code.out"
        run_result = container_mgr.run_command_in_container(
            session_id, run_cmd, timeout
        )
        if run_result is None:
            return False, "Failed to execute binary in container", -1
        stdout = run_result.output[0].decode("utf-8") if run_result.output[0] else ""
        stderr = run_result.output[1].decode("utf-8") if run_result.output[1] else ""
        exit_code = run_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        return success, output, exit_code
