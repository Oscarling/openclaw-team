from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "artifacts" / "scripts" / "pdf_to_excel_ocr.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("pdf_to_excel_ocr", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PdfToExcelOcrScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = load_script_module()

    def test_process_one_pdf_returns_partial_when_text_exists_but_ocr_fails(self) -> None:
        with mock.patch.object(self.script, "extract_text_pypdf", return_value=("base text", 1)):
            with mock.patch.object(self.script, "extract_text_ocr", side_effect=RuntimeError("ocr boom")):
                result = self.script.process_one_pdf(
                    Path("/tmp/sample.pdf"),
                    ocr_mode="on",
                    ocr_lang="chi_sim+eng",
                    auto_ocr_min_chars=50,
                )

        self.assertEqual(result.status, "partial")
        self.assertIn("OCR failed", result.error)
        self.assertIn("Text was extracted", result.warnings)

    def test_process_one_pdf_success_without_errors(self) -> None:
        with mock.patch.object(self.script, "extract_text_pypdf", return_value=("plain text", 2)):
            result = self.script.process_one_pdf(
                Path("/tmp/sample.pdf"),
                ocr_mode="off",
                ocr_lang="chi_sim+eng",
                auto_ocr_min_chars=50,
            )

        self.assertEqual(result.status, "success")
        self.assertEqual(result.error, "")
        self.assertEqual(result.extract_method, "text")
        self.assertEqual(result.page_count, 2)

    def test_main_report_includes_files_notes_and_next_steps(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pdf-to-excel-ocr-script-") as tmp:
            tmpdir = Path(tmp)
            input_dir = tmpdir / "input"
            input_dir.mkdir(parents=True, exist_ok=True)
            output_xlsx = tmpdir / "output.xlsx"
            sample_pdf = input_dir / "sample.pdf"
            sample_pdf.write_bytes(b"%PDF-1.4\n")

            args = SimpleNamespace(
                input_dir=str(input_dir),
                output_xlsx=str(output_xlsx),
                ocr="auto",
                dry_run=True,
                ocr_lang="chi_sim+eng",
                auto_ocr_min_chars=50,
                report_json="",
            )
            partial_file = self.script.FileResult(
                file_name="sample.pdf",
                file_path=str(sample_pdf),
                status="partial",
                extract_method="text",
                page_count=1,
                text_chars=10,
                text_preview="preview",
                warnings="warn",
                error="",
            )

            stdout = io.StringIO()
            with mock.patch.object(self.script, "parse_args", return_value=args):
                with mock.patch.object(self.script, "discover_pdfs", return_value=[sample_pdf]):
                    with mock.patch.object(self.script, "detect_ocr_runtime_status", return_value=("partial", ["binary tesseract"])):
                        with mock.patch.object(self.script, "process_one_pdf", return_value=partial_file):
                            with contextlib.redirect_stdout(stdout):
                                exit_code = self.script.main()

        self.assertEqual(exit_code, 0)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report["status"], "partial")
        self.assertEqual(len(report["files"]), 1)
        self.assertEqual(report["files"][0]["status"], "partial")
        self.assertTrue(any("OCR runtime status" in note for note in report["notes"]))
        self.assertTrue(any("Inspect per-file partial records" in step for step in report["next_steps"]))


if __name__ == "__main__":
    unittest.main()
