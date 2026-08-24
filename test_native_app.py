from pathlib import Path
import unittest

from native_app import make_batch_options


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


if __name__ == "__main__":
    unittest.main()
