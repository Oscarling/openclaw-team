from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

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

    def test_smoke_read_reports_missing_credentials_before_http(self) -> None:
        result = trello_readonly_prep.smoke_read_trello(
            list_id="list-123",
            board_id=None,
            limit=1,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("Missing Trello credentials", result["reason"])

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


if __name__ == "__main__":
    unittest.main()
