import unittest

from gui.widgets import (
    TABLE_COL_MAX_WIDTH,
    TABLE_COL_MIN_WIDTH,
    _table_column_widths,
    _text_units,
)


class TableWidthTests(unittest.TestCase):
    """验证预览表格列宽估算，避免多列数据再次横向挤丢。"""

    def test_chinese_text_counts_as_wider_than_ascii(self):
        self.assertEqual(_text_units("金额AB"), 6)

    def test_column_width_has_minimum_and_maximum(self):
        widths = _table_column_widths(
            ["a", "very_long_column"],
            [
                ("x", "value"),
                ("y", "z" * 200),
            ],
        )

        self.assertEqual(widths[0], TABLE_COL_MIN_WIDTH)
        self.assertEqual(widths[1], TABLE_COL_MAX_WIDTH)

    def test_many_short_columns_still_have_scrollable_total_width(self):
        columns = [f"c{i}" for i in range(30)]
        rows = [tuple(range(30))]
        widths = _table_column_widths(columns, rows)

        self.assertTrue(all(width >= TABLE_COL_MIN_WIDTH for width in widths))
        self.assertGreater(sum(widths), 30 * 80)


if __name__ == "__main__":
    unittest.main()
