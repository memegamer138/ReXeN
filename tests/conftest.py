from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def remove_test_reports():
    """Remove only report files created by the current test."""
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    existing_reports = set(reports_dir.iterdir())

    yield

    for report_path in reports_dir.iterdir():
        if report_path not in existing_reports and report_path.is_file():
            report_path.unlink()