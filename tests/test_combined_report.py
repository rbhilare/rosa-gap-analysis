from tests.conftest import generate_combined_report


def test_load_status_check_file_missing(tmp_path):
    assert generate_combined_report.load_status_check_file(str(tmp_path), 7) is None


def test_get_status_message_from_status_file(tmp_path):
    import json

    status = {
        "check_number": 7,
        "status": "FAIL",
        "details": {
            "message": "gate missing",
            "errors": ["Deprecated gate in target: api.openshift.com/foo"],
        },
    }
    (tmp_path / "status-check-7.json").write_text(json.dumps(status))

    assert generate_combined_report.get_status_message(str(tmp_path), 7, "default") == "gate missing"
    loaded = generate_combined_report.load_status_check_file(str(tmp_path), 7)
    assert loaded["details"]["errors"][0].startswith("Deprecated")


def test_fallback_validation_result_preserves_fail(tmp_path):
    import json

    (tmp_path / "status-check-9.json").write_text(
        json.dumps({"status": "FAIL", "details": {"message": "crashed"}})
    )
    assert generate_combined_report.fallback_validation_result(str(tmp_path), 9, default="SKIP") == "FAIL"


def test_fallback_validation_result_skip_when_missing(tmp_path):
    assert generate_combined_report.fallback_validation_result(str(tmp_path), 9, default="SKIP") == "SKIP"


def test_fallback_validation_result_warning_maps_to_warning(tmp_path):
    import json

    (tmp_path / "status-check-12.json").write_text(
        json.dumps({"status": "WARN", "details": {"message": "e2e failures"}})
    )
    assert generate_combined_report.fallback_validation_result(str(tmp_path), 12, default="SKIP") == "WARNING"
