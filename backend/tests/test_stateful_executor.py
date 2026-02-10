"""
Tests for StatefulDockerExecutor
"""

import pytest
import requests
import pandas as pd
from unittest.mock import MagicMock, patch
from docker.errors import NotFound
from app.services.stateful_docker_executor import StatefulDockerExecutor

@pytest.fixture
def mock_docker_client():
    with patch('app.services.stateful_docker_executor.docker') as mock_docker_lib:
        client = MagicMock()
        mock_docker_lib.from_env.return_value = client
        mock_docker_lib.errors.NotFound = NotFound
        yield client

@pytest.fixture
def executor(mock_docker_client):
    return StatefulDockerExecutor()

@pytest.mark.asyncio
async def test_stateful_execution_flow(executor, mock_docker_client):
    # Mock container lookup (returns NotFound first, then returns container)
    mock_docker_client.containers.get.side_effect = NotFound("Container not found")

    # Mock container creation
    mock_container = MagicMock()
    mock_container.attrs = {
        'NetworkSettings': {
            'Ports': {'5000/tcp': [{'HostPort': '32000'}]}
        }
    }
    mock_docker_client.containers.run.return_value = mock_container

    # Mock requests.post to the container
    with patch('requests.post') as mock_post:
        # First execution: Define variable x
        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = {
            "success": True,
            "stdout": "",
            "stderr": "",
            "variables": {"x": 10},
            "visualizations": []
        }
        mock_post.return_value = mock_response_1

        result1 = await executor.execute("x = 10", conversation_id="test_session")

        # Verify container created
        mock_docker_client.containers.run.assert_called_once()
        # Verify port binding is safe
        run_args = mock_docker_client.containers.run.call_args[1]
        assert run_args['ports']['5000/tcp'] == ('127.0.0.1', None)

        # Second execution: Use variable x
        mock_docker_client.containers.get.side_effect = None
        mock_docker_client.containers.get.return_value = mock_container

        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = {
            "success": True,
            "stdout": "20",
            "stderr": "",
            "variables": {"y": 20},
            "visualizations": []
        }
        mock_post.return_value = mock_response_2

        result2 = await executor.execute("y = x * 2; print(y)", conversation_id="test_session")

        assert result2["success"] is True
        assert result2["result"]["y"] == 20

@pytest.mark.asyncio
async def test_data_loading(executor, mock_docker_client):
    mock_container = MagicMock()
    mock_container.attrs = {'NetworkSettings': {'Ports': {'5000/tcp': [{'HostPort': '32000'}]}}}
    mock_docker_client.containers.get.return_value = mock_container

    df = pd.DataFrame({'a': [1, 2]})

    with patch('requests.post') as mock_post, \
         patch('tempfile.NamedTemporaryFile') as mock_temp, \
         patch('tarfile.open') as mock_tar, \
         patch('os.unlink'):

        mock_temp.return_value.__enter__.return_value.name = "/tmp/fake.parquet"
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        await executor.execute("print(df)", dataframe=df, conversation_id="test_session")

        # Verify put_archive called
        mock_container.put_archive.assert_called_once()
        # Verify data_path sent in payload
        call_args = mock_post.call_args
        assert call_args[1]['json']['data_path'] == "/app/data.parquet"
