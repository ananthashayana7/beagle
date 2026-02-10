"""
Stateful Docker Executor Service
Executes Python code in a persistent Docker container session
"""

import os
import json
import time
import requests
import traceback
import tarfile
import tempfile
import io
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import docker
from docker.errors import DockerException, APIError, ContainerError, NotFound

from app.config import settings

class StatefulDockerExecutor:
    """
    Execute Python code in a persistent Docker container session.

    This executor maintains a running container for each conversation/session,
    allowing variables to persist between executions. It communicates with the
    container via an internal Flask server.
    """

    def __init__(self):
        try:
            self.client = docker.from_env()
        except DockerException:
            self.client = None

        self.image = "beagle-sandbox"

    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate code for basic security issues.
        """
        # Block subprocess/os calls
        dangerous_terms = ['os.system', 'subprocess.']
        for term in dangerous_terms:
            if term in code:
                return False, f"Blocked term detected: {term}"

        return True, None

    async def execute(
        self,
        code: str,
        dataframe: Optional[pd.DataFrame] = None,
        timeout: int = 30,
        conversation_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Execute Python code in a persistent session.

        Args:
            code: Python code to execute
            dataframe: Optional dataframe to load (if provided, it refreshes 'df')
            timeout: Execution timeout in seconds
            conversation_id: ID for the session container

        Returns:
            Dictionary with execution results
        """
        if not self.client:
             return {
                "success": False,
                "error": "Docker client not initialized. Is Docker running?",
                "result": None,
                "execution_time_ms": 0,
                "visualizations": None
            }

        start_time = time.time()

        try:
            # get or create container for this session
            container, port = self._get_session_container(conversation_id)

            data_path_in_container = None
            if dataframe is not None:
                # Use put_archive to copy dataframe into container
                # 1. Create a tar archive in memory containing data.parquet
                data_path_in_container = "/app/data.parquet"

                with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
                    dataframe.to_parquet(tf.name)
                    tf.close()

                    # Create tar stream
                    tar_stream = io.BytesIO()
                    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                        tar.add(tf.name, arcname='data.parquet')

                    tar_stream.seek(0)

                    # 2. Copy to container
                    try:
                        container.put_archive("/app", tar_stream)
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"Failed to upload data to container: {e}",
                            "stdout": "",
                            "stderr": str(e),
                            "result": None,
                            "execution_time_ms": 0,
                            "visualizations": None
                        }
                    finally:
                        os.unlink(tf.name)

            # Construct request payload
            payload = {
                "code": code,
                "data_path": data_path_in_container
            }

            # Send request to container
            container_url = f"http://localhost:{port}/execute"

            try:
                response = requests.post(container_url, json=payload, timeout=timeout)
                response.raise_for_status()
                result_data = response.json()

                execution_time = int((time.time() - start_time) * 1000)

                return {
                    "success": result_data.get("success", False),
                    "error": result_data.get("stderr") if not result_data.get("success") else None,
                    "stdout": result_data.get("stdout"),
                    "stderr": result_data.get("stderr"),
                    "result": result_data.get("variables", {}),
                    "execution_time_ms": execution_time,
                    "visualizations": result_data.get("visualizations", [])
                }

            except requests.exceptions.Timeout:
                # If timeout, we might need to restart container as it's stuck
                container.restart()
                return {
                    "success": False,
                    "error": f"Execution timed out after {timeout} seconds",
                    "stdout": "",
                    "stderr": "TimeoutExpired",
                    "result": None,
                    "execution_time_ms": timeout * 1000,
                    "visualizations": None
                }

            except requests.exceptions.RequestException as e:
                return {
                    "success": False,
                    "error": f"Communication error with sandbox: {str(e)}",
                    "stdout": "",
                    "stderr": str(e),
                    "result": None,
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "visualizations": None
                }

        except Exception as e:
             return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": traceback.format_exc(),
                "result": None,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "visualizations": None
            }

    def _get_session_container(self, conversation_id: str) -> Tuple[Any, int]:
        """Find or create a container for the session"""
        container_name = f"beagle-session-{conversation_id}"

        try:
            container = self.client.containers.get(container_name)
            if container.status != 'running':
                container.start()
                self._wait_for_server(container)

            # Find mapped port
            container.reload() # Refresh attributes
            ports = container.attrs['NetworkSettings']['Ports']
            # '5000/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '32768'}]
            host_port = int(ports['5000/tcp'][0]['HostPort'])
            return container, host_port

        except NotFound:
            # Create new container
            # We publish 5000 to a random host port on localhost
            container = self.client.containers.run(
                image=self.image,
                name=container_name,
                ports={'5000/tcp': ('127.0.0.1', None)}, # Bind to random port on localhost only
                detach=True,
                mem_limit="1g",
                cpu_period=100000,
                cpu_quota=50000,
                network_mode="bridge",
                cap_drop=['ALL'],
                security_opt=['no-new-privileges']
            )

            self._wait_for_server(container)

            container.reload()
            ports = container.attrs['NetworkSettings']['Ports']
            host_port = int(ports['5000/tcp'][0]['HostPort'])
            return container, host_port

    def _wait_for_server(self, container, timeout=5):
        """Wait for Flask server to be ready"""
        # Simple sleep for now, proper healthcheck loop better
        time.sleep(2)
