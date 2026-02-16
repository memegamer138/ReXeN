import pytest
from rexen.tools.discovery.wayback import WaybackTool
from unittest.mock import patch, MagicMock

def test_parse_output_valid():
    tool = WaybackTool()
    output = """
http://a.com/page1
https://b.com/page2
not_a_url
ftp://c.com/file
"""
    urls = tool.parse_output(output)
    assert urls == ["http://a.com/page1", "https://b.com/page2", "ftp://c.com/file"]

def test_parse_output_empty():
    tool = WaybackTool()
    output = "\n\n"
    urls = tool.parse_output(output)
    assert urls == []

@patch("rexen.tools.base.Tool.run")
def test_run_success(mock_base_run):
    mock_base_run.return_value = {"success": True, "stdout": "http://a.com\nhttps://b.com", "stderr": ""}
    tool = WaybackTool()
    result = tool.run("example.com", [])
    assert result["success"] is True
    assert result["urls"] == ["http://a.com", "https://b.com"]
    assert result["url_count"] == 2
