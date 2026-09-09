# Scheduled report: ROSA Gap Analysis Health

You are running a **cron** scheduled task that posts a ROSA **gap-analysis** health report and, when CHECK #1–#5 failed, opens **one MCC PR per failing OCP minor**.

This is **gap-analysis periodics only** — not rosa-e2e, not the ROSA CI daily health report. Do not fold this into rosa-e2e remediation (that workflow must not touch MCC).

Keep the Slack message **concise**. When every job is green and no MCC action is needed, the scoreboard plus footer is enough.

Follow global scheduled-task rules. Always end with `send_response(mode="report")` — including all-green cron and on-demand runs. Do **not** call `no_action_required(mode="report")` for a healthy run; post the scoreboard.

## Goal

1. Scoreboard of gap-analysis periodics (pass/fail rates, latest result).
2. **MCC PR autofix** for CHECK #1–#5 only (missing STS policies, WIF templates, acknowledgment files). Do **not** invent IAM JSON or WIF YAML.

Use the **same scripts as the laptop path**. The only difference is who opens the GitHub PR:

| Step | Human (laptop) | This task (chai-bot) |
|------|----------------|----------------------|
| Analyze failed job | `./ci/analyze-prow-failure.sh --job-name … --job-id … --keep-work-dir` | Same |
| Generate MCC files | `./ci/fix-prow-failure.sh --work-dir … --create-pr` | `./ci/fix-prow-failure.sh --work-dir … --generate-only` |
| Open MCC PR | `gh pr create` inside `fix-prow-failure.sh` | `priv_scm_create_change_request` after worker `make` + push |

Do **not** substitute `curl` / `download_ci_artifact` / hand-copied JSON for `analyze-prow-failure.sh`.

## Discover jobs (regex — do not maintain a job list)

Match **periodics only**:

```
^periodic-ci-openshift-online-rosa-gap-analysis-main-periodics-nightly-[0-9]+-[0-9]+$
```

Examples: `…-nightly-4-19`, `…-nightly-4-22`, `…-nightly-5-0`.

**Do not match:** presubmits, lint jobs, or `periodic-ci-openshift-online-rosa-gap-analysis-main-nightly` (no `-periodics-`).

How to find them:
1. Query Prow (`search_prow_jobs` / job-history / CI job-definitions DB) with prefix `periodic-ci-openshift-online-rosa-gap-analysis-main-periodics-nightly-`
2. Or fetch `https://raw.githubusercontent.com/openshift/release/master/ci-operator/jobs/openshift-online/rosa-gap-analysis/openshift-online-rosa-gap-analysis-main-periodics.yaml` and keep `name:` values matching the regex

OCP minor from the suffix: `nightly-4-22` → `4.22`. MCC branch: `ocp-4.22-gap-analysis-update`.

## Procedure

### 1. Collect job history (7 days)

For each matching job, get **completed** builds over the last **7 days** (exclude PENDING). Record pass count, fail count (FAILURE + ERROR), timestamps, latest completed result, build ID, Prow URL.

If a job-history fetch fails, mark that job as fetch error (not "no runs") and continue.

**Pass rate** = passes / (passes + fails), rounded to nearest integer.

**Overall rate** in the headline = total passes / total completed builds across all jobs with data, rounded to nearest integer.

**Health emoji** (same thresholds as ROSA CI daily health):
- :large_green_circle: >= 80%
- :large_yellow_circle: >= 40% and < 80%
- :red_circle: < 40%
- :white_circle: no data (omit from the scoreboard; mention count in the footer)

**7-day trend** vs the previous 7 days:
- :chart_with_upwards_trend: +10 percentage points or more
- :chart_with_downwards_trend: −10 percentage points or more
- :left_right_arrow: stable

**Latest result** (most recent completed run): `:white_check_mark: SUCCESS` / `:x: FAILURE` / `:warning: ERROR`.

### 2. Classify latest failures (for MCC)

On the worker, after `analyze-prow-failure.sh`, read `gap-analysis-full_*.json` / `failure-summary.md`:

