import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from gui.pages.cleaner_page import CLEANING_GUIDE, CleanerPage


class CleanerExportTests(unittest.TestCase):
    """验证清洗页的当前数据选择和导出逻辑。"""

    def test_current_result_prefers_cleaner_dataframe(self):
        raw = pd.DataFrame({"value": [1, 2]})
        cleaned = pd.DataFrame({"value": [2]})
        page = CleanerPage.__new__(CleanerPage)
        page.app = SimpleNamespace(
            loader=SimpleNamespace(df=raw),
            cleaner=SimpleNamespace(df=cleaned),
        )

        result, state = CleanerPage._current_result_df(page)

        self.assertIs(result, cleaned)
        self.assertEqual(state, "cleaned")

    def test_current_result_falls_back_to_loaded_dataframe(self):
        raw = pd.DataFrame({"value": [1]})
        page = CleanerPage.__new__(CleanerPage)
        page.app = SimpleNamespace(
            loader=SimpleNamespace(df=raw),
            cleaner=None,
        )

        result, state = CleanerPage._current_result_df(page)

        self.assertIs(result, raw)
        self.assertEqual(state, "raw")

    def test_default_export_name_uses_source_stem(self):
        page = CleanerPage.__new__(CleanerPage)
        page.app = SimpleNamespace(
            loader=SimpleNamespace(file_path=r"D:\data\orders.xlsx")
        )

        self.assertEqual(
            CleanerPage._default_export_name(page),
            "orders_cleaned.csv",
        )

    def test_csv_export_uses_utf8_sig(self):
        page = CleanerPage.__new__(CleanerPage)
        df = pd.DataFrame({"客户": ["张三"], "金额": [12.5]})

        with patch.object(pd.DataFrame, "to_csv") as to_csv:
            CleanerPage._export_dataframe(page, df, "cleaned.csv")

        to_csv.assert_called_once_with(
            "cleaned.csv",
            index=False,
            encoding="utf-8-sig",
        )

    def test_xlsx_export_uses_excel_writer(self):
        page = CleanerPage.__new__(CleanerPage)
        df = pd.DataFrame({"客户": ["张三"], "金额": [12.5]})

        with patch.object(pd.DataFrame, "to_excel") as to_excel:
            CleanerPage._export_dataframe(page, df, "cleaned.xlsx")

        to_excel.assert_called_once_with("cleaned.xlsx", index=False)

    def test_cleaning_guide_mentions_preview_and_export(self):
        self.assertIn("预览当前清洗结果", CLEANING_GUIDE)
        self.assertIn("导出为新的 CSV 或 Excel 文件", CLEANING_GUIDE)


if __name__ == "__main__":
    unittest.main()
