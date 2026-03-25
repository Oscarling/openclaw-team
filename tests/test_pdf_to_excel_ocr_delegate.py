from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
DELEGATE_PATH = REPO_ROOT / "artifacts" / "scripts" / "pdf_to_excel_ocr.py"


def load_delegate_module():
    module_name = "pdf_to_excel_ocr"
    spec = importlib.util.spec_from_file_location(module_name, DELEGATE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load delegate module from {DELEGATE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class PdfToExcelOcrDelegateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.delegate = load_delegate_module()

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="pdf-to-excel-ocr-delegate-"))
        self.input_dir = self.tmpdir / "input"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_xlsx = self.tmpdir / "output.xlsx"
        self.report_json = self.tmpdir / "report.json"
        self.fake_pdf = self.input_dir / "sample.pdf"
        self.fake_pdf.write_bytes(b"%PDF-1.4\n% test fixture\n")

    def _invoke_main(self, extra_args: list[str] | None = None) -> tuple[int, dict[str, object], dict[str, object]]:
        argv = [
            "pdf_to_excel_ocr.py",
            "--input-dir",
            str(self.input_dir),
            "--output-xlsx",
            str(self.output_xlsx),
            "--report-json",
            str(self.report_json),
        ]
        if extra_args:
            argv.extend(extra_args)

        stdout = io.StringIO()
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
            exit_code = self.delegate.main()

        stdout_payload = json.loads(stdout.getvalue())
        sidecar_payload = json.loads(self.report_json.read_text(encoding="utf-8"))
        return exit_code, stdout_payload, sidecar_payload

    def _mock_file_result(self, *, status: str = "success"):
        return self.delegate.FileResult(
            file_name="sample.pdf",
            file_path=str(self.fake_pdf),
            status=status,
            extract_method="text",
            page_count=1,
            text_chars=12,
            text_preview="hello world",
            warnings="",
            error="",
        )

    def test_report_json_is_written_for_dry_run(self) -> None:
        with mock.patch.object(self.delegate, "discover_pdfs", return_value=[self.fake_pdf]), mock.patch.object(
            self.delegate, "process_one_pdf", return_value=self._mock_file_result(status="success")
        ):
            exit_code, stdout_payload, sidecar_payload = self._invoke_main(extra_args=["--dry-run"])

        self.assertEqual(exit_code, 0)
        self.assertTrue(self.report_json.exists())
        self.assertEqual(stdout_payload, sidecar_payload)
        self.assertEqual(sidecar_payload["status"], "success")
        self.assertEqual(sidecar_payload["total_files"], 1)
        self.assertEqual(sidecar_payload["dry_run"], True)

    def test_report_json_is_written_on_write_failure(self) -> None:
        with mock.patch.object(self.delegate, "discover_pdfs", return_value=[self.fake_pdf]), mock.patch.object(
            self.delegate, "process_one_pdf", return_value=self._mock_file_result(status="success")
        ), mock.patch.object(self.delegate, "write_excel", side_effect=RuntimeError("xlsx write failed")):
            exit_code, stdout_payload, sidecar_payload = self._invoke_main()

        self.assertEqual(exit_code, 3)
        self.assertTrue(self.report_json.exists())
        self.assertEqual(stdout_payload, sidecar_payload)
        self.assertEqual(sidecar_payload["status"], "failed")
        self.assertIn("xlsx write failed", str(sidecar_payload.get("error")))


if __name__ == "__main__":
    unittest.main()
