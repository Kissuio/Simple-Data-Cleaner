import unittest
from unittest.mock import patch
from types import SimpleNamespace

import pandas as pd

from gui.pages.load_page import LoadPage
from gui.window import App, RFM_MAPPING_GUIDE, make_data_filter


class _PageStub:
    """记录页面是否因状态变化而刷新。"""

    def __init__(self):
        self.show_count = 0

    def on_show(self):
        self.show_count += 1


class FilterStateTests(unittest.TestCase):
    """验证更换数据语义时不会沿用旧筛选条件。"""

    def test_make_data_filter_returns_independent_empty_states(self):
        """默认筛选工厂每次都应返回独立字典。"""
        first = make_data_filter()
        second = make_data_filter()

        first["country"] = "旧国家"

        self.assertEqual(
            second,
            {"date_from": None, "date_to": None, "country": None},
        )

    def test_confirming_field_mapping_resets_old_filter(self):
        """重新映射可能更换日期或国家来源，因此必须清除旧筛选。"""
        app = App.__new__(App)
        app.data_filter = {
            "date_from": pd.Timestamp("2024-01-01"),
            "date_to": pd.Timestamp("2024-12-31"),
            "country": "旧国家",
        }
        app.field_mapping = {"Country": "old_country"}
        app.rfm_analyzer = object()
        app.rfm_df = object()
        app.chart_progress = {"old": {"chart"}}
        app.current_page = _PageStub()
        app.current_label = "主页"
        app.set_status = lambda _text: None

        App._on_field_mapping_confirmed(
            app,
            {"InvoiceDate": "date", "Country": "new_country"},
        )

        self.assertEqual(app.data_filter, make_data_filter())
        self.assertIsNone(app.rfm_analyzer)
        self.assertIsNone(app.rfm_df)
        self.assertEqual(app.current_page.show_count, 1)

    def test_loading_transition_resets_old_filter(self):
        """选择新文件时应连同旧分析状态一起清除筛选。"""
        reset_calls = []
        app = SimpleNamespace(
            cleaner=object(),
            rfm_analyzer=object(),
            rfm_df=object(),
            visualizer=object(),
            field_mapping={"Country": "country"},
            mapping_intro_seen=True,
            cleaning_intro_seen=True,
            chart_progress={"sales": {"monthly_trend"}},
            reset_data_filter=lambda: reset_calls.append(True),
        )
        page = LoadPage.__new__(LoadPage)
        page.app = app
        page._archive_current_cleaning_log = lambda: None

        LoadPage._reset_downstream_state(page)

        self.assertEqual(reset_calls, [True])
        self.assertIsNone(app.cleaner)
        self.assertIsNone(app.rfm_analyzer)
        self.assertIsNone(app.rfm_df)
        self.assertIsNone(app.visualizer)
        self.assertIsNone(app.field_mapping)
        self.assertFalse(app.mapping_intro_seen)
        self.assertFalse(app.cleaning_intro_seen)

    def test_first_mapping_opens_guide_then_mapping_dialog(self):
        """每份数据首次映射前应先讲解，关闭说明后再进入映射。"""
        frame = pd.DataFrame({"customer": [1]})
        app = App.__new__(App)
        app.cleaner = SimpleNamespace(df=frame)
        app.field_mapping = None
        app.mapping_intro_seen = False
        app.guided_mode_var = SimpleNamespace(get=lambda: True)

        with (
            patch("gui.intro_dialog.IntroDialog") as intro_dialog,
            patch("gui.mapping_dialog.MappingDialog") as mapping_dialog,
        ):
            App.open_field_mapping(app)

            intro_dialog.assert_called_once()
            mapping_dialog.assert_not_called()
            callback = intro_dialog.call_args.kwargs["on_close"]
            callback()
            mapping_dialog.assert_called_once()

        self.assertTrue(app.mapping_intro_seen)

    def test_manual_remap_skips_intro(self):
        """调整已有映射时应直接打开映射窗口，不重复展示教程。"""
        frame = pd.DataFrame({"customer": [1]})
        app = App.__new__(App)
        app.cleaner = SimpleNamespace(df=frame)
        app.field_mapping = {"CustomerID": "customer"}
        app.mapping_intro_seen = True

        with (
            patch("gui.intro_dialog.IntroDialog") as intro_dialog,
            patch("gui.mapping_dialog.MappingDialog") as mapping_dialog,
        ):
            App.open_field_mapping(app, show_intro=False)

            intro_dialog.assert_not_called()
            mapping_dialog.assert_called_once()

    def test_rfm_guide_contains_model_and_usage_instructions(self):
        """教程正文应同时覆盖模型含义、流程和核心映射字段。"""
        for phrase in [
            "Recency",
            "Frequency",
            "Monetary",
            "推荐使用流程",
            "CustomerID",
            "InvoiceNo",
            "InvoiceDate",
            "TotalPrice",
            "Quantity × UnitPrice",
        ]:
            self.assertIn(phrase, RFM_MAPPING_GUIDE)


if __name__ == "__main__":
    unittest.main()
