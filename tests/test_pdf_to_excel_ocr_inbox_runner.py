from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "artifacts" / "scripts" / "pdf_to_excel_ocr_inbox_runner.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("pdf_to_excel_ocr_inbox_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load runner module from {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PdfToExcelOcrInboxRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner_module()

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="pdf-to-excel-ocr-inbox-runner-"))

    def _make_input_dir(self, *, with_pdf: bool) -> Path:
        input_dir = self.tmpdir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        if with_pdf:
            (input_dir / "sample.pdf").write_bytes(b"%PDF-1.4\n% test fixture\n")
        return input_dir

    def _invoke_main(
        self,
        *,
        input_dir: Path,
        extra_args: list[str] | None = None,
        cwd: Path | None = None,
        reviewed_base_script: Path | None = None,
    ) -> tuple[int, dict[str, Any], str]:
        summary_path = self.tmpdir / "summary.json"
        output_path = self.tmpdir / "output.xlsx"
        argv = [
            "pdf_to_excel_ocr_inbox_runner.py",
            "--input-dir",
            str(input_dir),
            "--output-xlsx",
            str(output_path),
            "--summary-json",
            str(summary_path),
        ]
        if extra_args:
            argv.extend(extra_args)

        stdout = io.StringIO()
        previous_cwd = Path.cwd()
        patchers = [mock.patch.object(sys, "argv", argv)]
        if reviewed_base_script is not None:
            patchers.append(mock.patch.object(self.runner, "REVIEWED_BASE_SCRIPT", reviewed_base_script.resolve()))

        with contextlib.ExitStack() as stack:
            for patcher in patchers:
                stack.enter_context(patcher)
            stack.enter_context(contextlib.redirect_stdout(stdout))
            if cwd is not None:
                os.chdir(cwd)
                stack.callback(os.chdir, previous_cwd)
            exit_code = self.runner.main()

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        return exit_code, summary, stdout.getvalue()

    def test_dry_run_returns_partial_without_delegation(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)

        exit_code, summary, _ = self._invoke_main(
            input_dir=input_dir,
            extra_args=["--dry-run", "true"],
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["status"], "partial")
        self.assertFalse(summary["execution"]["delegated"])
        self.assertFalse(summary["output"]["exists"])
        self.assertTrue(any("Dry run requested" in note for note in summary["notes"]))

    def test_zero_pdf_input_short_circuits_to_partial(self) -> None:
        input_dir = self._make_input_dir(with_pdf=False)

        exit_code, summary, _ = self._invoke_main(input_dir=input_dir)

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["status"], "partial")
        self.assertEqual(summary["discovery"]["pdf_count"], 0)
        self.assertFalse(summary["execution"]["delegated"])
        self.assertTrue(any("No PDF files were discovered" in note for note in summary["notes"]))

    def test_relative_base_script_resolves_from_repo_root_not_cwd(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        foreign_cwd = self.tmpdir / "elsewhere"
        foreign_cwd.mkdir(parents=True, exist_ok=True)

        exit_code, summary, _ = self._invoke_main(
            input_dir=input_dir,
            extra_args=["--dry-run", "true"],
            cwd=foreign_cwd,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            summary["parameters"]["preferred_base_script"],
            str((REPO_ROOT / "artifacts" / "scripts" / "pdf_to_excel_ocr.py").resolve()),
        )

    def test_rejects_unreviewed_delegate_script(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        rogue_script = self.tmpdir / "rogue.py"
        rogue_script.write_text("print('rogue')\n", encoding="utf-8")

        exit_code, summary, _ = self._invoke_main(
            input_dir=input_dir,
            extra_args=["--preferred-base-script", str(rogue_script)],
        )

        self.assertNotEqual(exit_code, 0)
        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["execution"]["delegated"])
        self.assertFalse(summary["contract"]["readonly_delegate_verified"])
        self.assertTrue(any("reviewed repository script" in note for note in summary["notes"]))

    def test_propagates_delegate_partial_status_when_output_exists(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        fake_base = self.tmpdir / "fake_pdf_to_excel_ocr.py"
        fake_base.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import argparse
                import json
                from pathlib import Path

                parser = argparse.ArgumentParser()
                parser.add_argument("--input-dir", required=True)
                parser.add_argument("--output-xlsx", required=True)
                parser.add_argument("--ocr", default="auto")
                args = parser.parse_args()

                output = Path(args.output_xlsx)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"fake-xlsx")
                print(json.dumps({"status": "partial", "total_files": 1}))
                """
            ),
            encoding="utf-8",
        )

        exit_code, summary, _ = self._invoke_main(
            input_dir=input_dir,
            extra_args=["--preferred-base-script", str(fake_base)],
            reviewed_base_script=fake_base,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["status"], "partial")
        self.assertTrue(summary["execution"]["delegated"])
        self.assertEqual(summary["execution"]["delegate_report"]["status"], "partial")
        self.assertTrue(summary["output"]["exists"])


if __name__ == "__main__":
    unittest.main()
