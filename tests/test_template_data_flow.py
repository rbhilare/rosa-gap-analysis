"""Ensure JSON report fields render in HTML templates (no partials)."""

import pytest

from reporters import generate_html_report


@pytest.fixture
def render_html():
    return generate_html_report


def test_aws_sts_validation_errors_in_html(render_html):
    data = {
        "type": "AWS STS Policy Gap Analysis",
        "baseline": "4.21.0",
        "target": "4.22.0",
        "timestamp": "2026-01-01T00:00:00",
        "validation_result": "FAIL",
        "validation_checked": True,
        "validation_details": {
            "check_1_resources": {
                "status": "FAIL",
                "errors": ["Missing file operator_iam_role_policy.json"],
                "file_count": 0,
                "warnings_structured": [],
            },
            "check_2_admin_ack": {
                "status": "PASS",
                "errors": [],
                "expected_baseline": "4.21",
            },
        },
        "aws_marketplace": {"status": "PASS", "message": "ROSA Classic available", "channels": {}},
        "comparison": {"actions": {"target_only": [], "baseline_only": []}, "file_changes": []},
        "summary": {"added": 0, "removed": 0, "total_changes": 0},
    }
    html = render_html(data)
    assert "Missing file operator_iam_role_policy.json" in html
    assert "CHECK #1: Resources Validation - FAILED" in html


def test_versions_channels_validation_errors_in_html(render_html):
    data = {
        "type": "Version Channel Gap Analysis",
        "baseline": "4.21.15",
        "target": "4.22.0",
        "baseline_minor": "4.21",
        "target_minor": "4.22",
        "is_z_stream": False,
        "timestamp": "2026-01-01T00:00:00",
        "validation_result": "FAIL",
        "validation_errors": ["Target 4.22 not in any channel"],
        "channel_availability": {
            "baseline_in_stable": True,
            "baseline_version_channels": ["stable"],
            "target_version_channels": [],
            "target_highest_channel": None,
            "baseline": {"minor": "4.21", "version": "4.21.15", "channels": {}},
            "target": {"minor": "4.22", "version": "4.22.0", "channels": {}},
        },
        "marketplace": {
            "available": False,
            "hcp": {
                "baseline": {"hcp_enabled": False, "channels": []},
                "target": {"hcp_enabled": False, "channels": []},
            },
            "gcp": {
                "baseline": {"skipped": False, "gcp_marketplace_enabled": None, "channel_group": None},
                "target": {"skipped": False, "gcp_marketplace_enabled": None, "channel_group": None},
            },
            "aws": {"target_minor_versions": []},
        },
        "summary": {
            "baseline_in_stable": True,
            "target_highest_channel": None,
            "baseline_channels": ["stable"],
            "target_channels": [],
            "target_is_ga": False,
            "marketplace_available": False,
            "api_errors": ["OCM API timeout for fast channel"],
            "gcp_skipped": False,
        },
    }
    html = render_html(data)
    assert "Target 4.22 not in any channel" in html
    assert "OCM API timeout for fast channel" in html


def test_ocm_version_gate_change_lists_in_html(render_html):
    data = {
        "type": "OCM Version Gate Gap Analysis",
        "baseline": "4.21.0",
        "target": "4.22.0",
        "baseline_minor": "4.21",
        "target_minor": "4.22",
        "validation_result": "FAIL",
        "is_mock_data": False,
        "gates_count": {"baseline": 1, "target": 1},
        "baseline_gates": [],
        "target_gates": [],
        "comparison": {
            "common_gates_count": 0,
            "new_gates_count": 1,
            "deprecated_gates_count": 1,
            "common_gates": [],
            "new_gates": [{"label": "api.openshift.com/new-gate", "description": "New gate"}],
            "deprecated_gates": [{"label": "api.openshift.com/old-gate", "description": "Old gate"}],
        },
        "skipped_labels": ["api.openshift.com/wif"],
        "configuration_validation": {"valid": False, "errors": ["Gate metadata mismatch"]},
    }
    html = render_html(data)
    assert "api.openshift.com/new-gate" in html
    assert "api.openshift.com/old-gate" in html
