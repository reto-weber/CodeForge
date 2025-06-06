"""
Docker Container Manager for Code Execution

This module handles Docker container lifecycle for secure code execution.
Each user session gets a dedicated container for isolation.
"""

import docker
import os
import tempfile
import uuid
import time
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContainerManager:
    """Manages Docker containers for code execution."""

    def __init__(self):
        """Initialize the Docker client."""
        try:
            self.client = None

            # Try Linux/WSL Docker connection methods
            # Method 1: Try from environment (default Linux socket)
            try:
                self.client = docker.from_env()
                self.client.ping()
                logger.info("Docker client initialized from environment")
            except Exception as env_e:
                logger.debug(f"Failed to initialize from env: {env_e}")

                # Method 2: Try Unix socket directly
                try:
                    self.client = docker.DockerClient(
                        base_url="unix://var/run/docker.sock"
                    )
                    self.client.ping()
                    logger.info("Docker client initialized via Unix socket")
                except Exception as socket_e:
                    logger.debug(f"Failed via Unix socket: {socket_e}")

                    # Method 3: Try TCP for Docker-in-Docker scenarios
                    try:
                        self.client = docker.DockerClient(
                            base_url="tcp://localhost:2376"
                        )
                        self.client.ping()
                        logger.info("Docker client initialized via TCP")
                    except Exception as tcp_e:
                        logger.debug(f"Failed via TCP: {tcp_e}")

                        # All methods failed
                        raise Exception(
                            f"All Docker connection methods failed. "
                            f"env={env_e}, socket={socket_e}, tcp={tcp_e}"
                        )

            if self.client is None:
                raise Exception("Failed to initialize Docker client")

        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise RuntimeError(f"Docker is not available: {e}")

        self.active_containers: Dict[str, dict] = {}
        self.image_name = "code-executor:latest"

    def build_execution_image(self) -> bool:
        """Build the Docker image for code execution."""
        try:
            dockerfile_path = Path(__file__).parent / "Dockerfile.execution"
            if not dockerfile_path.exists():
                logger.error("Dockerfile.execution not found")
                return False

            logger.info("Building execution Docker image...")
            self.client.images.build(
                path=str(dockerfile_path.parent),
                dockerfile="Dockerfile.execution",
                tag=self.image_name,
                rm=True,
                forcerm=True,
            )
            logger.info("Docker image built successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to build Docker image: {e}")
            return False

    def ensure_image_exists(self) -> bool:
        """Ensure the execution image exists, build if necessary."""
        try:
            self.client.images.get(self.image_name)
            logger.info("Execution image already exists")
            return True
        except docker.errors.ImageNotFound:
            logger.info("Execution image not found, building...")
            return self.build_execution_image()
        except Exception as e:
            logger.error(f"Error checking image: {e}")
            return False

    def create_session_container(self, session_id: str) -> Optional[str]:
        """Create a new container for a user session."""
        try:
            if not self.ensure_image_exists():
                return None

            container_name = f"code-session-{session_id}"

            # Remove existing container if it exists
            self.cleanup_session_container(session_id)

            container = self.client.containers.run(
                self.image_name,
                name=container_name,
                detach=True,
                remove=False,  # We'll remove manually for cleanup control
                working_dir="/workspace",
                mem_limit="512m",  # Memory limit for security
                cpu_quota=50000,  # CPU limit (50% of one core)
                network_disabled=True,  # Disable network for security
                user="coderunner",
                command="sleep infinity",  # Keep container running
            )

            self.active_containers[session_id] = {
                "container": container,
                "container_id": container.id,
                "created_at": time.time(),
                "name": container_name,
            }

            logger.info(f"Created container {container_name} for session {session_id}")
            return container.id

        except Exception as e:
            logger.error(f"Failed to create container for session {session_id}: {e}")
            return None

    def execute_code(
        self, session_id: str, code: str, language: str, timeout: int = 30
    ) -> Tuple[bool, str, int]:
        """Execute code in the session container."""
        try:
            if session_id not in self.active_containers:
                if not self.create_session_container(session_id):
                    return False, "Failed to create execution container", -1

            container_info = self.active_containers[session_id]
            container = container_info["container"]

            # Refresh container object to ensure it's current
            try:
                container.reload()
                if container.status != "running":
                    logger.info(
                        f"Container {container.name} is not running, recreating..."
                    )
                    if not self.create_session_container(session_id):
                        return False, "Failed to recreate execution container", -1
                    container = self.active_containers[session_id]["container"]
            except Exception:
                # Container might not exist, recreate it
                if not self.create_session_container(session_id):
                    return False, "Failed to recreate execution container", -1
                container = self.active_containers[session_id]["container"]

            # Determine file extension and execution command
            file_extensions = {"python": "py", "c": "c", "cpp": "cpp", "java": "java"}

            file_ext = file_extensions.get(language, "txt")
            filename = f"code.{file_ext}"

            # Write code to container
            container.put_archive(
                "/workspace", self._create_tar_archive(filename, code)
            )

            # Prepare execution command based on language
            if language == "python":
                cmd = f"python3 {filename}"
            elif language == "c":
                cmd = f"gcc {filename} -o code.out && ./code.out"
            elif language == "cpp":
                cmd = f"g++ {filename} -o code.out && ./code.out"
            elif language == "java":
                # Extract class name for Java
                import re

                match = re.search(r"public\s+class\s+(\w+)", code)
                if match:
                    class_name = match.group(1)
                    # Rename file to match class name
                    java_filename = f"{class_name}.java"
                    container.exec_run(f"mv {filename} {java_filename}")
                    cmd = f"javac {java_filename} && java {class_name}"
                else:
                    cmd = f"javac {filename} && java $(basename {filename} .java)"
            else:
                return False, f"Unsupported language: {language}", -1

            # Execute the command
            exec_result = container.exec_run(
                f"timeout {timeout} bash -c '{cmd}'",
                stdout=True,
                stderr=True,
                stream=False,
                demux=True,
            )

            exit_code = exec_result.exit_code
            stdout = (
                exec_result.output[0].decode("utf-8") if exec_result.output[0] else ""
            )
            stderr = (
                exec_result.output[1].decode("utf-8") if exec_result.output[1] else ""
            )

            # Combine stdout and stderr for output
            output = stdout if exit_code == 0 else (stderr or stdout)

            # Handle timeout
            if exit_code == 124:  # timeout command exit code
                output = f"Execution timed out after {timeout} seconds"
                exit_code = -1

            success = exit_code == 0

            logger.info(
                f"Code execution completed for session {session_id}: exit_code={exit_code}"
            )
            return success, output, exit_code

        except Exception as e:
            logger.error(f"Error executing code for session {session_id}: {e}")
            return False, f"Execution error: {str(e)}", -1

    def cancel_execution(self, session_id: str) -> bool:
        """Cancel running execution in the session container."""
        try:
            if session_id not in self.active_containers:
                return False

            container = self.active_containers[session_id]["container"]

            # Kill all processes in the container
            try:
                container.exec_run("pkill -f 'timeout|python3|gcc|g++|java|javac'")
                logger.info(f"Cancelled execution for session {session_id}")
                return True
            except Exception as e:
                logger.error(
                    f"Error cancelling execution for session {session_id}: {e}"
                )
                return False

        except Exception as e:
            logger.error(f"Error cancelling execution for session {session_id}: {e}")
            return False

    def cleanup_session_container(self, session_id: str) -> bool:
        """Clean up the container for a session."""
        try:
            if session_id in self.active_containers:
                container_info = self.active_containers[session_id]
                container = container_info["container"]

                try:
                    container.stop(timeout=5)
                    container.remove()
                    logger.info(f"Cleaned up container for session {session_id}")
                except Exception as e:
                    logger.warning(
                        f"Error stopping/removing container for session {session_id}: {e}"
                    )

                del self.active_containers[session_id]
                return True
            else:
                # Try to find and remove container by name
                container_name = f"code-session-{session_id}"
                try:
                    container = self.client.containers.get(container_name)
                    container.stop(timeout=5)
                    container.remove()
                    logger.info(f"Cleaned up orphaned container {container_name}")
                except docker.errors.NotFound:
                    pass  # Container doesn't exist, which is fine
                except Exception as e:
                    logger.warning(
                        f"Error cleaning up orphaned container {container_name}: {e}"
                    )

                return True

        except Exception as e:
            logger.error(f"Error cleaning up container for session {session_id}: {e}")
            return False

    def cleanup_old_containers(self, max_age_hours: int = 24) -> int:
        """Clean up containers older than specified hours."""
        cleaned_count = 0
        current_time = time.time()

        sessions_to_cleanup = []
        for session_id, container_info in self.active_containers.items():
            age_hours = (current_time - container_info["created_at"]) / 3600
            if age_hours > max_age_hours:
                sessions_to_cleanup.append(session_id)

        for session_id in sessions_to_cleanup:
            if self.cleanup_session_container(session_id):
                cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} old containers")
        return cleaned_count

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """Get information about a session container."""
        if session_id not in self.active_containers:
            return None

        container_info = self.active_containers[session_id]
        try:
            container = container_info["container"]
            container.reload()

            return {
                "session_id": session_id,
                "container_id": container_info["container_id"],
                "status": container.status,
                "created_at": container_info["created_at"],
                "age_seconds": time.time() - container_info["created_at"],
            }
        except Exception as e:
            logger.error(f"Error getting session info for {session_id}: {e}")
            return None

    def _create_tar_archive(self, filename: str, content: str) -> bytes:
        """Create a tar archive containing the file with given content."""
        import tarfile
        import io

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            file_data = content.encode("utf-8")
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(file_data)
            tarinfo.mode = 0o644
            tar.addfile(tarinfo, io.BytesIO(file_data))

        tar_buffer.seek(0)
        return tar_buffer.getvalue()


# Global container manager instance
container_manager = None


def get_container_manager() -> ContainerManager:
    """Get the global container manager instance."""
    global container_manager
    if container_manager is None:
        container_manager = ContainerManager()
    return container_manager
