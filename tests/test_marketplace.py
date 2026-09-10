from unittest.mock import patch

import marketplace


def _cincinnati_for(channel):
    if channel == "candidate-5.0":
        return {f"5.0.0-rc.{i}" for i in range(3)}
    return set()


def _rosa_versions(channel, major_minor, hosted_cp=False):
    if major_minor != "5.0":
        return set()
    if hosted_cp and channel == "candidate":
        return {"5.0.0-rc.1"}
    return set()


@patch("marketplace.shutil.which", return_value="/usr/bin/rosa")
@patch("marketplace._get_rosa_versions", side_effect=_rosa_versions)
@patch("marketplace._get_cincinnati_versions", side_effect=_cincinnati_for)
def test_aws_marketplace_pass_when_hcp_only(_cincinnati, _rosa, _which):
    """OpenShift 5.x is HCP-first; Classic missing must not FAIL if HCP is enabled."""
    result = marketplace.check_aws_marketplace_enablement("5.0.0-rc.1")
    assert result["status"] == "PASS"
    assert result["gaps"] == []
    assert result["channels"]["candidate"]["rosa_hcp"] is True
    assert result["channels"]["candidate"]["rosa_classic"] is False


@patch("marketplace.shutil.which", return_value="/usr/bin/rosa")
@patch("marketplace._get_rosa_versions", return_value=set())
@patch("marketplace._get_cincinnati_versions", side_effect=_cincinnati_for)
def test_aws_marketplace_fail_when_neither_classic_nor_hcp(_cincinnati, _rosa, _which):
    result = marketplace.check_aws_marketplace_enablement("5.0.0-rc.1")
    assert result["status"] == "FAIL"
    assert "candidate" in result["gaps"]
