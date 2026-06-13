"""Display helper tests for the home dashboard."""

import unittest

from gui.pages.home_page import (
    ALCHEMY_ROWS,
    alchemy_column_change_text,
    alchemy_gauge_font_size,
    alchemy_row_change_text,
    fit_font_size,
)


class HomePageDisplayTests(unittest.TestCase):
    """Verify home dashboard display helpers stay readable."""

    def test_gauge_percent_font_is_capped(self):
        """Common percent strings should not use the old oversized value font."""
        self.assertLessEqual(alchemy_gauge_font_size("99.2%", 180), 22)
        self.assertLess(alchemy_gauge_font_size("100.0%", 180), 25)

    def test_gauge_font_shrinks_for_longer_text(self):
        """Longer gauge text should get a smaller font than compact text."""
        compact = alchemy_gauge_font_size("9.9%", 180)
        longer = alchemy_gauge_font_size("100.0%", 180)
        self.assertGreater(compact, longer)

    def test_gauge_placeholder_remains_readable(self):
        """Placeholder text should remain visible without being oversized."""
        self.assertEqual(alchemy_gauge_font_size("--", 180), 22)

    def test_row_change_text_is_field_agnostic(self):
        """The home quality metric should use row counts, not any specific column."""
        self.assertEqual(alchemy_row_change_text(8399, 8336, True), "减少 63")
        self.assertEqual(alchemy_row_change_text(100, 100, True), "0")
        self.assertEqual(alchemy_row_change_text(100, 0, False), "待清洗")
        self.assertEqual(alchemy_row_change_text(0, 0, False), "--")

    def test_column_change_text_is_field_agnostic(self):
        """Column count changes should be summarized without relying on field names."""
        self.assertEqual(alchemy_column_change_text(12, 10, True), "减少 2")
        self.assertEqual(alchemy_column_change_text(10, 12, True), "增加 2")
        self.assertEqual(alchemy_column_change_text(10, 10, True), "0")
        self.assertEqual(alchemy_column_change_text(10, 0, False), "待清洗")

    def test_fit_font_size_shrinks_until_it_fits(self):
        """长文本在最大字号放不下时，应逐档缩小到刚好放下；短文本保持最大字号。"""
        measure = lambda t, s: len(t) * s  # 假测量器：宽度 = 字符数 × 字号
        self.assertEqual(fit_font_size("减少 63", 5 * 15, measure, max_size=15, min_size=9), 15)
        # "减少 154,361" 共 10 字符；usable=100 → 需 10*size<=100 → size=10
        self.assertEqual(fit_font_size("减少 154,361", 100, measure, max_size=15, min_size=9), 10)

    def test_fit_font_size_respects_min(self):
        """极窄时即使最小字号仍超，也不应低于 min_size。"""
        measure = lambda t, s: len(t) * s
        self.assertEqual(fit_font_size("减少 1,234,567", 5, measure, max_size=15, min_size=9), 9)

    def test_fit_font_size_falls_back_when_width_invalid(self):
        """宽度无效(<=1)或空文本时回退最大字号，避免无意义的收缩。"""
        measure = lambda t, s: len(t) * s
        self.assertEqual(fit_font_size("减少 154,361", 1, measure, max_size=15), 15)
        self.assertEqual(fit_font_size("", 100, measure, max_size=15), 15)

    def test_alchemy_panel_has_multiple_metrics(self):
        """The alchemy panel should not collapse back to a single metric."""
        keys = {item[1] for item in ALCHEMY_ROWS}
        self.assertGreaterEqual(len(ALCHEMY_ROWS), 4)
        self.assertIn("raw_rows", keys)
        self.assertIn("clean_rows", keys)
        self.assertIn("row_change", keys)
        self.assertIn("col_change", keys)


if __name__ == "__main__":
    unittest.main()
