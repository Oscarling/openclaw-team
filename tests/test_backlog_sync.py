from __future__ import annotations

import importlib.util
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "backlog_sync.py"
SPEC = importlib.util.spec_from_file_location("backlog_sync", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load backlog sync module from {MODULE_PATH}")
backlog_sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backlog_sync)


class BacklogSyncTests(unittest.TestCase):
    def _write_backlog(self, text: str) -> Path:
        tmpdir = Path(tempfile.mkdtemp(prefix="backlog-sync-"))
        path = tmpdir / "PROJECT_BACKLOG.md"
        path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")
        return path

    def test_repository_backlog_passes_sync_check(self) -> None:
        errors, required_items = backlog_sync.collect_sync_issues(REPO_ROOT / "PROJECT_BACKLOG.md")

        self.assertEqual(errors, [])
        self.assertTrue(required_items)

    def test_now_active_item_requires_real_issue(self) -> None:
        path = self._write_backlog(
            """
            # Project Backlog

            ## Backlog Items

            ### BL-20260324-001
            - title: Active now item
            - type: blocker
            - status: active
            - phase: now
            - priority: p1
            - owner: Oscarling
            - depends_on: -
            - start_when: Start now
            - done_when: Finish now
            - source: test
            - link: test
            - issue: -
            - evidence: -
            - last_reviewed_at: 2026-03-24
            - opened_at: 2026-03-24
            """
        )

        errors, required_items = backlog_sync.collect_sync_issues(path)

        self.assertEqual(len(required_items), 1)
        self.assertTrue(any("missing a mirrored GitHub issue" in error for error in errors))

    def test_now_item_cannot_use_deferred_issue(self) -> None:
        path = self._write_backlog(
            """
            # Project Backlog

            ## Backlog Items

            ### BL-20260324-002
            - title: Deferred but now item
            - type: mainline
            - status: planned
            - phase: now
            - priority: p1
            - owner: Oscarling
            - depends_on: -
            - start_when: Start now
            - done_when: Finish now
            - source: test
            - link: test
            - issue: deferred:waiting-for-manual-creation
            - evidence: -
            - last_reviewed_at: 2026-03-24
            - opened_at: 2026-03-24
            """
        )

        errors, _ = backlog_sync.collect_sync_issues(path)

        self.assertTrue(any("cannot use deferred issue mirroring" in error for error in errors))

    def test_next_item_can_remain_unmirrored(self) -> None:
        path = self._write_backlog(
            """
            # Project Backlog

            ## Backlog Items

            ### BL-20260324-003
            - title: Next item
            - type: debt
            - status: planned
            - phase: next
            - priority: p2
            - owner: Oscarling
            - depends_on: -
            - start_when: Start later
            - done_when: Finish later
            - source: test
            - link: test
            - issue: -
            - evidence: -
            - last_reviewed_at: 2026-03-24
            - opened_at: 2026-03-24
            """
        )

        errors, required_items = backlog_sync.collect_sync_issues(path)

        self.assertEqual(errors, [])
        self.assertEqual(required_items, [])


if __name__ == "__main__":
    unittest.main()
