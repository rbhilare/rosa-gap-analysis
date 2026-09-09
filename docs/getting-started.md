# Getting Started

Quick guide to installing and running gap analysis.

## Installation

### Prerequisites

```bash
# Required
make setup                   # pip install -r requirements.txt + pre-commit hook
# or: pip install -r requirements.txt

# Download oc CLI
curl -L https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz | tar xz -C /usr/local/bin
```

**Optional** (graceful fallback when absent):

| Tool | Used for |
|------|----------|
| `ocm` + `OCM_TOKEN` | CHECK #6 channels, CHECK #7 version gates, ROSA Classic/OSD GCP marketplace |
| `rosa` | ROSA HCP marketplace (CHECK #6) |
| `gh` | GitHub PR link detection for unexpected managed-cluster-config changes |

Verify installation:

```bash
oc version --client
python3 --version
python3 -c "import yaml, jinja2; print('Dependencies OK')"
make lint    # static checks
make test    # unit tests
```

## Basic Usage

### Auto-Detect Versions (Recommended)

```bash
# Run all 13 checks
./scripts/gap-all.sh

# Individual analyses (examples)
python3 ./scripts/gap-aws-sts.py
python3 ./scripts/gap-gcp-wif.py
python3 ./scripts/gap-ocp-gate-ack.py
python3 ./scripts/gap-versions-channels.py
python3 ./scripts/gap-ocm-version-gate.py
python3 ./scripts/gap-api-resources.py
python3 ./scripts/gap-critical-alerts.py
python3 ./scripts/gap-cluster-install.py
python3 ./scripts/gap-e2e-validation.py
python3 ./scripts/gap-upgrade-e2e.py
python3 ./scripts/gap-feature-gates.py   # always runs last in gap-all.sh
```

**Auto-detection:** Compares latest stable → latest candidate (or use `--version` for single-version resolution).

### Specify Versions

```bash
# Full analysis
./scripts/gap-all.sh --baseline 4.21 --target 4.22
./scripts/gap-all.sh --version 4.22   # RECOMMENDED: auto-resolves baseline and target

# Individual scripts
python3 ./scripts/gap-aws-sts.py --baseline 4.21.6 --target 4.22.0-ec.3
python3 ./scripts/gap-api-resources.py --version 4.22 --topology hcp
python3 ./scripts/gap-upgrade-e2e.py --version 4.22 --topology classic
```

### Environment Variables

```bash
OPENSHIFT_VERSION=4.22 ./scripts/gap-all.sh
BASE_VERSION=4.21 TARGET_VERSION=4.22 ./scripts/gap-all.sh
TARGET_VERSION=NIGHTLY ./scripts/gap-all.sh
REPORT_DIR=/tmp/reports ./scripts/gap-all.sh
OCM_TOKEN=... ./scripts/gap-all.sh   # live OCM API for checks 6–7
```

### Container

```bash
podman build -f ci/Containerfile -t gap-analysis:dev .
podman run --rm gap-analysis:dev gap-all.sh --version 4.22
```

## Viewing Reports

Reports are generated in `./reports/` (or `$REPORT_DIR`):

```bash
firefox reports/gap-analysis-full_*.html
jq '.aws_sts.comparison' reports/gap-analysis-full_*.json
jq . reports/status-check-1.json
```

`gap-all.sh` sets `GAP_FULL_REPORT=1` by default: individual per-check HTML is skipped; you get per-check JSON, `status-check-<n>.json`, and combined `gap-analysis-full_*.{html,json}`. Run a script directly (or `GAP_FULL_REPORT=0 ./scripts/gap-all.sh`) for standalone HTML.

| Format | Extension | Use Case |
|--------|-----------|----------|
| HTML | `.html` | Browser viewing, presentations |
| JSON | `.json` | Programmatic analysis, CI/CD |
| Status | `status-check-<n>.json` | Per-check pass/fail for orchestrator and combined report fallbacks |

See [Report Documentation](reports.md) for details.

## Common Scenarios

### Pre-Upgrade Assessment

```bash
./scripts/gap-all.sh --version 4.22
firefox reports/gap-analysis-full_*.html
```

### CI/CD Integration

```bash
./scripts/gap-all.sh --version 4.22 || exit 1
# Exits 1 when checks 1–7 or 13 fail, or on execution errors
# Checks 8–12 are informational (exit 0); missing Prow/JUnit artifacts → SKIP
```

### Run Subset of Checks

```bash
./scripts/gap-all.sh --version 4.22 --steps aws,gcp
./scripts/gap-all.sh --steps upgrade-e2e
```

### Multiple Version Comparisons

```bash
for target in 4.21 4.22 4.23; do
  ./scripts/gap-all.sh --baseline 4.20 --target $target
done
```

## Understanding Output

### Exit Codes

| Outcome | Exit code |
|---------|-----------|
| Checks 1–7 and 13 pass | `0` |
| Any check 1–7 or 13 fails | `1` |
| Checks 8–12 (informational) | `0` when report shows FAIL/WARN/SKIP |
| Execution error on any check (including 8–12) | `1` |

**Note:** `gap-feature-gates.py` (check 8) is informational and always exits 0 on successful execution. Check 13 fails on failed post-upgrade e2e or unhealthy ClusterOperators.

### Console Output

```
[INFO] OpenShift Gap Analysis Suite
[INFO] Baseline: 4.21.7
[INFO] Target: 4.22.0-ec.4
[INFO] Running AWS STS Policy Gap Analysis...
[INFO] Policy differences detected: 3 added, 1 removed
[SUCCESS] Reports generated: ./reports/
```

## Next Steps

- [Configuration](configuration.md) - CLI args, env vars, version resolution
- [Validation Checks](validation-checks.md) - All 13 checks in detail
- [Development](development.md) - Contributing and testing
