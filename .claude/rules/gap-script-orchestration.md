# Gap Script Orchestration Rules

When a gap analysis script is added, updated, or removed, multiple related files MUST be kept in sync.

## Prerequisites

Read these rules first:
- `.claude/rules/when-to-plan.md` - Determines if change is high-impact
- `.claude/rules/proactive-agent-usage.md` - Defines approval workflow

**This rule defines WHAT needs updating when gap scripts change.**
**Those rules define HOW to get user approval before making changes.**

## Current Baseline (M4 — keep docs/skills in sync with this)

| Global check # | Script | `gap-all.sh` step | Job impact |
|----------------|--------|-------------------|------------|
| 1–2 | `gap-aws-sts.py` | `aws` | FAIL → exit 1 |
| 3–4 | `gap-gcp-wif.py` | `gcp` | FAIL → exit 1 |
| 5 | `gap-ocp-gate-ack.py` | `ocp` | FAIL → exit 1 |
| 6 | `gap-versions-channels.py` | `versions-channels` | FAIL → exit 1 |
| 7 | `gap-ocm-version-gate.py` | `ocm-version-gate` | FAIL → exit 1 |
| 8 | `gap-feature-gates.py` | `feature-gates` | Informational (always last) |
| 9 | `gap-api-resources.py` | `api-resources` | Informational; SKIP if no snapshot |
| 10 | `gap-critical-alerts.py` | `critical-alerts` | Informational; SKIP if no snapshot |
| 11 | `gap-cluster-install.py` | `cluster-install` | Informational; SKIP if no snapshot |
| 12 | `gap-e2e-validation.py` | `e2e-validation` | Informational; report FAIL does not fail job |
| 13 | `gap-upgrade-e2e.py` | `upgrade-e2e` | FAIL → exit 1 |

**Orchestration notes:**
- **13 checks** today; next new check is **#14** (insert before `feature-gates` in `gap-all.sh`).
- `gap-all.sh` sets `GAP_FULL_REPORT=1` by default (per-check JSON + `status-check-<n>.json` + combined HTML/JSON).
- `--steps` values: `aws,gcp,ocp,versions-channels,ocm-version-gate,api-resources,critical-alerts,cluster-install,e2e-validation,upgrade-e2e,feature-gates` (not `ocp-gate`).
- Standalone GA script: `scripts/prod/gap-ga-validation.py` (not in `gap-all.sh` / CI pipeline).
- Unit tests: `make test` (`tests/`).

## Orchestration Instructions

**IMPORTANT**: When you (Claude) detect that gap scripts have been modified (via user message, hook output, or file diff), you MUST:
1. Identify this as a **high-impact change** (per when-to-plan.md)
2. Show an implementation plan listing all affected files
3. Suggest the appropriate subagents (gap-script-orchestrator, docs-reviewer, etc.)
4. **Wait for user approval** before spawning any subagents

### Detection Triggers

If you observe ANY of these conditions:
- User mentions adding/updating/removing a gap script
- Hook output shows gap script changes
- User asks about orchestrating changes
- File diff shows `scripts/gap-*.py` changes

### Required Actions

You MUST:

1. **Show implementation plan** with all affected files (see Change Dependencies Matrix below)

2. **Suggest gap-script-orchestrator subagent:**
   ```
   The gap-script-orchestrator subagent can handle orchestrating all related
   changes: templates, gap-all.sh, generate-combined-report.py, skills, and
   documentation.

   Would you like me to invoke it?
   ```

3. **After user approves, spawn gap-script-orchestrator:**
   - Wait for orchestrator to complete
   - Optionally spawn reviewers in parallel (docs-reviewer, skills-reviewer, claude-md-updater)
   - Provide summary of all changes made

### Correct Workflow Example

When user says: "I just added scripts/gap-network.py"

✅ **CORRECT Response:**
```
## Implementation Plan

This is a high-impact change affecting multiple areas.

### Files to Create:
1. scripts/gap-network.py (validation logic)
2. scripts/templates/network.html.j2
3. skills/network-gap/SKILL.md

### Files to Update:
1. scripts/gap-all.sh (add execution step before feature gates)
2. scripts/generate-combined-report.py (add to aggregation)
3. docs/validation-checks.md (add check #14 — next after current 13)
4. README.md (update validation checks table)
5. CLAUDE.md (update validation table)

### Subagents That Could Help:
- gap-script-orchestrator: Can scaffold all files and updates
- docs-reviewer: Can update documentation
- skills-reviewer: Can update skills

Approve this plan? Would you like me to invoke gap-script-orchestrator?
```

