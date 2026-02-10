"""
Tests for DockerExecutor with Mocks
"""

import pytest
import os
import json
from unittest.mock import MagicMock, patch
import docker
from app.services.docker_executor import DockerExecutor

@pytest.fixture
def mock_docker_client():
    with patch('app.services.docker_executor.docker') as mock_docker_lib:
        client = MagicMock()
        mock_docker_lib.from_env.return_value = client
        yield client

@pytest.mark.asyncio
async def test_docker_execution_success(mock_docker_client):
    # We need to instantiate executor ensuring docker.from_env() returns our mock
    executor = DockerExecutor()

    # Setup container mock
    container = MagicMock()
    executor.client.containers.run.return_value = container

    # Configure logs (bytes)
    container.logs.side_effect = lambda stdout=False, stderr=False: b"Output" if stdout else b""

    # Mock container.wait to simulate successful run AND write the result file
    def side_effect_wait(timeout=None):
        # Inspect the run call to find the temp directory
        # executor.client.containers.run was called with volumes={temp_dir: ...}
        call_args = executor.client.containers.run.call_args
        if not call_args:
            return {'StatusCode': 1}

        kwargs = call_args[1]
        volumes = kwargs.get('volumes', {})
        if volumes:
            temp_dir = list(volumes.keys())[0]

            # Create result.json in that directory
            result_data = {
                "variables": {"x": 42},
                "visualizations": []
            }
            with open(os.path.join(temp_dir, "result.json"), "w") as f:
                json.dump(result_data, f)

        return {'StatusCode': 0}

    container.wait.side_effect = side_effect_wait

    # Execute
    result = await executor.execute("x = 42")

    assert result["success"] is True
    assert result["result"]["x"] == 42

    # Verify docker call
    executor.client.containers.run.assert_called_once()
    kwargs = executor.client.containers.run.call_args[1]
    assert kwargs['image'] == "beagle-sandbox"
    assert kwargs['network_mode'] == "none"
    assert kwargs['mem_limit'] == "512m"

@pytest.mark.asyncio
async def test_docker_execution_timeout(mock_docker_client):
    executor = DockerExecutor()
    container = MagicMock()
    executor.client.containers.run.return_value = container

    # Simulate timeout
    # The executor catches generic Exception and assumes timeout if it fails during wait?
    # No, strictly:
    # try: result = container.wait(timeout=timeout)
    # except Exception as e: container.kill(); raise TimeoutError...

    container.wait.side_effect = Exception("Read timed out")

    result = await executor.execute("while True: pass", timeout=1)

    assert result["success"] is False
    assert "Execution timed out" in result["error"]
    container.kill.assert_called_once()

@pytest.mark.asyncio
async def test_docker_init_fail():
    # Test when docker is not available
    # We need to ensure docker.from_env() raises DockerException
    with patch('app.services.docker_executor.docker') as mock_docker_lib:
        # We need the real DockerException class because the code imports it
        from docker.errors import DockerException
        mock_docker_lib.from_env.side_effect = DockerException("Docker not running")

        executor = DockerExecutor()
        assert executor.client is None

        result = await executor.execute("print('hello')")
        assert result["success"] is False
        assert "Docker client not initialized" in result["error"]
