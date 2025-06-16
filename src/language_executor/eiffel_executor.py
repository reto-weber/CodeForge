import os
from typing import Optional, Tuple

import tree_sitter_eiffel as eiffel
from jinja2 import Template
from tree_sitter import Language, Parser, Query, QueryCursor

from container_manager import get_container_manager

from .base import LanguageExecutor


class EiffelExecutor(LanguageExecutor):

    def __init__(self, version):
        super().__init__(version)
        self.container_mgr = get_container_manager()

    @staticmethod
    def _get_class_name(code: str) -> str:

        e_language = Language(eiffel.language())
        parser = Parser(e_language)
        code_bytes = bytes(code, "utf8")
        tree = parser.parse(code_bytes)

        cursor = QueryCursor(
            Query(e_language, "(class_declaration (class_name) @class_name)")
        )
        captures = cursor.captures(tree.root_node)
        return captures["class_name"][0].text.decode("utf8")

    @staticmethod
    def _get_creation_procedure(code: str):
        e_language = Language(eiffel.language())
        parser = Parser(e_language)
        code_bytes = bytes(code, "utf8")
        tree = parser.parse(code_bytes)

        cursor = QueryCursor(
            Query(
                e_language,
                "(class_declaration (creation_clause (identifier) @creation_procedure))",
            )
        )
        captures = cursor.captures(tree.root_node)
        if not captures or "creation_procedure" not in captures:
            return None, False
        else:
            return captures["creation_procedure"][0].text.decode("utf8"), True

    def _load_ecf_template(self) -> str:
        # Try to load the ECF template from a file in the examples/eiffel directory

        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "../examples/eiffel/ecf_template.xml",
        )

        if not os.path.exists(template_path):
            # Fallback: try absolute path from workspace root
            template_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "../../examples/eiffel/ecf_template.xml"
                )
            )
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"ECF template not found at {template_path}")
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def _put_ecf_to_container(
        self,
        session_id: str,
        creation_procedure: Optional[str] = None,
        class_name: Optional[str] = None,
    ):
        # Check if container already exists, create only if needed
        if session_id not in self.container_mgr.active_containers:
            if not self.container_mgr.create_session_container(session_id, "eiffel"):
                return False, "Failed to create compilation container", None

        # Load and format the ECF template
        template_content = self._load_ecf_template()

        # Use Jinja2 for template rendering
        template = Template(template_content)
        if creation_procedure and class_name:
            formatted_ecf = template.render(
                USE_SPECIFIC_ROOT=True,
                ROOT_CLASS=class_name,
                CREATION_PROCEDURE=creation_procedure,
            )
        else:
            formatted_ecf = template.render(USE_SPECIFIC_ROOT=False)

        if not self.container_mgr.put_file_in_container(
            session_id, "Ace.ecf", formatted_ecf
        ):
            return False, "Failed to copy ECF file to container", None

        return True, "ECF file successfully created", None

    def _put_code_to_container(self, session_id: str, code: str):
        # Check if container already exists, create only if needed
        if session_id not in self.container_mgr.active_containers:
            if not self.container_mgr.create_session_container(session_id, "eiffel"):
                return False, "Failed to create compilation container", None

        class_name = self._get_class_name(code)
        filename = f"{class_name.lower()}.e"
        if not self.container_mgr.put_file_in_container(session_id, filename, code):
            return False, "Failed to copy code to container", None

        return True, "Code file successfully created", None

    def compile(self, code: str, session_id: str) -> Tuple[bool, str, Optional[str]]:
        # Extract class name and creation procedure from the code
        print(f"Compiling Eiffel code for session {session_id}")

        try:
            class_name = self._get_class_name(code)
            creation_procedure, has_creation = self._get_creation_procedure(code)

            # Format ECF template with extracted information
            if has_creation and creation_procedure:
                self._put_ecf_to_container(session_id, creation_procedure, class_name)
            else:
                # Use all_classes root if no specific creation procedure found
                self._put_ecf_to_container(session_id)

        except Exception as e:
            print(f"Error parsing Eiffel code: {e}")
            # Fallback to all_classes root
            self._put_ecf_to_container(session_id)

        self._put_code_to_container(session_id, code)
        cmd = "apb -c_compile -batch"
        exec_result = self.container_mgr.run_command_in_container(session_id, cmd, 60)
        if exec_result is None:
            return False, "Failed to compile code in container", None
        stdout = exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
        stderr = exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
        exit_code = exec_result.exit_code
        output = stdout if exit_code == 0 else (stderr or stdout)
        success = exit_code == 0
        output_path = self._get_class_name(code) if success else None
        return success, output, output_path

    def execute(
        self, code: str, session_id: str, timeout: int = 60
    ) -> Tuple[bool, str, int]:
        print(f"Executing Eiffel code for session {session_id}")
        run_cmd = "./EIFGENs/tests/W_code/autoproof-tests"
        run_result = self.container_mgr.run_command_in_container(
            session_id, run_cmd, timeout
        )
        if run_result is None:
            return False, "Failed to execute binary in container", -1
        stdout = run_result.output[0].decode("utf-8") if run_result.output[0] else ""
        # stderr = run_result.output[1].decode("utf-8") if run_result.output[1] else ""
        exit_code = run_result.exit_code
        output = stdout
        success = exit_code == 0
        return success, output, exit_code

    def verify(
        self, code: str, session_id: str, timeout: int = 60
    ) -> Tuple[bool, str, int]:
        # Extract class name and creation procedure from the code
        try:
            class_name = self._get_class_name(code)
            creation_procedure, has_creation = self._get_creation_procedure(code)

            # Format ECF template with extracted information
            if has_creation and creation_procedure:
                self._put_ecf_to_container(session_id, creation_procedure, class_name)
            else:
                # Use all_classes root if no specific creation procedure found
                self._put_ecf_to_container(session_id)

        except Exception as e:
            print(f"Error parsing Eiffel code: {e}")
            # Fallback to all_classes root
            self._put_ecf_to_container(session_id)

        self._put_code_to_container(session_id, code)
        run_cmd = "apb -c_compile -batch -autoproof -html"
        run_result = self.container_mgr.run_command_in_container(
            session_id, run_cmd, timeout
        )
        if run_result is None:
            return False, "Failed to execute binary in container", -1
        stdout = run_result.output[0].decode("utf-8") if run_result.output[0] else ""
        stderr = run_result.output[1].decode("utf-8") if run_result.output[1] else ""
        exit_code = run_result.exit_code
        output = run_result.output[0].decode()
        success = exit_code == 0
        return success, output, exit_code
