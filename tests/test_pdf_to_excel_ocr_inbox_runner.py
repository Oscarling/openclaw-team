from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
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
        output_path = REPO_ROOT / "artifacts" / "outputs" / "unit_tests" / f"{self.tmpdir.name}-output.xlsx"
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

    def test_dry_run_forwards_flag_to_delegate_and_returns_partial(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        fake_base = self.tmpdir / "fake_pdf_to_excel_ocr_dry_run.py"
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
                parser.add_argument("--dry-run", action="store_true")
                parser.add_argument("--report-json", default="")
                args = parser.parse_args()

                payload = {"status": "partial", "dry_run": bool(args.dry_run), "total_files": 1}
                if args.report_json:
                    Path(args.report_json).write_text(json.dumps(payload), encoding="utf-8")
                print(json.dumps(payload))
                """
            ),
            encoding="utf-8",
        )

        exit_code, summary, _ = self._invoke_main(
            input_dir=input_dir,
            extra_args=["--dry-run", "true", "--preferred-base-script", str(fake_base)],
            reviewed_base_script=fake_base,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["status"], "partial")
        self.assertTrue(summary["execution"]["delegated"])
        self.assertIn("--dry-run", summary["execution"]["command"])
        self.assertIsInstance(summary["execution"]["delegate_report"], dict)
        self.assertTrue(summary["execution"]["delegate_report"]["dry_run"])
        self.assertFalse(summary["output"]["exists"])
        self.assertTrue(any("forwarding --dry-run to delegate" in note for note in summary["notes"]))

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
        self.assertEqual(
            summary["provenance"]["delegate_path_resolution"]["strategy"],
            "repo_root_relative",
        )
        self.assertEqual(
            summary["provenance"]["delegate_path_resolution"]["repo_relative_path"],
            "artifacts/scripts/pdf_to_excel_ocr.py",
        )
        self.assertTrue(summary["provenance"]["delegate_path_resolution"]["within_repo_root"])

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
        self.assertTrue(
            any(
                ("reviewed repository script" in note) or ("within repository root" in note)
                for note in summary["notes"]
            )
        )

    def test_rejects_delegate_path_outside_repo_root(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)

        exit_code, summary, _ = self._invoke_main(
            input_dir=input_dir,
            extra_args=["--preferred-base-script", "../../outside-repo/delegate.py"],
        )

        self.assertEqual(exit_code, 5)
        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["execution"]["delegated"])
        self.assertFalse(summary["provenance"]["delegate_path_resolution"]["within_repo_root"])
        self.assertTrue(any("within repository root" in note for note in summary["notes"]))

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
                parser.add_argument("--report-json", default="")
                args = parser.parse_args()

                output = Path(args.output_xlsx)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"fake-xlsx")
                payload = {"status": "partial", "total_files": 1}
                if args.report_json:
                    Path(args.report_json).write_text(json.dumps(payload), encoding="utf-8")
                print(json.dumps(payload))
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
        self.assertEqual(summary["execution"]["delegate_report_source"], "sidecar")

    def test_sidecar_report_is_canonical_when_stdout_diverges(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        fake_base = self.tmpdir / "fake_pdf_to_excel_ocr_sidecar_priority.py"
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
                parser.add_argument("--report-json", default="")
                args = parser.parse_args()

                output = Path(args.output_xlsx)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"fake-xlsx")

                sidecar_payload = {"status": "partial", "total_files": 1}
                if args.report_json:
                    Path(args.report_json).write_text(json.dumps(sidecar_payload), encoding="utf-8")

                stdout_payload = {
                    "status": "success",
                    "total_files": 1,
                    "status_counter": {"failed": 0, "partial": 0},
                    "dry_run": False,
                    "excel_written": True,
                    "output_exists": True,
                    "output_size_bytes": 9,
                }
                print(json.dumps(stdout_payload))
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
        self.assertEqual(summary["execution"]["delegate_report_source"], "sidecar")
        self.assertEqual(summary["execution"]["delegate_report"]["status"], "partial")
        self.assertTrue(
            any("using sidecar as canonical evidence" in note for note in summary["notes"])
        )

    def test_success_requires_strong_delegate_evidence(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        fake_base = self.tmpdir / "fake_pdf_to_excel_ocr_success.py"
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
                parser.add_argument("--report-json", default="")
                args = parser.parse_args()

                output = Path(args.output_xlsx)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"fake-xlsx")
                payload = {"status": "success"}
                if args.report_json:
                    Path(args.report_json).write_text(json.dumps(payload), encoding="utf-8")
                print(json.dumps(payload))
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
        self.assertTrue(summary["output"]["exists"])
        self.assertTrue(any("at least one processed PDF file" in note for note in summary["notes"]))

    def test_rejects_output_path_outside_approved_root(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)

        exit_code, summary, _ = self._invoke_main(
            input_dir=input_dir,
            extra_args=["--output-xlsx", str(self.tmpdir / "outside.xlsx")],
        )

        self.assertEqual(exit_code, 6)
        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["execution"]["delegated"])
        self.assertFalse(summary["provenance"]["output_path_resolution"]["within_approved_output_root"])
        self.assertTrue(any("outside approved output root" in note for note in summary["notes"]))

    def test_surfaces_delegate_extraction_export_phase_distinction(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        fake_base = self.tmpdir / "fake_pdf_to_excel_ocr_export_failed.py"
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
                parser.add_argument("--report-json", default="")
                args = parser.parse_args()

                payload = {
                    "status": "failed",
                    "total_files": 1,
                    "status_counter": {"partial": 1},
                    "dry_run": False,
                    "extraction_status": "partial",
                    "export_status": "failed",
                    "excel_written": False,
                    "output_exists": False,
                    "output_size_bytes": 0,
                    "ocr_runtime_status": "available",
                    "notes": ["Excel write step failed after extraction."],
                    "next_steps": ["Inspect extraction evidence in files/status_counter."],
                    "error": "openpyxl missing",
                }
                if args.report_json:
                    Path(args.report_json).write_text(json.dumps(payload), encoding="utf-8")
                print(json.dumps(payload))
                """
            ),
            encoding="utf-8",
        )

        exit_code, summary, _ = self._invoke_main(
            input_dir=input_dir,
            extra_args=["--preferred-base-script", str(fake_base)],
            reviewed_base_script=fake_base,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["execution"]["delegate_extraction_status"], "partial")
        self.assertEqual(summary["execution"]["delegate_export_status"], "failed")
        self.assertTrue(any("extraction_status=partial" in note for note in summary["notes"]))
        self.assertTrue(any("export_status=failed" in note for note in summary["notes"]))

    def test_surfaces_delegate_error_context_in_wrapper_notes(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        fake_base = self.tmpdir / "fake_pdf_to_excel_ocr_failed_with_error.py"
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
                parser.add_argument("--report-json", default="")
                args = parser.parse_args()

                payload = {
                    "status": "failed",
                    "total_files": 0,
                    "status_counter": {},
                    "dry_run": False,
                    "excel_written": False,
                    "output_exists": False,
                    "output_size_bytes": 0,
                    "ocr_runtime_status": "unknown",
                    "notes": ["Input discovery failed before extraction could start."],
                    "next_steps": ["Verify input directory exists and is readable, then rerun."],
                    "error": "Input directory does not exist: /tmp/missing-input",
                }
                if args.report_json:
                    Path(args.report_json).write_text(json.dumps(payload), encoding="utf-8")
                print(json.dumps(payload))
                """
            ),
            encoding="utf-8",
        )

        exit_code, summary, _ = self._invoke_main(
            input_dir=input_dir,
            extra_args=["--preferred-base-script", str(fake_base)],
            reviewed_base_script=fake_base,
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["execution"]["delegate_report_source"], "sidecar")
        self.assertTrue(
            any("Delegate reported error: Input directory does not exist" in note for note in summary["notes"])
        )

    def test_ocr_runtime_blocked_keeps_wrapper_partial_even_with_success_attestation(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        fake_base = self.tmpdir / "fake_pdf_to_excel_ocr_ocr_blocked.py"
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
                parser.add_argument("--report-json", default="")
                args = parser.parse_args()

                output = Path(args.output_xlsx)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"fake-xlsx")
                payload = {
                    "status": "success",
                    "total_files": 1,
                    "status_counter": {"failed": 0, "partial": 0},
                    "dry_run": False,
                    "excel_written": True,
                    "output_exists": True,
                    "output_size_bytes": 9,
                    "ocr_runtime_status": "blocked",
                }
                if args.report_json:
                    Path(args.report_json).write_text(json.dumps(payload), encoding="utf-8")
                print(json.dumps(payload))
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
        self.assertTrue(
            any("ocr_runtime_status=blocked" in note for note in summary["notes"])
        )

    def test_timeout_returns_failed_with_explicit_note(self) -> None:
        input_dir = self._make_input_dir(with_pdf=True)
        fake_base = self.tmpdir / "fake_pdf_to_excel_ocr_timeout.py"
        fake_base.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

        with mock.patch.object(
            self.runner.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(cmd=["python3", str(fake_base)], timeout=7),
        ):
            exit_code, summary, _ = self._invoke_main(
                input_dir=input_dir,
                extra_args=["--preferred-base-script", str(fake_base), "--delegate-timeout-seconds", "7"],
                reviewed_base_script=fake_base,
            )

        self.assertEqual(exit_code, 124)
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["execution"]["timeout_seconds"], 7)
        self.assertTrue(any("timed out after 7 seconds" in note for note in summary["notes"]))

    def test_default_description_preserves_traceability_context(self) -> None:
        self.assertIn("Traceability:", self.runner.DEFAULT_DESCRIPTION)
        self.assertIn("BL-20260324-014", self.runner.DEFAULT_DESCRIPTION)
        self.assertNotIn("...", self.runner.DEFAULT_DESCRIPTION)

    def test_emits_provenance_and_readonly_attestation(self) -> None:
        input_dir = self._make_input_dir(with_pdf=False)

        exit_code, summary, _ = self._invoke_main(input_dir=input_dir)

        self.assertEqual(exit_code, 0)
        self.assertIn("run_id", summary)
        self.assertEqual(summary["readonly_attestation"]["mode"], "local_filesystem_delegate_only")
        self.assertEqual(summary["readonly_attestation"]["readonly_scope"], "no_external_writeback")
        self.assertFalse(summary["readonly_attestation"]["network_calls_performed"])
        self.assertFalse(summary["readonly_attestation"]["trello_write_performed"])
        self.assertTrue(summary["readonly_attestation"]["local_filesystem_writes_allowed"])
        self.assertTrue(summary["readonly_attestation"]["readonly_label_present"])
        self.assertIn("delegate_path_resolution", summary["provenance"])
        self.assertIn("input_dir_resolution", summary["provenance"])


if __name__ == "__main__":
    unittest.main()
