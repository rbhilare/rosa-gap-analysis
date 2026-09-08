import json
from pathlib import Path

from reporters import (
    build_status_details,
    collect_errors,
    format_failure_message,
    generate_status_report,
    status_exit_code,
)


def test_collect_errors_deduplicates():
    errors = collect_errors(["a", "b"], ["b", "c"], None)
    assert errors == ["a", "b", "c"]


def test_format_failure_message_includes_preview():
    message = format_failure_message(
        "2 validation failure(s)",
        ["first", "second", "third", "fourth"],
        max_preview=2,
    )
    assert message.startswith("2 validation failure(s):")
    assert "first" in message
    assert "fourth" not in message
    assert "2 more" in message


def test_build_status_details_truncates_errors():
    errors = [f"error-{i}" for i in range(25)]
    details = build_status_details("failed", errors)
    assert len(details["errors"]) == 20
    assert details["errors_truncated"] == 5


def test_status_exit_code_mapping():
    assert status_exit_code("PASS") == 0
    assert status_exit_code("WARNING") == 0
    assert status_exit_code("WARN") == 0
    assert status_exit_code("SKIP") == 0
    assert status_exit_code("FAIL") == 1
    assert status_exit_code("ERROR") == 1


def test_generate_status_report_writes_expected_schema(tmp_path):
    generate_status_report(
        check_number=7,
        check_name="OCM Version Gates",
        status="FAIL",
        details=build_status_details(
            "1 validation failure(s): missing gate",
            ["missing gate"],
            gates_count=1,
        ),
        report_dir=str(tmp_path),
    )

    status_file = tmp_path / "status-check-7.json"
    assert status_file.exists()
    data = json.loads(status_file.read_text())
    assert data["check_number"] == 7
    assert data["status"] == "FAIL"
    assert data["exit_code"] == 1
    assert data["details"]["errors"] == ["missing gate"]
