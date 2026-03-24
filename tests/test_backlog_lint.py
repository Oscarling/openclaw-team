from __future__ import annotations

import importlib.util
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "backlog_lint.py"
SPEC = importlib.util.spec_from_file_location("backlog_lint", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load backlog lint module from {MODULE_PATH}")
backlog_lint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backlog_lint)


class BacklogLintTests(unittest.TestCase):
    def _write_backlog(self, text: str) -> Path:
        tmpdir = Path(tempfile.mkdtemp(prefix="backlog-lint-"))
        path = tmpdir / "PROJECT_BACKLOG.md"
        path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")
        return path

    def test_repository_backlog_passes_lint(self) -> None:
        errors = backlog_lint.lint_backlog(REPO_ROOT / "PROJECT_BACKLOG.md")
        self.assertEqual(errors, [])

    def test_duplicate_id_and_done_without_evidence_fail(self) -> None:
        path = self._write_backlog(
            """
            # Project Backlog

            ## Backlog Items

            ### BL-20260324-001
            - title: First item
            - type: mainline
            - status: done
            - phase: now
            - priority: p1
            - owner: Oscarling
            - depends_on: -
            - start_when: Start now
            - done_when: Done now
            - source: test
            - link: test
            - issue: -
            - evidence: -
            - last_reviewed_at: 2026-03-24
            - opened_at: 2026-03-24

            ### BL-20260324-001
            - title: Duplicate item
            - type: blocker
            - status: planned
            - phase: now
            - priority: p1
            - owner: Oscarling
            - depends_on: BL-20260324-999
            - start_when: Later
            - done_when: Later
            - source: test
            - link: test
            - issue: not-an-issue-link
            - evidence: -
            - last_reviewed_at: 2026-03-24
            - opened_at: 2026-03-24
            """
        )

        errors = backlog_lint.lint_backlog(path)

        self.assertTrue(any("duplicate backlog id" in error for error in errors))
        self.assertTrue(any("done items must replace evidence" in error for error in errors))
        self.assertTrue(any("depends_on references unknown backlog id" in error for error in errors))
        self.assertTrue(any("issue must be" in error for error in errors))

    def test_future_items_must_use_later_phase(self) -> None:
        path = self._write_backlog(
            """
            # Project Backlog

            ## Backlog Items

            ### BL-20260324-010
            - title: Future item
            - type: future
            - status: planned
            - phase: now
            - priority: p3
            - owner: Oscarling
            - depends_on: -
            - start_when: Someday
            - done_when: Eventually
            - source: test
            - link: test
            - issue: -
            - evidence: -
            - last_reviewed_at: 2026-03-24
            - opened_at: 2026-03-24
            """
        )

        errors = backlog_lint.lint_backlog(path)

        self.assertTrue(any("type=future items must use phase=later" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
