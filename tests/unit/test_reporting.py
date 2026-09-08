import os
import shutil
import pathlib
import pytest
from rexen.reporting import generator
from rexen.reporting.preprocessor import preprocess_results

@pytest.fixture(scope="function")
def temp_template(tmp_path):
    template_path = tmp_path / "report_template.j2"
    template_path.write_text("{{ target }} - {{ executive_summary }} - {{ urls|join(',') }} - {{ raw_output }}")
    yield str(template_path)

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
        template_path=temp_template,
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


def test_preprocess_results_calculates_authoritative_counts():
    results = {
        "gospider": {
            "urls": [
                "https://example.com/",
                "https://example.com/",
                "https://external.example.org/reference",
            ]
        },
        "httpx": {
            "results": [
                {"url": "https://example.com/", "status": "200"},
                {"url": "https://example.com/missing", "status": "404"},
                {"url": "https://external.example.org/reference", "status": "200"},
            ]
        },
    }

    preprocessed = preprocess_results(results, target="https://example.com")

    assert preprocessed["counts"] == {
        "subdomains": 0,
        "discovered_urls": 1,
        "out_of_scope_urls": 1,
        "probed_urls": 2,
        "live_urls": 1,
        "failed_urls": 1,
    }
