from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path
from urllib.error import URLError

from scripts import pin_trello_done_list


class FakeHTTPResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


class PinTrelloDoneListTests(unittest.TestCase):
    def _write_env(self, text: str) -> Path:
        tmpdir = Path(tempfile.mkdtemp(prefix="pin-trello-done-list-"))
        env_file = tmpdir / "trello_env.sh"
        env_file.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
        return env_file

    def test_lookup_writes_done_list_id_and_backup(self) -> None:
        env_file = self._write_env(
            """
            export TRELLO_API_KEY='key-123'
            export TRELLO_API_TOKEN='token-456'
            export TRELLO_BOARD_ID='board-789'
            """
        )

        def fake_urlopen(_request, timeout=20):  # type: ignore[no-untyped-def]
            self.assertEqual(timeout, 20)
            return FakeHTTPResponse(
                [
                    {"id": "list-todo", "name": "待办", "closed": False},
                    {"id": "list-done", "name": "完成", "closed": False},
                ]
            )

        result = pin_trello_done_list.pin_done_list_id(
            env_file,
            board_id_override=None,
            done_list_id_override=None,
            done_list_name_override="完成",
            apply=True,
            urlopen=fake_urlopen,
        )

        updated_text = env_file.read_text(encoding="utf-8")
        self.assertEqual(result["status"], "updated")
        self.assertIn("export TRELLO_DONE_LIST_ID='list-done'\n", updated_text)
        self.assertTrue(Path(result["backup_file"]).exists())
        self.assertNotIn("TRELLO_DONE_LIST_ID", Path(result["backup_file"]).read_text(encoding="utf-8"))

    def test_explicit_done_list_id_skips_lookup(self) -> None:
        env_file = self._write_env(
            """
            export TRELLO_KEY='key-only'
            export TRELLO_TOKEN='token-only'
            export TRELLO_BOARD_ID='board-789'
            """
        )

        def unexpected_urlopen(_request, timeout=20):  # type: ignore[no-untyped-def]
            raise AssertionError("urlopen should not be called when done-list-id is explicit")

        result = pin_trello_done_list.pin_done_list_id(
            env_file,
            board_id_override=None,
            done_list_id_override="manual-done-id",
            done_list_name_override=None,
            apply=True,
            urlopen=unexpected_urlopen,
        )

        self.assertEqual(result["resolution"], "explicit_done_list_id")
        self.assertIn("export TRELLO_DONE_LIST_ID='manual-done-id'\n", env_file.read_text(encoding="utf-8"))

    def test_missing_credentials_raise_clear_error(self) -> None:
        env_file = self._write_env(
            """
            export TRELLO_BOARD_ID='board-789'
            """
        )

        with self.assertRaisesRegex(RuntimeError, "Missing Trello credentials in env file"):
            pin_trello_done_list.pin_done_list_id(
                env_file,
                board_id_override=None,
                done_list_id_override=None,
                done_list_name_override=None,
                apply=False,
            )

    def test_network_error_is_reported(self) -> None:
        env_file = self._write_env(
            """
            export TRELLO_API_KEY='key-123'
            export TRELLO_API_TOKEN='token-456'
            export TRELLO_BOARD_ID='board-789'
            """
        )

        def failing_urlopen(_request, timeout=20):  # type: ignore[no-untyped-def]
            raise URLError("boom")

        with self.assertRaisesRegex(RuntimeError, "Unable to resolve Trello Done list before HTTP response"):
            pin_trello_done_list.pin_done_list_id(
                env_file,
                board_id_override=None,
                done_list_id_override=None,
                done_list_name_override=None,
                apply=False,
                urlopen=failing_urlopen,
            )


if __name__ == "__main__":
    unittest.main()
