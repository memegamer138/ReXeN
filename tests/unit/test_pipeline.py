import pytest
from unittest.mock import patch, MagicMock

# Patch all tool wrappers and decision engine
@patch('rexen.core.pipeline.GospiderTool')
@patch('rexen.core.pipeline.KatanaTool')
@patch('rexen.core.pipeline.HttpxTool')
@patch('rexen.core.pipeline.SubfinderTool')
@patch('rexen.core.pipeline.DecisionEngine')
def test_run_pipeline_adaptive(mock_decision_engine, mock_subfinder, mock_httpx, mock_katana, mock_gospider):
    from rexen.core.pipeline import run_pipeline
    # Mock tool instances
    gospider = mock_gospider.return_value
    katana = mock_katana.return_value
    httpx = mock_httpx.return_value
    subfinder = mock_subfinder.return_value
    # Set tool names to match pipeline expectations
    gospider.name = "gospider"
    katana.name = "katana"
    httpx.name = "httpx"
    subfinder.name = "subfinder"
    # Mock tool outputs
    gospider.run.return_value = {"success": True, "urls": ["http://a.com"]}
    katana.run.return_value = {"success": True, "urls": ["http://b.com"]}
    httpx.run.return_value = {"success": True, "results": [{"url": "http://a.com", "status": "200"}]}
    subfinder.run.return_value = {"success": True, "subdomains": ["a.com"]}
    # Mock decision engine
    engine = mock_decision_engine.return_value
    # First call: choose_tools returns ["subfinder"]
    engine.choose_tools.return_value = ["subfinder"]
    # next_action: run gospider, then katana, then httpx, then report
    engine.next_action.side_effect = [
        ["gospider"],
        ["katana"],
        ["httpx"],
        "report"
    ]
    user_input = "example.com"
    target = "example.com"
    output = run_pipeline(user_input, target)
    results = output["results"]
    # Check that all tools were run and results aggregated
    assert "subfinder" in results
    assert "gospider" in results
    assert "katana" in results
    assert "httpx" in results
    assert results["subfinder"]["success"]
    assert results["gospider"]["success"]
    assert results["katana"]["success"]
    assert results["httpx"]["success"]
    # Check decision engine was called as expected
    assert engine.choose_tools.called
    assert engine.next_action.call_count == 4
