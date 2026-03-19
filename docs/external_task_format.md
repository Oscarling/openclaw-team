# External Task Format (Local Inbox Simulation)

This document defines the external JSON format accepted by `inbox/*.json` in Phase 8E.

## Required Fields
- `title` (string, required)
  - non-empty, minimum practical length 3
- `description` (string, required)
  - non-empty, minimum practical length 10

## Optional Fields
- `origin_id` (string, recommended)
  - used as primary idempotency key when provided
- `labels` (array of string, optional)
  - each label must match: `^[a-z0-9][a-z0-9_.:-]{0,31}$`
- `metadata` (object, optional)
  - any object payload from external system
- `source` (object, optional)
  - additional source metadata; adapter will enforce `source.kind=local_inbox`
- `priority` (`low|medium|high`, optional)
- `request_type` (currently only `pdf_to_excel_ocr`)
- `input` (object, optional)
  - `input_dir`
  - `output_xlsx`
  - `ocr` (`auto|on|off`)
  - `dry_run` (boolean)

## Source / Origin Convention
- Adapter injects standardized source:
  - `source.kind = local_inbox`
  - `source.origin_id`
  - `source.inbox_file`
  - `source.received_at`
- If `origin_id` is missing, adapter derives one from inbox filename.

## Example
```json
{
  "origin_id": "EXT-LOCAL-20260319-001",
  "title": "PDF to Excel OCR batch run",
  "description": "Run PDF->Excel conversion for the local sample directory and attach review.",
  "labels": ["pdf", "excel", "ocr", "pilot"],
  "metadata": {
    "owner": "integration-test",
    "ticket": "LOCAL-123"
  },
  "request_type": "pdf_to_excel_ocr",
  "input": {
    "input_dir": "~/Desktop/pdf样本",
    "output_xlsx": "artifacts/outputs/phase8b/pdf_to_excel.xlsx",
    "ocr": "auto",
    "dry_run": false
  }
}
```

## Processing Contract
- External input must go through `adapters/local_inbox_adapter.py`.
- Adapter only normalizes and validates, it does not dispatch workers.
- Manager ingest (`skills/ingest_tasks.py`) creates `preview/*.json` by default.
- External input does not dispatch workers until explicit approval is written to `approvals/<preview_id>.json`.
- Manager execution (`skills/execute_approved_previews.py`) is the only entry that can dispatch approved previews.
