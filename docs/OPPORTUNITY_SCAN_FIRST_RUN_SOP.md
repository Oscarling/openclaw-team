# Opportunity Scan First-Run SOP

## 1. Purpose

Use this SOP to run the first real-model validation for `request_type=opportunity_scan` through the governed pipeline:

`inbox -> ingest -> preview -> approval -> execute`.

This SOP is for **real execution** (`--test-mode off`) and includes pass/fail criteria.

---

## 2. Preconditions

1. Run on a topic branch (not `main`).
2. `opportunity_scan` adapter code and tests are already landed on current branch.
3. Docker worker runtime is available.
4. LLM provider key/base/model are prepared (for example DeepSeek OpenAI-compatible endpoint).
5. `project_delivery_status` remains healthy (`ready_for_replay` expected for current stage).

---

## 3. Input Contract (Minimum)

Place a JSON file in `inbox/` with:

- `title`: non-empty string
- `description`: non-empty string
- `request_type`: `opportunity_scan`
- `input.goal`: non-empty string
- `input.constraints`: string array (optional but recommended)
- `input.items`: non-empty array of objects
- `input.items[].name`: non-empty string
- `origin_id`: strongly recommended for traceability/replay

Example path:

- `inbox/opportunity_scan_real_001.json`

---

## 4. First-Run Commands

## 4.1 Ingest

```bash
python3 skills/ingest_tasks.py --once
```

Expected:

- `processed >= 1`
- `preview_created >= 1`
- `decision=preview_created_pending_approval`

Capture:

- `preview_id`
- `preview_file`

## 4.2 Approve Preview

Create:

- `approvals/<preview_id>.json`

Payload template:

```json
{
  "preview_id": "<preview_id>",
  "approved": true,
  "approved_by": "manual-first-run",
  "approved_at": "2026-03-29T12:00:00Z",
  "note": "Opportunity scan real-model first run"
}
```

## 4.3 Execute (Real Model)

```bash
OPENAI_API_KEY="<provider_key>" \
OPENAI_API_BASE="https://api.deepseek.com/v1" \
OPENAI_MODEL_NAME="deepseek-chat" \
ARGUS_LLM_WIRE_API="chat_completions" \
python3 skills/execute_approved_previews.py --once --preview-id <preview_id> --test-mode off
```

If previous failed attempt marked preview as executed, replay with:

```bash
... python3 skills/execute_approved_previews.py --once --preview-id <preview_id> --test-mode off --allow-replay
```

---

## 5. Success Criteria (Pass Gate)

A run is considered successful when all are true:

1. `execute_approved_previews` reports:
   - `processed=1`
   - `rejected=0`
2. approval sidecar shows:
   - `status=processed`
   - `critic_verdict=pass` or an acceptable governed verdict for your stage
3. analysis and review artifacts both exist:
   - `artifacts/analysis/opportunity_scan_*.md`
   - `artifacts/reviews/opportunity_scan_*_review.md`
4. runtime logs confirm real endpoint execution (not test payload):
   - `workspaces/automation/<AUTO_TASK_ID>/runtime.log`
   - `workspaces/critic/<CRITIC_TASK_ID>/runtime.log`

---

## 6. Quality Checklist (Analysis Artifact)

Check the analysis report for:

1. Item-by-item analysis is complete (no missing candidate).
2. Each item has explicit decision label (`GO` / `WATCH` / `NO-GO`).
3. Ranking is present and consistent with verdict rationale.
4. 7-day actions are concrete (not generic slogans).
5. Risks are explicit and tied to provided evidence/constraints.

---

## 7. Quality Checklist (Critic Artifact)

Check review report for:

1. Clear verdict (`pass` / `needs_revision` / `fail`).
2. Findings point to concrete strengths/issues.
3. Rationale is decision-oriented (not generic restatement).
4. Reviewer validates actionability and prioritization quality.

---

## 8. 3-Sample Regression Mode

After first run passes, validate stability with 3 different samples:

1. Prepare three different `origin_id` + scenario payloads.
2. Repeat Steps 4.1–4.3 for each sample.
3. Build comparison table with:
   - preview id
   - critic verdict
   - GO/WATCH/NO-GO distribution
   - top priority candidate
   - artifact paths
   - runtime duration (automation/critic)

Regression pass recommendation:

- 3/3 runs `processed` with governed verdicts and complete artifacts.

---

## 9. Branch Hygiene

1. Commit code/doc changes only (no accidental secret material).
2. Keep runtime evidence in governed folders; do not force-reset shared history.
3. Push topic branch and open PR for review.

