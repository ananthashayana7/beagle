"""
Tests for ProcessExecutor
"""

import pytest
import pandas as pd
import numpy as np
from app.services.process_executor import ProcessExecutor

@pytest.fixture
def executor():
    return ProcessExecutor()

@pytest.mark.asyncio
async def test_basic_execution(executor):
    code = """
x = 10
y = 20
z = x + y
"""
    result = await executor.execute(code)
    assert result["success"] is True
    assert result["result"]["z"] == 30

@pytest.mark.asyncio
async def test_blocked_terms(executor):
    code = "import os; os.system('ls')"
    is_valid, msg = executor.validate_code(code)
    assert is_valid is False
    assert "Blocked term" in msg

@pytest.mark.asyncio
async def test_timeout(executor):
    code = """
import time
time.sleep(2)
"""
    # Set timeout to 1 second
    result = await executor.execute(code, timeout=1)
    assert result["success"] is False
    assert "timed out" in result["error"]

@pytest.mark.asyncio
async def test_dataframe_execution(executor):
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    code = """
result = df['a'].sum()
df['c'] = df['a'] + df['b']
"""
    result = await executor.execute(code, dataframe=df)
    assert result["success"] is True
    assert result["result"]["result"] == 6
    # DataFrame modifications are not returned directly in 'variables' unless we explicitly check
    # But 'df' should be in variables if modified?
    # ProcessExecutor logic says: "if name == 'df' and isinstance(val, pd.DataFrame): pass"
    # So 'df' is included.
    assert "df" in result["result"]
    assert result["result"]["df"]["shape"] == [3, 3]  # Added column 'c'

@pytest.mark.asyncio
async def test_syntax_error(executor):
    code = "x = "
    result = await executor.execute(code)
    assert result["success"] is False
    assert "SyntaxError" in result["stderr"]

@pytest.mark.asyncio
async def test_runtime_error(executor):
    code = "x = 1 / 0"
    result = await executor.execute(code)
    assert result["success"] is False
    assert "ZeroDivisionError" in result["stderr"]
