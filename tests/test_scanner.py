import json
from pathlib import Path
import tempfile
import unittest
from sharecheck.scanner import scan
from sharecheck.report import html_report


class ScannerTests(unittest.TestCase):
    def test_secret_is_detected_but_never_exported(self):
        with tempfile.TemporaryDirectory() as folder:
            token = "ghp_" + "a" * 36
            Path(folder, "config.py").write_text("# config\nTOKEN=" + token, encoding="utf-8")
            result = scan(folder)
            hit = next(f for f in result["findings"] if f["title"] == "GitHub token")
            self.assertEqual(hit["line"], 2)
            self.assertNotIn(token, json.dumps(result))
            self.assertNotIn(token, html_report(result))

    def test_exclusions_binary_and_env_template(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "node_modules").mkdir()
            (root / "node_modules" / "secret").write_text("ghp_" + "a" * 36)
            (root / "binary").write_bytes(b"\x00ghp_" + b"a" * 36)
            (root / ".env.example").write_text("TOKEN=your-token")
            (root / ".env").write_text("MODE=dev")
            result = scan(root)
            self.assertEqual(result["stats"]["files"], 3)
            self.assertEqual(result["stats"]["skipped_content"], 1)
            warnings = [f for f in result["findings"] if f["severity"] == "warning"]
            self.assertEqual([f["path"] for f in warnings], [".env"])
            self.assertFalse(any(f["severity"] == "error" for f in result["findings"]))

    def test_report_escapes_untrusted_paths(self):
        result = {"root": "<script>alert(1)</script>", "stats": {"files": 0, "text_files": 0, "skipped_content": 0, "skipped_links": 0}, "findings": []}
        report = html_report(result)
        self.assertNotIn("<script>", report)
        self.assertIn("&lt;script&gt;", report)

    def test_invalid_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                scan(Path(folder) / "missing")

    def test_large_text_content_is_explicitly_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "large.txt").write_bytes(b"a" * (2 * 1024 * 1024 + 1))
            self.assertEqual(scan(folder)["stats"]["skipped_content"], 1)


if __name__ == "__main__":
    unittest.main()
