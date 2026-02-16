import pytest
from unittest.mock import MagicMock, patch
from rexen.core.orchestrator import Orchestrator
import time

class DummyTool:
    def __init__(self, name="dummy"):
        self.name = name
        self.is_installed = True
    def run(self, target, args=None, **kwargs):
        return {"success": True, "stdout": f"ran {self.name} on {target}", "urls": [f"http://{target}/a"]}

def test_run_tool_success():
    orch = Orchestrator(max_workers=1)
    tool = DummyTool()
    result = orch.run_tool(tool, "example.com", args=[])
    assert result["success"] is True
    assert "ran dummy on example.com" in result["stdout"]

def test_run_all_parallel():
    orch = Orchestrator(max_workers=2)
    tools = [DummyTool(name=f"tool{i}") for i in range(2)]
    results = orch.run_all(tools, "example.com", args=[])
    assert set(results.keys()) == {"tool0", "tool1"}
    for res in results.values():
        assert res["success"] is True

def test_run_tool_not_installed():
    orch = Orchestrator()
    tool = DummyTool()
    tool.is_installed = False
    # Patch tool.run to simulate not installed
    def fake_run(target, args=None, **kwargs):
        return {"success": False, "error": "not installed"}
    tool.run = fake_run
    result = orch.run_tool(tool, "example.com", args=[])
    assert result["success"] is False
    assert "not installed" in result["error"]

def test_rate_limit():
    orch = Orchestrator()
    orch.last_request_time = time.time()
    start = time.time()
    orch.rate_limit()  # Should sleep if called too soon
    end = time.time()
    # Should not sleep more than 1 second
    assert (end - start) < 1.5
