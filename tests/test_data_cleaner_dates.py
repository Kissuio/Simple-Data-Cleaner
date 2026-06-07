import unittest

import pandas as pd

from data_handlers.data_cleaner import DataCleaner


class DateConversionTests(unittest.TestCase):
    """验证日期转换覆盖常见导出格式且不会静默误判。"""

    def _convert(self, values, **kwargs):
        cleaner = DataCleaner(pd.DataFrame({"date": values}))
        cleaner.convert_date("date", **kwargs)
        return cleaner

    def test_month_first_text_and_iso_can_coexist(self):
        """美式斜杠日期与年在前 ISO 日期应分别正确解析。"""
        cleaner = self._convert(
            [
                "12/1/2010 8:26",
                "1/13/2010 9:00",
                "2010-12-02T10:00:00",
            ]
        )

        self.assertEqual(
            cleaner.df["date"].tolist(),
            [
                pd.Timestamp("2010-12-01 08:26:00"),
                pd.Timestamp("2010-01-13 09:00:00"),
                pd.Timestamp("2010-12-02 10:00:00"),
            ],
        )

    def test_day_first_is_inferred_without_corrupting_year_first_dates(self):
        """列内出现 31 日时应推断日在前，同时保持 YYYY-MM-DD 语义。"""
        cleaner = self._convert(
            ["31/01/2026", "02/01/2026", "2026-01-03"]
        )

        self.assertEqual(
            cleaner.df["date"].tolist(),
            [
                pd.Timestamp("2026-01-31"),
                pd.Timestamp("2026-01-02"),
                pd.Timestamp("2026-01-03"),
            ],
        )

    def test_compact_numeric_dates_support_multiple_precisions(self):
        """紧凑数字应覆盖年、年月、日期及精确到秒的时间。"""
        cleaner = self._convert(
            [
                2026,
                202601,
                20260131,
                2026013112,
                202601311230,
                20260131123045,
            ]
        )

        self.assertEqual(
            cleaner.df["date"].tolist(),
            [
                pd.Timestamp("2026-01-01"),
                pd.Timestamp("2026-01-01"),
                pd.Timestamp("2026-01-31"),
                pd.Timestamp("2026-01-31 12:00:00"),
                pd.Timestamp("2026-01-31 12:30:00"),
                pd.Timestamp("2026-01-31 12:30:45"),
            ],
        )

    def test_excel_and_unix_numeric_dates_are_recognized(self):
        """Excel 序号及 Unix 秒/毫秒/微秒/纳秒应得到同一真实时间。"""
        cleaner = self._convert(
            [
                44197.5,
                1704067200,
                1704067200000,
                1704067200000000,
                1704067200000000000,
            ]
        )

        self.assertEqual(
            cleaner.df["date"].tolist(),
            [
                pd.Timestamp("2021-01-01 12:00:00"),
                pd.Timestamp("2024-01-01"),
                pd.Timestamp("2024-01-01"),
                pd.Timestamp("2024-01-01"),
                pd.Timestamp("2024-01-01"),
            ],
        )

    def test_scientific_notation_numeric_string_is_supported(self):
        """电子表格导出的科学计数法时间戳也应进入数值解析。"""
        cleaner = self._convert(["1.7040672e+18"])

        self.assertEqual(
            cleaner.df.loc[0, "date"],
            pd.Timestamp("2024-01-01"),
        )

    def test_failure_log_reports_rate_and_samples(self):
        """转换日志应区分空值，并给出非空失败样例。"""
        cleaner = self._convert(["2026-01-01", "not-a-date", "", None])

        self.assertTrue(pd.isna(cleaner.df.loc[1, "date"]))
        self.assertIn("成功 1/2", cleaner.log[-2])
        self.assertIn("not-a-date", cleaner.log[-1])
        self.assertTrue(cleaner.can_undo)


if __name__ == "__main__":
    unittest.main()
