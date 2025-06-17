from .base import LanguageExecutor, FileInfo
from typing import Tuple, Optional, Union, List
from container_manager import get_container_manager


class CExecutor(LanguageExecutor):
    def _normalize_input(
        self, code: Union[str, List[FileInfo]], main_file: Optional[str] = None
    ) -> Tuple[List[FileInfo], str]:
        """
        Convert input to normalized format for C.
        Ensures single-file mode creates a .c file.
        """
        if isinstance(code, str):
            # Legacy single-file mode - ensure .c extension
            filename = main_file or "main.c"
            if not filename.endswith(".c"):
                if "." in filename:
                    filename = filename.rsplit(".", 1)[0] + ".c"
                else:
                    filename = filename + ".c"
            return [FileInfo(filename, code)], filename
        else:
            # Multi-file mode
            files = code
            if main_file:
                return files, main_file
            else:
                # If no main file specified, use the first .c file or first file
                c_files = [f for f in files if f.name.endswith(".c")]
                if c_files:
                    main_filename = c_files[0].name
                elif files:
                    main_filename = files[0].name
                else:
                    main_filename = "main.c"
                return files, main_filename

    def compile(
        self,
        code: Union[str, List[FileInfo]],
        session_id: str,
        main_file: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        print(f"Compiling C code for session {session_id}")
        container_mgr = get_container_manager()

        if not container_mgr.create_session_container(session_id, "c"):
            return False, "Failed to create compilation container", None

        # Handle both legacy string and new multi-file formats
        files, _ = self._normalize_input(code, main_file)

        # Write all files to container
        if not self._write_files_to_container(files, session_id):
            return False, "Failed to copy files to container", None

        # For C, compile all .c files together
        c_files = [f.name for f in files if f.name.endswith(".c")]
        if not c_files:
            return False, "No C source files found", None

        cmd = f"gcc {' '.join(c_files)} -o code.out"
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
        self,
        code: Union[str, List[FileInfo]],
        session_id: str,
        timeout: int = 30,
        main_file: Optional[str] = None,
    ) -> Tuple[bool, str, int]:
        print(f"Executing C code for session {session_id}")
        container_mgr = get_container_manager()

        # For multi-file execution, write files if needed
        if isinstance(code, list):
            if not self._write_files_to_container(code, session_id):
                return False, "Failed to copy files to container", -1

        # Only run the binary, do not compile
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