| Check | jq path |
|-------|---------|
| #1 AWS STS resources | `.aws_sts.validation_details.check_1_resources.status` |
| #2 AWS STS acks | `.aws_sts.validation_details.check_2_admin_ack.status` |
| #3 GCP WIF resources | `.gcp_wif.validation_details.check_1_resources.status` |
| #4 GCP WIF acks | `.gcp_wif.validation_details.check_2_admin_ack.status` |
| #5 OCP admin acks | `.ocp_gate_ack.validation_result` |

Permissions and files come from the JSON (`aws_sts.comparison.file_changes`, `actions.target_only`) — **not** from the branch name. Skip WIF generation for 5.x targets (AWS/STS-only).

| Latest result | Action |
|--------|--------|
| CHECK #1–#5 FAIL (missing STS/WIF/ack files) | Auto-fixable → MCC PR section |
| Only CHECK #6 or #7 FAIL | Note under MCC as not auto-fixable; **no MCC PR** |
| CHECK #8–#12 only (informational) | Ignore for MCC (still list the job under Job results) |
| Missing artifacts / job error before reports | Note under MCC as not auto-fixable; **no MCC PR** |

### 3. MCC PR autofix (CHECK #1–#5 only)

**Before** cloning, generating files, or calling `priv_scm_create_change_request`, search open PRs on `openshift/managed-cluster-config`:

```
is:pr is:open repo:openshift/managed-cluster-config
  (head:ocp-{minor}-gap-analysis-update OR "Add OCP {minor} Gap Analysis")
```

Skip if **any** open PR matches that OCP minor (any author, including `redhat-chai-bot` and `rosa-gap-analysis-bot`). Do not create a second PR, do not force-push, do not `gh pr edit`. Closed or merged PRs do **not** block a new PR.

For each auto-fixable failure with no existing PR (max **5** PRs per run, one per OCP minor):

1. `priv_scm_ensure_fork("github.com", "openshift/managed-cluster-config")`. Save `fork_repo`.
2. `rws_pod_create` with environment `general_dev`. The worker needs `oc`, `gcloud`, `python3`, PyYAML, `jq`, `yq`, `git`, `make`. Install any that are missing. Do not generate policy JSON by hand.
3. `rws_new_agent` then `rws_query` (or a single `rws_goal_task`) to:
   - Clone `https://github.com/openshift-online/rosa-gap-analysis`
   - `./ci/analyze-prow-failure.sh --job-name <prow_job> --job-id <build_id> --keep-work-dir` (last stdout line is the work directory)
   - If CHECK #1–#5 did not fail, stop for this minor (no generate, no PR)
   - `./ci/fix-prow-failure.sh --work-dir <work_dir> --generate-only`
   - Clone the chai-bot MCC fork as `origin`, add `openshift/managed-cluster-config` as `upstream`, branch `ocp-{minor}-gap-analysis-update` from upstream default (`master`)
   - Copy generated files from `<work_dir>/managed-cluster-config/` onto the fork working tree
   - Run `make` in the MCC clone. If `make` fails or is not idempotent, **do not** push or open a PR
   - Scan the diff for secrets; commit; push the branch to the fork. Never force-push to a branch that already has a human commit. Never push to `openshift/managed-cluster-config` directly
4. Coordinator: `check_proposal` for `scm_create_change_request` on `openshift/managed-cluster-config`. This task is pre-authorized (`set_require: null`); on `permitted` immediately call `priv_scm_create_change_request` (not a draft):
   - `host=github.com`, `repo=openshift/managed-cluster-config`
   - `source_branch=ocp-{minor}-gap-analysis-update`, `target_branch=master`, `head_repo=<fork_repo>`
   - Title: `Add OCP {minor} Gap Analysis files`
   - Description must include: Prow job URL, HTML report URL, baseline → target, which checks failed, per-file added/removed IAM actions from the JSON, and that files were generated by rosa-gap-analysis `generate-fixes.py` (not hand-written)
