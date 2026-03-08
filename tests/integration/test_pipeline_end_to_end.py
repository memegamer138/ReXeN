import os
import shutil
import pathlib
import pytest
from unittest.mock import patch

@pytest.fixture(scope="function")
def temp_template():
    gen_dir = pathlib.Path(__file__).parent.parent.parent / "src" / "rexen" / "reporting"
    templates_dir = (gen_dir / "../../templates").resolve()
    templates_dir.mkdir(parents=True, exist_ok=True)
    template_path = templates_dir / "report_template.j2"
    template_path.write_text("{{ target }} - {{ executive_summary }} - {{ urls|join(',') }} - {{ raw_output }}")
    yield str(template_path)
    try:
        template_path.unlink()
    except FileNotFoundError:
        pass

def test_pipeline_end_to_end(tmp_path, temp_template):
    # Patch LLM to always return a fixed string
    with patch('rexen.core.pipeline.render_template_report') as mock_report:
        mock_report.return_value = str(tmp_path / "report.txt")
        # Patch all tool wrappers to return predictable outputs
        with patch('rexen.core.pipeline.GospiderTool') as mock_gospider, \
             patch('rexen.core.pipeline.KatanaTool') as mock_katana, \
             patch('rexen.core.pipeline.HttpxTool') as mock_httpx, \
             patch('rexen.core.pipeline.SubfinderTool') as mock_subfinder, \
             patch('rexen.core.pipeline.DecisionEngine') as mock_decision:
            gospider = mock_gospider.return_value
            katana = mock_katana.return_value
            httpx = mock_httpx.return_value
            subfinder = mock_subfinder.return_value
            gospider.name = "gospider"
            katana.name = "katana"
            httpx.name = "httpx"
            subfinder.name = "subfinder"
            gospider.run.return_value = {"urls": ["http://a.com"]}
            katana.run.return_value = {"urls": ["http://b.com"]}
            httpx.run.return_value = {"results": [{"url": "http://a.com", "status": "200"}]}
            subfinder.run.return_value = {"subdomains": ["a.com"]}
            engine = mock_decision.return_value
            engine.choose_tools.return_value = ["subfinder"]
            engine.next_action.side_effect = [
                ["gospider"],
                ["katana"],
                ["httpx"],
                "report"
            ]
            from rexen.core.pipeline import run_pipeline
            output = run_pipeline(user_input="example.com", target="example.com")
            assert "results" in output
            assert "report_path" in output
            assert output["report_path"].endswith("report.txt")
            # Check that all tools were run
            for tool in ["subfinder", "gospider", "katana", "httpx"]:
                assert tool in output["results"]
