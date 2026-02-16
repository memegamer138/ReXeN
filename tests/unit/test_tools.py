import pytest
from unittest.mock import patch, MagicMock
from rexen.tools.base import Tool

def test_tool_initialization():
    tool = Tool(name="dummy", command="dummycmd", install_url="dummyurl")
    assert tool.name == "dummy"
    assert tool.command == "dummycmd"
    assert tool.install_url == "dummyurl"

@patch("subprocess.run")
def test_check_installation_success(mock_run):
    mock_run.return_value = MagicMock()
    tool = Tool(name="dummy", command="dummycmd")
    assert tool.is_installed is True

@patch("subprocess.run", side_effect=FileNotFoundError)
def test_check_installation_failure(mock_run):
    tool = Tool(name="dummy", command="dummycmd")
    assert tool.is_installed is False

@patch("subprocess.run")
def test_run_success(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "output"
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    tool = Tool(name="dummy", command="dummycmd")
    tool.is_installed = True
    result = tool.run("target", ["--opt"])
    assert result["success"] is True
    assert result["stdout"] == "output"
    assert result["command"] == "dummycmd --opt target"

def test_run_not_installed():
    tool = Tool(name="dummy", command="dummycmd")
    tool.is_installed = False
    result = tool.run("target", ["--opt"])
    assert result["success"] is False
    assert "not installed" in result["error"]