**After user says "yes" or "proceed":**
```
[Spawns gap-script-orchestrator agent]
[Waits for completion]
[Spawns docs-reviewer, skills-reviewer, claude-md-updater in parallel if needed]
[Provides comprehensive summary]
```

❌ **INCORRECT Response (violates when-to-plan.md):**
```
I've detected a new gap script. Let me orchestrate all the related changes.

[Immediately spawns gap-script-orchestrator without asking]
```

## Change Dependencies Matrix

| Change Type | Affected Files | Action Required |
|-------------|---------------|-----------------|
| **New gap script** | `scripts/gap-{name}.py` | Create with standard imports, validation logic, report generation |
| | `scripts/templates/{name}.html.j2` | Create HTML template |
| | `scripts/gap-all.sh` | Add execution step (before feature gates) |
| | `scripts/generate-combined-report.py` | Add to report aggregation |
| | `skills/{name}-gap/SKILL.md` | Create Claude skill |
| | `docs/validation-checks.md` | Document new check number |
| | `CLAUDE.md` | Update validation checks table, shared libraries |
| | `README.md` | Update validation checks table |
| **Update gap script** | Same script file | Modify logic |
| | Related template | Update if output structure changes |
| | `docs/validation-checks.md` | Update if check behavior changes |
| | Skill file | Update if workflow changes |
| | `CLAUDE.md` | Update if architectural patterns change |
| **Update shared library** | `scripts/lib/ack_validation.py` | Modify validation logic |
| | **ALL templates** | **ALWAYS check if templates need updating when result structure changes** (e.g., adding `warnings` field, new comparison categories) |
| | `scripts/templates/aws-sts.html.j2` | Update if validation_details structure changes |
| | `scripts/templates/gcp-wif.html.j2` | Update if validation_details structure changes |
| | `scripts/templates/full-gap.html.j2` | Update if validation_details structure changes |
| | `scripts/gap-*.py` files | Update if function signatures change |
| | `scripts/lib/reporters.py` | Update if report data structures change |
| | **ALL templates** | **ALWAYS check if new fields need display** (e.g., continues_default_hypershift for feature gates) |
| | `scripts/templates/feature-gates.html.j2` | Update if comparison structure changes |
| | `scripts/templates/full-gap.html.j2` | Update if comparison structure changes |
| **Remove gap script** | Delete script file | Remove file |
| | Delete template | Remove HTML template |
| | `scripts/gap-all.sh` | Remove execution step |
| | `scripts/generate-combined-report.py` | Remove from aggregation |
| | Delete skill | Remove skill directory |
| | `docs/validation-checks.md` | Remove or mark deprecated |
| | `CLAUDE.md` | Update validation table |
| | `README.md` | Update validation table |

## Critical Ordering Rules

