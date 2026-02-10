"""
Tests for ProcessExecutor with Visualization
"""

import pytest
import pandas as pd
import numpy as np
import base64
import json
from app.services.process_executor import ProcessExecutor

@pytest.fixture
def executor():
    return ProcessExecutor()

@pytest.mark.asyncio
async def test_matplotlib_capture(executor):
    code = """
import matplotlib.pyplot as plt
plt.plot([1, 2, 3], [4, 5, 6])
plt.show()
"""
    result = await executor.execute(code)
    if not result["success"]:
        print(f"STDOUT: {result['stdout']}")
        print(f"STDERR: {result['stderr']}")
    assert result["success"] is True
    assert result["visualizations"] is not None
    assert len(result["visualizations"]) == 1
    assert result["visualizations"][0]["type"] == "image"
    assert result["visualizations"][0]["format"] == "png"
    # Verify content is base64
    assert base64.b64decode(result["visualizations"][0]["content"])

@pytest.mark.asyncio
async def test_plotly_capture(executor):
    code = """
import plotly.graph_objects as go
fig = go.Figure(data=go.Bar(y=[2, 3, 1]))
"""
    result = await executor.execute(code)
    if not result["success"]:
        print(f"STDOUT: {result['stdout']}")
        print(f"STDERR: {result['stderr']}")
    assert result["success"] is True
    assert result["visualizations"] is not None
    assert len(result["visualizations"]) == 1
    assert result["visualizations"][0]["type"] == "plotly"
    assert "data" in result["visualizations"][0]["content"]

@pytest.mark.asyncio
async def test_no_visualization(executor):
    code = "x = 1"
    result = await executor.execute(code)
    if not result["success"]:
        print(f"STDOUT: {result['stdout']}")
        print(f"STDERR: {result['stderr']}")
    assert result["success"] is True
    assert not result["visualizations"]
