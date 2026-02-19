import pytest
from unittest.mock import patch, MagicMock
from rexen.tools.crawlers.gospider import GospiderTool
from rexen.tools.crawlers.katana import KatanaTool
from rexen.tools.discovery.httpx import HttpxTool

@patch("subprocess.run")
def test_gospider_run_success(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://example.com\nhttps://example.com/page.js"
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    tool = GospiderTool()
    tool.is_installed = True
    result = tool.run("example.com", [])
    assert result["success"] is True
    assert "https://example.com" in result["urls"]
    assert "https://example.com/page.js" not in result["urls"]  # filtered static

@patch("subprocess.run")
def test_katana_run_success(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://example.com\nhttps://example.com/image.png"
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    tool = KatanaTool()
    tool.is_installed = True
    result = tool.run("example.com", [])
    assert result["success"] is True
    assert "https://example.com" in result["urls"]
    assert "https://example.com/image.png" not in result["urls"]  # filtered static

@patch("subprocess.run")
def test_httpx_run_success(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"url": "https://example.com", "status_code": 200}\n{"url": "https://example.com/page", "status_code": 404}'
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    tool = HttpxTool()
    tool.is_installed = True
    # Patch parse_output to handle JSON lines
    def fake_parse_output(stdout):
        results = []
        for line in stdout.strip().split("\n"):
            if line:
                try:
                    results.append(eval(line))
                except Exception:
                    pass
        return results
    tool.parse_output = fake_parse_output
    result = tool.run(["https://example.com", "https://example.com/page"], [])
    assert result["success"] is True
    assert any(r["status_code"] == 200 for r in result["results"])
    assert any(r["status_code"] == 404 for r in result["results"])