1. **Feature Gates (check #8) ALWAYS runs last** in `gap-all.sh` — even when new scripts are added (new checks run before it)
2. **Check numbers are globally sequential** — next new check is **#14** (after current 1–13)
3. **Informational checks (#8–#12)** must not exit 1 on validation FAIL/SKIP; check #12 uses `status-check` status `WARNING` when e2e tests fail
4. **Standard checks (#1–#7, #13)** exit 1 on validation FAIL
5. **Execution errors** on any script (including informational) exit 1 and fail `gap-all.sh`

## Version 5.x Platform Rules

OpenShift 5.x is **AWS/STS-only** — all GCP/WIF checks must be skipped for 5.x+ versions. Checks #9–#12 use `--topology hcp`, `--topology classic`, and `--topology osd-gcp`; each topology is compared to itself. OSD GCP snapshots/JUnit are skipped when either compared minor is 5.x (5.x has no OSD GCP fresh-install jobs). Check #13 covers HCP, Classic, and OSD GCP (`osd-gcp-upgrade-staging-y-minus-1`); missing JUnit is SKIP. For **5.x targets**, upgrade validation is HCP/Classic only as a product path (OSD GCP → 5.x is not supported; expect SKIP). Treat 5.0 as another OpenShift version with those conditions.

**Detection:** Use `is_version_5x(minor_version)` from `scripts/lib/common.py`. Returns `True` when major version ≥ 5.

**Marketplace per-version skip:** GCP marketplace/WIF skip is applied per-version, not globally. For a 4.22 → 5.0 upgrade, baseline 4.22 still gets GCP marketplace/WIF checked; only the 5.0 side is skipped. Use `skip_gcp_baseline` and `skip_gcp_target` separately — never a single `skip_gcp` flag. Snapshot Checks #9–#12 are different: OSD GCP is skipped for the whole comparison when any compared minor is 5.x. Check #13 includes OSD GCP for **4.x** upgrade paths; for 5.x targets prefer HCP/Classic examples (OSD GCP → 5.x is not a product path; missing JUnit → SKIP).

| Script | Guard Pattern | What's Skipped |
|--------|--------------|----------------|
| `gap-gcp-wif.py` | Early exit block (same pattern as `< 4.16` skip) with dummy PASS/SKIP report | All GCP WIF validation |
| `gap-ocm-version-gate.py` | `skipped_labels` set excludes `api.openshift.com/gate-wif` for `target_minor.startswith("5.")` | WIF gate comparison |
| `gap-versions-channels.py` | `skip_gcp_baseline` / `skip_gcp_target` per-version flags passed to `analyze_marketplace_availability()` | GCP marketplace data for each 5.x version individually |
| `gap-api-resources.py` | HCP vs HCP (hosted + management when present), Classic vs Classic, OSD GCP vs OSD GCP | Missing snapshot; OSD GCP on 5.x |
| `gap-critical-alerts.py` | Same as Check #9 | Missing snapshot; OSD GCP on 5.x |
| `gap-cluster-install.py` | Same as Check #9 | Missing snapshot; OSD GCP on 5.x |
| `gap-e2e-validation.py` | Target-only HCP, Classic, and OSD GCP JUnit | Missing target JUnit; OSD GCP on 5.x |
| `gap-upgrade-e2e.py` | HCP, Classic, and OSD GCP Y-1 → Y upgrade JUnit | Missing upgrade JUnit |
| `gap-ga-validation.py` | `_skip_gcp` flag: GCP handled within combined `check_marketplace_availability()`; excludes `check_gcp_wif_compatibility` from `all_checks` | GCP marketplace (via `_skip_gcp` in combined check) + WIF template checks |

**When adding a new gap script with GCP/WIF checks:** Add a 5.x guard using `is_version_5x()` and document it in this table.

## GA-Aware Channel Rules

All channel-based checks (channel availability, marketplace, version queries) MUST use GA-aware channel sets:

- **GA versions** → `GA_CHANNELS = ['stable', 'eus', 'fast', 'candidate']`
- **Pre-GA versions** → `PRE_GA_CHANNELS = ['candidate']`

**Same order for both baseline and target.** Channel priority is stable first, candidate last.

**Detection:** Use `is_ga_minor_version(minor_version)` from `scripts/lib/openshift_releases.py`.

**Constants** defined in `gap-versions-channels.py`:
```python
GA_CHANNELS = ['stable', 'eus', 'fast', 'candidate']
PRE_GA_CHANNELS = ['candidate']
```

**Usage in `main()`:**
```python
baseline_channels = GA_CHANNELS if baseline_is_ga else PRE_GA_CHANNELS
target_channels = GA_CHANNELS if target_is_ga else PRE_GA_CHANNELS
```

**This applies to:**
- Channel availability checks (which OCM channels contain the version)
- Marketplace checks: ROSA Classic, ROSA HCP, OSD GCP
- Any future checks that query version data by channel

**When adding a new gap script that queries channels or marketplace:** Pass the GA-aware channel sets (`baseline_channels`, `target_channels`) rather than hardcoding channel lists.

## Marketplace Validation Rules

Marketplace checks validate that target versions are available on cloud provider marketplaces. The checks and their severity differ by platform version:

**Categories and scope:**

| Category | Source | 4.x | 5.x |
|----------|--------|-----|-----|
| **ROSA HCP** | `rosa list versions --hosted-cp` | ✓ checked | ✓ checked |
| **ROSA Classic** | OCM API `rosa_enabled` | ✓ checked | ✓ checked |
| **OSD GCP** | OCM API `gcp_marketplace_enabled` | ✓ checked | ⊘ skipped (AWS/STS-only) |

**Severity for GA targets (missing → result):**

| Category | 4.x GA Missing | 5.x GA Missing |
|----------|----------------|----------------|
| **ROSA HCP** | **FAIL** | **FAIL** |
| **ROSA Classic** | **FAIL** | **WARN** |
| **OSD GCP** | **FAIL** | ⊘ skipped |

**Non-GA targets:** All marketplace checks are informational only (no FAIL).

**Per-version skip:** OSD GCP is skipped per-version, not globally. For a 4.22 → 5.0 upgrade, baseline 4.22 gets OSD GCP checked; only target 5.0 is skipped. Use `skip_gcp_baseline` and `skip_gcp_target` (each derived from `is_version_5x()`) rather than a single flag.

**When adding marketplace checks to a new gap script:** Follow this severity matrix. Use per-version `is_version_5x()` checks to determine 4.x vs 5.x behavior for each version independently.

## Script Placement Rules

**`scripts/gap-*.py`** — Standalone analysis scripts with a `main()` function and `if __name__ == '__main__':` entry point. These are invoked directly from the CLI or from `gap-all.sh`.

**`scripts/lib/`** — Shared libraries and helper modules without a `main()` function. These are imported by gap scripts but never run directly.

| Has `main()`? | Placement | Example |
|---------------|-----------|---------|
| Yes | `scripts/gap-{name}.py` | `gap-aws-sts.py`, `gap-ocm-version-gate.py` |
| No | `scripts/lib/{name}.py` | `marketplace.py`, `ack_validation.py`, `reporters.py` |

**If a file in `scripts/` has no `main()` function, it MUST be moved to `scripts/lib/`.** Use standard Python imports (`from module import func`) instead of `importlib.import_module()` for lib modules.

## Version Resolution Rules

All gap scripts MUST use `resolve_gap_versions()` from `scripts/lib/openshift_releases.py` for version resolution. **Never duplicate version resolution logic in individual scripts.**

```python
from openshift_releases import resolve_gap_versions, extract_minor_version

baseline, target = resolve_gap_versions(
    version=args.version, baseline=args.baseline, target=args.target
)
```

**Special version mappings** (e.g., `4.22 → 5.0`, `4.23 → 5.1`) are maintained in two functions in `openshift_releases.py`:
- `get_special_baseline_mapping(target)` — maps target → baseline (e.g., `5.0 → 4.22`)
- `get_special_target_mapping(baseline)` — maps baseline → target (e.g., `4.22 → 5.0`)

**When a new major version transition or non-standard upgrade path is introduced:**
1. Update `get_special_baseline_mapping()` and `get_special_target_mapping()` in `openshift_releases.py`
2. All gap scripts automatically pick up the new mapping via `resolve_gap_versions()`
3. Do NOT add version mapping logic to individual gap scripts

## Standard Gap Script Template Structure

```python
#!/usr/bin/env python3
"""<Description> Gap Analysis - Compare <what> between OpenShift versions."""

import argparse
import sys
from pathlib import Path

# Standard import pattern
sys.path.insert(0, str(Path(__file__).parent / 'lib'))
from common import log_info, log_success, log_error, log_warning, check_command
from openshift_releases import resolve_gap_versions, extract_minor_version
from reporters import generate_html_report, generate_json_report

def main():
    parser = argparse.ArgumentParser(description='<Description>')
    parser.add_argument('--version', help='Single version to analyze (auto-resolves baseline and target)')
    parser.add_argument('--baseline', help='Baseline version (requires --target)')
    parser.add_argument('--target', help='Target version (requires --baseline)')
    parser.add_argument('--report-dir', default='reports', help='Report directory')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    # Version resolution (includes special mappings like 4.22 → 5.0)
    baseline, target = resolve_gap_versions(
        version=args.version, baseline=args.baseline, target=args.target
    )

    # Check dependencies
    check_command('oc')  # or other required tools

    # Perform analysis
    # ...

    # Generate reports
    template_data = {
        'type': '<Analysis Type>',
        'baseline': baseline,
        'target': target,
        'comparison': comparison_result,
        'validation': validation_result
    }

    generate_html_report('<type>', template_data, args.report_dir)
    generate_json_report('<type>', template_data, args.report_dir)

    # Exit code logic
    if validation_failed:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
```

## Template Requirements

**HTML Template (`scripts/templates/{name}.html.j2`):**
- Bootstrap/custom CSS styling
- Color-coded changes (green=added, red=removed, orange=changed)
- Responsive tables
- Include check number in header
- Display validation results with ✓/✗ symbols
- Show added/removed items
- Include GitHub URLs for managed-cluster-config files
- Timestamp and version info

## gap-all.sh Integration Pattern

**Current execution order** (feature gates always last):

1. AWS STS (checks 1–2) — step `aws`
2. GCP WIF (checks 3–4) — step `gcp`
3. OCP Gate Ack (check 5) — step `ocp`
4. Versions & Channels (check 6) — step `versions-channels`
5. OCM Version Gates (check 7) — step `ocm-version-gate`
6. API Resources (check 9) — step `api-resources`
7. Critical Alerts (check 10) — step `critical-alerts`
8. Cluster Install (check 11) — step `cluster-install`
9. Target E2E (check 12) — step `e2e-validation`
10. Upgrade E2E (check 13) — step `upgrade-e2e`
11. **[NEW SCRIPT HERE]** (check #14+) — insert before feature gates
12. Feature Gates (check 8) — step `feature-gates` — **ALWAYS LAST**

When adding a script, update in `gap-all.sh`:
- `STEPS` validation list and default `STEPS_ARRAY`
- `check_num`, `check_display_num`, `check_name`, `check_type` (`standard` vs `informational`)
- `should_run_step` execution block + `read_check_status`
- `usage()` help text

Exit logic uses `check_results` + `check_type` — informational validation FAIL must still exit 0 from the Python script; only execution errors should set `check_results=1`.

## Skill File Structure

Location: `skills/{name}-gap/SKILL.md`

Required frontmatter:
```yaml
---
name: {name}-gap
description: >
  Brief description of what this analyzes
compatibility:
  required_tools:
    - oc
    - python3
    - PyYAML
---
```

Required sections:
- When to Use
- What This Analyzes
- Workflow (3-4 steps)
- Example Interaction
- Output format

## Pre-commit Validation Checklist

Before committing changes involving gap scripts:

- [ ] Script follows standard import pattern
- [ ] HTML template exists
- [ ] gap-all.sh updated (if new/removed script)
- [ ] generate-combined-report.py updated (if new/removed script)
- [ ] Check number assigned and documented
- [ ] Skill file created/updated
- [ ] docs/validation-checks.md updated
- [ ] CLAUDE.md validation table updated
- [ ] README.md validation table updated
- [ ] Feature gates still runs LAST in gap-all.sh
- [ ] `make test` and `make lint` pass
- [ ] `docs/reports.md` updated if status-check or combined-report behavior changes

## Documentation Update Requirements

**docs/validation-checks.md:**
- Add row to check numbering table
- Add "Check Execution by Script" entry
- Add detailed validation section with examples

**CLAUDE.md:**
- Update validation checks table
- Update shared library structure if new lib files added
- Update essential commands if new patterns introduced

**README.md:**
- Update validation checks table (currently **13 checks** → N after adding a script)
- Update examples if relevant

## Anti-Patterns to Avoid

❌ **Don't** add scripts without templates - reports will fail to generate
❌ **Don't** skip check number assignment - creates confusion
❌ **Don't** add scripts after feature gates in gap-all.sh - violates ordering rule
❌ **Don't** forget to update generate-combined-report.py - combined report will be incomplete
❌ **Don't** use different template variable names - breaks consistency
❌ **Don't** exit 1 for informational **validation** results (checks #8–#12) — creates false CI failures
❌ **Don't** use `--steps ocp-gate` — valid step name is `ocp`

## Quick Reference Commands

```bash
# Verify all dependencies for a script are in place
./ci/prow/trigger-job.sh -j <job-name>  # Test in CI

# Check template syntax
python3 -c "from jinja2 import Template; Template(open('scripts/templates/new.html.j2').read())"

# Validate script runs
python3 scripts/gap-new.py --baseline 4.21 --target 4.22

# Check reports generated
ls -lh reports/gap-analysis-new_*
```
