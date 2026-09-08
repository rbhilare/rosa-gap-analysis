#!/usr/bin/env python3
"""Report generation utilities for gap analysis using Jinja2 templates."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from prow_artifacts import topology_display_name

# Get templates directory
TEMPLATE_DIR = Path(__file__).parent.parent / 'templates'

# Initialize Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)
jinja_env.filters['topology_label'] = topology_display_name

MAX_STATUS_ERRORS = 20


def collect_errors(*error_lists: Optional[Iterable[Any]]) -> List[str]:
    """Merge error lists into a de-duplicated string list."""
    errors: List[str] = []
    for error_list in error_lists:
        if not error_list:
            continue
        for item in error_list:
            if item is None:
                continue
            text = str(item).strip()
            if text and text not in errors:
                errors.append(text)
    return errors


def format_failure_message(summary: str, errors: Optional[List[str]] = None,
                           max_preview: int = 3) -> str:
    """Build a concise status message with optional error preview."""
    if not errors:
        return summary
    preview = "; ".join(errors[:max_preview])
    if len(errors) > max_preview:
        preview += f"; ... and {len(errors) - max_preview} more"
    return f"{summary}: {preview}"


def build_status_details(message: str, errors: Optional[List[str]] = None,
                         **extra: Any) -> Dict[str, Any]:
    """Build orchestrator status details with optional structured errors."""
    details = dict(extra)
    details['message'] = message
    if errors:
        details['errors'] = errors[:MAX_STATUS_ERRORS]
        if len(errors) > MAX_STATUS_ERRORS:
            details['errors_truncated'] = len(errors) - MAX_STATUS_ERRORS
    return details


def status_exit_code(status: str) -> int:
    """Map report status to process exit code for gap-all.sh."""
    return 0 if status in ('PASS', 'WARNING', 'WARN', 'SKIP') else 1


def generate_json_report(data: Dict[str, Any], output_file: str = None) -> str:
    """Generate JSON report from gap analysis data."""
    report = json.dumps(data, indent=2, sort_keys=True)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)

    return report


def generate_status_report(check_number: int, check_name: str, status: str,
                          details: Dict[str, Any], report_dir: str) -> None:
    """
    Generate a structured status file for gap-all.sh to consume.

    Args:
        check_number: Numeric check identifier (1-13)
        check_name: Human-readable check name
        status: PASS, FAIL, WARNING, WARN, ERROR, SKIP
        details: Dictionary containing check-specific details (message, errors, ...)
        report_dir: Directory to write status file
    """
    status_data = {
        "check_number": check_number,
        "check_name": check_name,
        "status": status,
        "exit_code": status_exit_code(status),
        "details": details
    }

    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    status_file = report_path / f"status-check-{check_number}.json"
    with open(status_file, 'w') as f:
        json.dump(status_data, f, indent=2)


def generate_html_report(data: Dict[str, Any], output_file: str = None) -> str:
    """Generate HTML report from gap analysis data using Jinja2 templates."""
    report_type = data.get('type', 'Gap Analysis')

    # Select template based on report type
    if 'AWS STS' in report_type:
        template = jinja_env.get_template('aws-sts.html.j2')
    elif 'GCP WIF' in report_type:
        template = jinja_env.get_template('gcp-wif.html.j2')
    elif 'Feature Gate' in report_type:
        template = jinja_env.get_template('feature-gates.html.j2')
    elif 'OCP Admin Gate' in report_type or 'Gate Acknowledgment' in report_type:
        template = jinja_env.get_template('ocp-gate-ack.html.j2')
    elif 'Version Channel' in report_type:
        template = jinja_env.get_template('versions-channels.html.j2')
    elif 'GA Readiness' in report_type or 'GA Validation' in report_type:
        template = jinja_env.get_template('ga-validation.html.j2')
    elif "Upgrade Validation from Y-1 to Y" in report_type:
        template = jinja_env.get_template('upgrade-e2e.html.j2')
    elif report_type == "Target E2E Validation and alert monitoring" or "E2E Validation" in report_type:
        template = jinja_env.get_template('e2e-validation.html.j2')
    elif report_type == "Critical Alerts Diff Validation" or "Critical Alerts" in report_type:
        template = jinja_env.get_template('critical-alerts.html.j2')
    elif report_type == "API Resources and CRD Diff Validation" or "API Resources and CRD" in report_type:
        template = jinja_env.get_template('api-resources.html.j2')
    elif report_type == "Cluster Install and Delete Validation" or "Cluster Install" in report_type:
        template = jinja_env.get_template('cluster-install.html.j2')
    elif 'OCM Version Gate' in report_type:
        template = jinja_env.get_template('ocm-version-gate.html.j2')
    elif 'Full Gap Analysis' in report_type or 'Aggregated Gap Analysis' in report_type:
        template = jinja_env.get_template('full-gap.html.j2')
    else:
        # Fallback to a generic template (use aws-sts as base)
        template = jinja_env.get_template('aws-sts.html.j2')

    # Render template
    html = template.render(**data)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(html)

    return html
