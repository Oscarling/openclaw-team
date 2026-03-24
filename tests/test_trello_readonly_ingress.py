from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from skills import ingest_tasks
from skills import trello_readonly_prep


class FakeResponse:
    def __init__(self, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)

    def json(self) -> object:
        return self._payload


class TrelloReadonlyIngressTests(unittest.TestCase):
    ENV_NAMES = (
        "TRELLO_API_KEY",
        "TRELLO_API_TOKEN",
        "TRELLO_KEY",
        "TRELLO_TOKEN",
        "TRELLO_BOARD_ID",
        "TRELLO_LIST_ID",
    )

    def setUp(self) -> None:
        self._old_env = {name: os.environ.get(name) for name in self.ENV_NAMES}
        for name in self.ENV_NAMES:
            os.environ.pop(name, None)

    def tearDown(self) -> None:
        for name, value in self._old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def _sample_local_inbox_payload(
        self,
        *,
        origin_id: str = "trello:card-regen-123",
        title: str = "Controlled same-origin regeneration sample",
        description_suffix: str = "baseline",
        regeneration_token: str | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "origin_id": origin_id,
            "title": title,
            "description": (
                "Purpose:\n\n"
                "Controlled regeneration-path verification for openclaw-team.\n\n"
                "Expected behavior:\n"
                "- preview only\n"
                "- no execute\n"
                f"- scenario: {description_suffix}\n\n"
                "Traceability:\n"
                "- backlog: BL-20260324-020\n\n"
                "Execution contract: keep this as a governed preview-ingest test."
            ),
            "labels": ["trello", "readonly", "reviewable"],
            "request_type": "pdf_to_excel_ocr",
            "input": {
                "input_dir": "/tmp/pdf-samples",
                "output_xlsx": "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx",
                "ocr": "auto",
                "dry_run": False,
            },
            "metadata": {"source_system": "trello"},
        }
        if regeneration_token is not None:
            payload["regeneration_token"] = regeneration_token
        return payload

    def _activate_temp_ingest_repo(self) -> tuple[Path, tuple[Path, Path, Path, Path, Path, Path]]:
        repo_root = Path(tempfile.mkdtemp(prefix="trello-readonly-ingest-regen-"))
        original_paths = (
            ingest_tasks.REPO_ROOT,
            ingest_tasks.INBOX_DIR,
            ingest_tasks.PROCESSING_DIR,
            ingest_tasks.PROCESSED_DIR,
            ingest_tasks.REJECTED_DIR,
            ingest_tasks.PREVIEW_DIR,
        )
        ingest_tasks.REPO_ROOT = repo_root
        ingest_tasks.INBOX_DIR = repo_root / "inbox"
        ingest_tasks.PROCESSING_DIR = repo_root / "processing"
        ingest_tasks.PROCESSED_DIR = repo_root / "processed"
        ingest_tasks.REJECTED_DIR = repo_root / "rejected"
        ingest_tasks.PREVIEW_DIR = repo_root / "preview"
        ingest_tasks.ensure_dirs()
        return repo_root, original_paths

    def _restore_ingest_repo(self, original_paths: tuple[Path, Path, Path, Path, Path, Path]) -> None:
        (
            ingest_tasks.REPO_ROOT,
            ingest_tasks.INBOX_DIR,
            ingest_tasks.PROCESSING_DIR,
            ingest_tasks.PROCESSED_DIR,
            ingest_tasks.REJECTED_DIR,
            ingest_tasks.PREVIEW_DIR,
        ) = original_paths

    def _write_processing_payload(self, repo_root: Path, filename: str, payload: dict[str, object]) -> Path:
        path = repo_root / "processing" / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_smoke_read_reports_missing_credentials_before_http(self) -> None:
        result = trello_readonly_prep.smoke_read_trello(
            list_id="list-123",
            board_id=None,
            limit=1,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("Missing Trello credentials", result["reason"])

    def test_prep_default_output_path_stays_out_of_processing_queue(self) -> None:
        output_path = trello_readonly_prep.default_mapped_output_path()

        self.assertIn("/artifacts/", output_path.as_posix())
        self.assertNotIn("/processing/", output_path.as_posix())
        self.assertEqual(output_path.name, "trello_readonly_mapped_sample.json")

    def test_parse_args_uses_safe_default_output_path(self) -> None:
        with mock.patch.object(sys, "argv", ["trello_readonly_prep.py"]):
            args = trello_readonly_prep.parse_args()

        self.assertEqual(Path(args.output), trello_readonly_prep.default_mapped_output_path())

    def test_smoke_read_passes_with_injected_http_and_maps_first_card(self) -> None:
        os.environ["TRELLO_API_KEY"] = "key-123"
        os.environ["TRELLO_API_TOKEN"] = "token-456"

        def fake_get(url: str, params: dict[str, object], timeout: int) -> FakeResponse:
            self.assertEqual(url, "https://api.trello.com/1/boards/board-123/cards")
            self.assertEqual(timeout, 20)
            self.assertEqual(params["limit"], 1)
            return FakeResponse(
                200,
                [
                    {
                        "id": "card-123",
                        "idShort": 7,
                        "name": "Sample card",
                        "desc": "Convert this PDF.",
                        "idBoard": "board-123",
                        "idList": "list-456",
                        "dateLastActivity": "2026-03-24T10:00:00.000Z",
                        "labels": [{"name": "Finance"}],
                    }
                ],
            )

        result = trello_readonly_prep.smoke_read_trello(
            list_id=None,
            board_id="board-123",
            limit=1,
            requests_get=fake_get,
        )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["read_count"], 1)
        self.assertEqual(result["mapped_preview"]["origin_id"], "trello:card-123")
        self.assertEqual(result["mapped_preview"]["source"]["mode"], "readonly")

    def test_smoke_read_classifies_forbidden_board_access(self) -> None:
        os.environ["TRELLO_API_KEY"] = "key-123"
        os.environ["TRELLO_API_TOKEN"] = "token-456"

        def fake_get(_url: str, params: dict[str, object], timeout: int) -> FakeResponse:
            self.assertEqual(timeout, 20)
            self.assertEqual(params["limit"], 1)
            return FakeResponse(403, "forbidden")

        result = trello_readonly_prep.smoke_read_trello(
            list_id=None,
            board_id="board-123",
            limit=1,
            requests_get=fake_get,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["error_code"], "token_no_board_access")

    def test_ingest_trello_readonly_writes_inbox_payload(self) -> None:
        os.environ["TRELLO_API_KEY"] = "key-123"
        os.environ["TRELLO_API_TOKEN"] = "token-456"

        repo_root = Path(tempfile.mkdtemp(prefix="trello-readonly-ingest-"))
        original_paths = (
            ingest_tasks.REPO_ROOT,
            ingest_tasks.INBOX_DIR,
            ingest_tasks.PROCESSING_DIR,
            ingest_tasks.PROCESSED_DIR,
            ingest_tasks.REJECTED_DIR,
            ingest_tasks.PREVIEW_DIR,
        )

        def fake_get(url: str, params: dict[str, object], timeout: int) -> FakeResponse:
            self.assertEqual(url, "https://api.trello.com/1/boards/board-123/cards")
            self.assertEqual(timeout, 20)
            self.assertEqual(params["limit"], 1)
            return FakeResponse(
                200,
                [
                    {
                        "id": "card-abc",
                        "idShort": 11,
                        "name": "Weekly PDF batch",
                        "desc": "Please extract the attached PDFs.",
                        "idBoard": "board-123",
                        "idList": "list-456",
                        "dateLastActivity": "2026-03-24T11:00:00.000Z",
                        "labels": [{"name": "Ops"}],
                    }
                ],
            )

        try:
            ingest_tasks.REPO_ROOT = repo_root
            ingest_tasks.INBOX_DIR = repo_root / "inbox"
            ingest_tasks.PROCESSING_DIR = repo_root / "processing"
            ingest_tasks.PROCESSED_DIR = repo_root / "processed"
            ingest_tasks.REJECTED_DIR = repo_root / "rejected"
            ingest_tasks.PREVIEW_DIR = repo_root / "preview"
            ingest_tasks.ensure_dirs()

            result = ingest_tasks.ingest_trello_readonly_once(
                board_id_override="board-123",
                list_id_override=None,
                limit=1,
                requests_get=fake_get,
            )
        finally:
            (
                ingest_tasks.REPO_ROOT,
                ingest_tasks.INBOX_DIR,
                ingest_tasks.PROCESSING_DIR,
                ingest_tasks.PROCESSED_DIR,
                ingest_tasks.REJECTED_DIR,
                ingest_tasks.PREVIEW_DIR,
            ) = original_paths

        self.assertEqual(result["status"], "done")
        self.assertEqual(result["read_count"], 1)
        self.assertEqual(result["inbox_written"], 1)

        written_path = Path(result["inbox_files"][0])
        self.assertTrue(written_path.exists())
        payload = json.loads(written_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["origin_id"], "trello:card-abc")
        self.assertEqual(payload["source"]["provider"], "trello")

    def test_ingest_trello_readonly_surfaces_missing_dependency_clearly(self) -> None:
        os.environ["TRELLO_API_KEY"] = "key-123"
        os.environ["TRELLO_API_TOKEN"] = "token-456"

        def missing_requests(_url: str, params: dict[str, object], timeout: int) -> FakeResponse:
            self.assertEqual(timeout, 20)
            self.assertEqual(params["limit"], 1)
            raise RuntimeError(
                "Missing Python dependency 'requests'. Install it before using Trello read-only HTTP calls."
            )

        with self.assertRaisesRegex(RuntimeError, "Missing Python dependency 'requests'"):
            ingest_tasks.ingest_trello_readonly_once(
                board_id_override="board-123",
                list_id_override=None,
                limit=1,
                requests_get=missing_requests,
            )

    def test_ingest_trello_readonly_surfaces_http_error_preview(self) -> None:
        os.environ["TRELLO_API_KEY"] = "key-123"
        os.environ["TRELLO_API_TOKEN"] = "token-456"

        def fake_get(_url: str, params: dict[str, object], timeout: int) -> FakeResponse:
            self.assertEqual(timeout, 20)
            self.assertEqual(params["limit"], 1)
            return FakeResponse(401, "invalid token")

        with self.assertRaisesRegex(RuntimeError, "HTTP 401"):
            ingest_tasks.ingest_trello_readonly_once(
                board_id_override="board-123",
                list_id_override=None,
                limit=1,
                requests_get=fake_get,
            )

    def test_process_one_blocks_same_origin_duplicate_without_regeneration_token(self) -> None:
        repo_root, original_paths = self._activate_temp_ingest_repo()
        seen_dedupe_keys: set[str] = set()

        try:
            first = ingest_tasks.process_one(
                self._write_processing_payload(
                    repo_root,
                    "baseline.json",
                    self._sample_local_inbox_payload(description_suffix="first-preview"),
                ),
                seen_dedupe_keys,
            )
            second = ingest_tasks.process_one(
                self._write_processing_payload(
                    repo_root,
                    "updated.json",
                    self._sample_local_inbox_payload(description_suffix="updated-content-same-origin"),
                ),
                seen_dedupe_keys,
            )
        finally:
            self._restore_ingest_repo(original_paths)

        self.assertEqual(first["status"], "processed")
        self.assertEqual(second["status"], "rejected")
        self.assertEqual(second["decision"], "duplicate_skipped")
        self.assertIn("origin:trello:card-regen-123", second["decision_reason"])

    def test_process_one_allows_controlled_regeneration_and_blocks_token_reuse(self) -> None:
        repo_root, original_paths = self._activate_temp_ingest_repo()
        seen_dedupe_keys: set[str] = set()
        regeneration_token = "regen-20260324-a"

        try:
            first = ingest_tasks.process_one(
                self._write_processing_payload(
                    repo_root,
                    "baseline.json",
                    self._sample_local_inbox_payload(description_suffix="first-preview"),
                ),
                seen_dedupe_keys,
            )
            regenerated = ingest_tasks.process_one(
                self._write_processing_payload(
                    repo_root,
                    "regenerated.json",
                    self._sample_local_inbox_payload(
                        description_suffix="explicit-regeneration",
                        regeneration_token=regeneration_token,
                    ),
                ),
                seen_dedupe_keys,
            )
            replayed_token = ingest_tasks.process_one(
                self._write_processing_payload(
                    repo_root,
                    "replayed-token.json",
                    self._sample_local_inbox_payload(
                        description_suffix="same-token-should-block",
                        regeneration_token=regeneration_token,
                    ),
                ),
                seen_dedupe_keys,
            )
        finally:
            self._restore_ingest_repo(original_paths)

        self.assertEqual(first["status"], "processed")
        self.assertEqual(regenerated["status"], "processed")
        self.assertNotEqual(first["preview_id"], regenerated["preview_id"])
        self.assertEqual(replayed_token["status"], "rejected")
        self.assertEqual(replayed_token["decision"], "duplicate_skipped")
        self.assertIn(
            "origin_regeneration:trello:card-regen-123:regen-20260324-a",
            replayed_token["decision_reason"],
        )

        regenerated_preview = json.loads(
            Path(regenerated["preview_file"]).read_text(encoding="utf-8")
        )
        regenerated_sidecar = json.loads(
            Path(regenerated["result_sidecar"]).read_text(encoding="utf-8")
        )

        self.assertEqual(regenerated_preview["source"]["regeneration_token"], regeneration_token)
        self.assertEqual(
            regenerated_preview["external_input"]["metadata"]["regeneration_token"],
            regeneration_token,
        )
        self.assertEqual(
            regenerated_preview["dedupe_keys"][0],
            "origin_regeneration:trello:card-regen-123:regen-20260324-a",
        )
        self.assertEqual(regenerated_sidecar["regeneration_token"], regeneration_token)


if __name__ == "__main__":
    unittest.main()
