import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from gui.pages.cleaner_page import CLEANING_GUIDE, CleanerPage
from gui.window import RFM_MAPPING_GUIDE


class GuideTests(unittest.TestCase):
    """验证清洗与映射说明能够说明工具无固定顺序并可重复打开。"""

    def test_cleaning_guide_explicitly_rejects_fixed_pipeline_model(self):
        """清洗说明必须明确工具分类没有固定执行顺序。"""
        for phrase in [
            "没有固定顺序",
            "三类工具入口",
            "自由组合",
            "撤销上一步",
            "不会直接修改",
        ]:
            self.assertIn(phrase, CLEANING_GUIDE)

    def test_cleaning_guide_is_shown_once_per_loaded_dataset(self):
        """同一份数据只自动提示一次，但换数据后可由状态重置再次提示。"""
        page = CleanerPage.__new__(CleanerPage)
        page.app = SimpleNamespace(
            loader=SimpleNamespace(df=pd.DataFrame({"x": [1]})),
            cleaning_intro_seen=False,
            guided_mode_var=SimpleNamespace(get=lambda: True),
        )
        page._show_cleaning_guide = lambda: setattr(page, "show_count", 1)
        page.show_count = 0

        CleanerPage._maybe_show_cleaning_guide(page)
        CleanerPage._maybe_show_cleaning_guide(page)

        self.assertTrue(page.app.cleaning_intro_seen)
        self.assertEqual(page.show_count, 1)

    def test_cleaning_guide_not_auto_shown_when_guided_mode_off(self):
        """引导模式关闭时，进入清洗页不应自动弹说明（提示改到新手学习入口）。"""
        page = CleanerPage.__new__(CleanerPage)
        page.app = SimpleNamespace(
            loader=SimpleNamespace(df=pd.DataFrame({"x": [1]})),
            cleaning_intro_seen=False,
            guided_mode_var=SimpleNamespace(get=lambda: False),
        )
        page._show_cleaning_guide = lambda: setattr(page, "show_count", 1)
        page.show_count = 0

        CleanerPage._maybe_show_cleaning_guide(page)

        self.assertEqual(page.show_count, 0)
        self.assertFalse(page.app.cleaning_intro_seen)

    def test_cleaning_help_button_method_can_reopen_dialog(self):
        """手动帮助入口应随时能够重新打开清洗说明。"""
        page = CleanerPage.__new__(CleanerPage)

        with patch("gui.intro_dialog.IntroDialog") as intro_dialog:
            CleanerPage._show_cleaning_guide(page)

        intro_dialog.assert_called_once()
        self.assertEqual(
            intro_dialog.call_args.kwargs["body"],
            CLEANING_GUIDE,
        )

    def test_mapping_guide_remains_complete_for_help_button(self):
        """映射帮助按钮使用的正文应继续包含核心 RFM 和金额规则。"""
        for phrase in ["Recency", "Frequency", "Monetary", "Quantity × UnitPrice"]:
            self.assertIn(phrase, RFM_MAPPING_GUIDE)


if __name__ == "__main__":
    unittest.main()
