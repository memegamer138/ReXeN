import os
import shutil
import pathlib
import pytest

@pytest.fixture(scope="function")
def temp_template(tmp_path):
    template_path = tmp_path / "report_template.j2"
    template_path.write_text("{{ target }} - {{ executive_summary }} - {{ urls|join(',') }} - {{ raw_output }}")
    yield str(template_path)

from unittest.mock import patch, MagicMock
from rexen.core import pipeline

def test_pipeline_llm_fallback(monkeypatch):
    # Patch tools and decision engine
    class DummyTool:
        def __init__(self, name):
            self.name = name
        def run(self, target, args=None, **kwargs):
            return {"urls": [target]}
    class DummyDecision:
        def choose_tools(self, user_input, available_tools):
            return ["dummy"]
        def next_action(self, results, available_tools, rag_context=None):
            return None  # Simulate LLM failure
    monkeypatch.setattr(pipeline, "GospiderTool", lambda: DummyTool("dummy"))
    monkeypatch.setattr(pipeline, "KatanaTool", lambda: DummyTool("dummy"))
    monkeypatch.setattr(pipeline, "HttpxTool", lambda: DummyTool("dummy"))
    monkeypatch.setattr(pipeline, "SubfinderTool", lambda: DummyTool("dummy"))
    monkeypatch.setattr(pipeline, "DecisionEngine", lambda: DummyDecision())
    monkeypatch.setattr(pipeline, "render_template_report", lambda **kwargs: "report.txt")
    output = pipeline.run_pipeline(user_input="test", target="http://a.com")
    assert "report_path" in output
    assert "results" in output
