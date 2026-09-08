from tests.conftest import gap_ocm_version_gate


def test_collect_ocm_validation_errors_for_deprecated_gate():
    analysis = {
        "deprecated_gates": [{"label": "api.openshift.com/gate-ocp"}],
        "baseline_has_gate": True,
        "target_has_gate": True,
        "metadata_errors": [],
    }
    errors = gap_ocm_version_gate.collect_ocm_validation_errors(analysis, "FAIL")
    assert errors == ["Deprecated gate in target: api.openshift.com/gate-ocp"]


def test_collect_ocm_validation_errors_for_missing_target_gate():
    analysis = {
        "deprecated_gates": [],
        "baseline_has_gate": True,
        "target_has_gate": False,
        "metadata_errors": ["invalid metadata"],
    }
    errors = gap_ocm_version_gate.collect_ocm_validation_errors(analysis, "FAIL")
    assert "Baseline gate labels missing from target" in errors
    assert "invalid metadata" in errors


def test_collect_ocm_validation_errors_pass_is_empty():
    analysis = {"deprecated_gates": [{"label": "x"}]}
    assert gap_ocm_version_gate.collect_ocm_validation_errors(analysis, "PASS") == []
