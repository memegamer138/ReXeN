import os
import shutil
import pathlib
import pytest
from rexen.reporting import generator

@pytest.fixture(scope="function")
def temp_template():
    # Find the generator.py directory
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

def test_render_template_report_basic(tmp_path, temp_template):
    preprocessed = {"urls": ["http://a.com"], "findings": ["test finding"]}
    target = "example.com"
    results = {"gospider": {"urls": ["http://a.com"]}}
    output_dir = tmp_path
    def fake_llm(prompt):
        return "LLM output"
    report_path = generator.render_template_report(
        preprocessed=preprocessed,
        target=target,
        results=results,
        output_dir=output_dir,
        template_path=None,  # Use default logic, which now finds the temp template
        llm_generate_fn=fake_llm
    )
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "LLM output" in content
    assert "example.com" in content
    assert "http://a.com" in content

def test_generate_report_fallback(tmp_path):
    results = {"gospider": {"urls": ["http://a.com"]}}
    target = "example.com"
    report_path = generator.generate_report_fallback(results, target, output_dir=tmp_path)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Recon Report for: example.com" in content
    assert "GOSPIDER" in content
    assert "http://a.com" in content
