from pathlib import Path
from unittest.mock import patch
import unittest

from native_app import ScreenshotApp, make_batch_options, request_cancel


class NativeAppOptionsTest(unittest.TestCase):
    def test_make_batch_options_converts_window_fields(self):
        opts = make_batch_options(
            workbook_path=Path("/tmp/input.xlsx"),
            run_dir=Path("/tmp/run"),
            values={
                "sheet_name": "数据表",
                "link_col": "C",
                "output_col": "F",
                "start_row": "3",
                "end_row": "",
                "resume": True,
                "timeout_ms": "30000",
                "min_delay_ms": "4000",
                "max_delay_ms": "65000",
                "max_retries": "3",
                "max_consecutive_failures": "6",
                "use_system_chrome_profile": True,
            },
        )

        self.assertEqual(opts.workbook_path, Path("/tmp/input.xlsx"))
        self.assertEqual(opts.run_dir, Path("/tmp/run"))
        self.assertEqual(opts.sheet_name, "数据表")
        self.assertEqual(opts.link_col, "C")
        self.assertEqual(opts.output_col, "F")
        self.assertEqual(opts.start_row, 3)
        self.assertIsNone(opts.end_row)
        self.assertTrue(opts.resume)
        self.assertEqual(opts.timeout_ms, 30000)
        self.assertEqual(opts.min_delay_ms, 4000)
        self.assertEqual(opts.max_delay_ms, 65000)
        self.assertEqual(opts.max_retries, 3)
        self.assertEqual(opts.max_consecutive_failures, 6)
        self.assertTrue(opts.use_system_chrome_profile)

    def test_request_cancel_writes_cancel_flag(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)

            cancel_path = request_cancel(run_dir)

            self.assertEqual(cancel_path, run_dir / "cancel_requested")
            self.assertTrue(cancel_path.exists())
            self.assertIn("用户手动终止", cancel_path.read_text(encoding="utf-8"))

    def test_live_progress_text_reports_elapsed_wait(self):
        with patch("native_app.time.time", return_value=130.0):
            text = ScreenshotApp.live_progress_text(
                None,
                "正在处理第 5 行，第 1 次尝试",
                {"startedAt": 100000, "timeoutMs": 25000},
            )

        self.assertIn("已超过预计等待 30s / 25s", text)
        self.assertIn("可点“终止当前任务”", text)


if __name__ == "__main__":
    unittest.main()