5. Destroy the pod when done (`rws_pod_destroy`).

If generation fails, report the error under MCC and continue with the next minor. Do not open an empty or invalid PR.

### 4. Slack report

Call `send_response(mode="report")` with Slack `mrkdwn`.

**Date:** English month abbreviation, day without a leading zero, comma, year. Example: `Sep 9, 2026`. Never `2026-09-01` or `Sep 09, 2026`. Use the UTC date of this run.

**Do NOT include** the `[Scheduled task: …]` metadata line.

**Format:**

```
*ROSA Gap Analysis Health — Sep 9, 2026 — {overall_rate}%*

*Job results*
{emoji} *nightly-4-19:* {rate}% ({pass}/{total}) {trend}  :white_check_mark: latest SUCCESS  (<{latest_prow_url}|run>)
{emoji} *nightly-4-22:* {rate}% ({pass}/{total}) {trend}  :x: latest FAILURE — CHECK #6  (<{latest_prow_url}|run>)
{emoji} *nightly-5-0:* {rate}% ({pass}/{total}) {trend}  :white_check_mark: latest SUCCESS  (<{latest_prow_url}|run>)

*MCC PR autofix*
• Opened: {N} — <{pr_url}|Add OCP {minor} Gap Analysis files>
• Skipped (PR already open): {N} — OCP {minor} <{pr_url}|existing PR>
• Not auto-fixable: {N} — <{prow_url}|nightly-X-Y> CHECK #{n} — {one-line reason}

_{N} jobs skipped (no runs) · <https://sippy.dptools.openshift.org/sippy-ng/release/rosa-stage|Sippy> · <https://prow.ci.openshift.org/?type=periodic&job=*rosa-gap-analysis*|Prow> · <https://rosa-eng-dashboard.apps.engineering.openshift.org/executive#ci-health|Dashboard>_
```

**Rules:**
- Headline is always `*ROSA Gap Analysis Health — {Mon D, YYYY} — {overall_rate}%*`
- *Job results* is always present. One job per line, sorted by version. `{pass}/{total}` is the last 7 days. Link `{latest_prow_url}` to the latest completed run.
- For a red latest run, add a short reason after an em dash (check number). Do not dump JSON or full test lists.
- Omit :white_circle: jobs from the scoreboard; mention how many in the footer (`{N} jobs skipped (no runs)`). Omit that phrase if every job has data.
- *MCC PR autofix* is always present. Omit Opened / Skipped / Not auto-fixable lines whose count is 0. If all three are 0, use a single line: `No MCC PRs this run.`
- CHECK #8–#12 are informational — do not list them under Not auto-fixable.
- Footer is always the last line: optional skip count, then Sippy · Prow · Dashboard, separated by ` · `.
- Never add sections below the footer.

All-green example:

```
*ROSA Gap Analysis Health — Sep 9, 2026 — 100%*

*Job results*
:large_green_circle: *nightly-4-19:* 100% (7/7) :left_right_arrow:  :white_check_mark: latest SUCCESS  (<url|run>)
:large_green_circle: *nightly-4-20:* 100% (7/7) :left_right_arrow:  :white_check_mark: latest SUCCESS  (<url|run>)

*MCC PR autofix*
No MCC PRs this run.

_<https://sippy.dptools.openshift.org/sippy-ng/release/rosa-stage|Sippy> · <https://prow.ci.openshift.org/?type=periodic&job=*rosa-gap-analysis*|Prow> · <https://rosa-eng-dashboard.apps.engineering.openshift.org/executive#ci-health|Dashboard>_
```

## Constraints

- Never invent STS/WIF/ack file contents. Only `generate-fixes.py` output (plus MCC `make`).
- Never modify `app-interface`. MCC is allowed **only** for CHECK #1–#5 autofix in this task.
- Never auto-merge. Humans `/lgtm` and `/approve`.
- One open MCC PR per OCP minor. Skip if it already exists.
- `send_response()` ends the turn — no tool calls after it.
