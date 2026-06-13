"""Teacher quick demo entry tests."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gui.window import (
    App,
    STARTUP_STATUS_TEXT,
    TEACHER_DEMO_DATA_PATH,
    TEACHER_QUICK_DEMO_DONE_NOTICE,
    TEACHER_QUICK_DEMO_DONE_TITLE,
    TEACHER_QUICK_DEMO_HOME_NOTICE,
    TEACHER_QUICK_DEMO_HOME_TITLE,
    TEACHER_QUICK_DEMO_GUIDE,
    TEACHER_QUICK_DEMO_REMINDER,
    TEACHER_STARTUP_NOTICE,
    TEACHER_STARTUP_NOTICE_TITLE,
)


class TeacherQuickDemoTests(unittest.TestCase):
    """Verify the teacher shortcut remains explicit and discoverable."""

    def test_demo_data_uses_online_retail_csv(self):
        """The shortcut should use the bundled Online Retail main CSV."""
        self.assertEqual(TEACHER_DEMO_DATA_PATH.name, "Online Retail.csv")
        self.assertEqual(TEACHER_DEMO_DATA_PATH.parent.name, "online_retail")

    def test_guide_explains_skipped_steps(self):
        """The confirmation dialog should explain what the shortcut automates."""
        for phrase in [
            "尊敬的老师",
            "直接查看系统最终生成的可视化图像",
            "加载数据",
            "数据清洗",
            "字段映射",
            "RFM 分析",
            "图表生成与预览",
            "页面中将呈现",
            "不会修改原始数据文件",
        ]:
            self.assertIn(phrase, TEACHER_QUICK_DEMO_GUIDE)

    def test_startup_reminder_points_to_shortcut(self):
        """The teacher reminder copy should point teachers to the shortcut."""
        self.assertIn("尊敬的老师", TEACHER_QUICK_DEMO_REMINDER)
        self.assertIn("图表预览", TEACHER_QUICK_DEMO_REMINDER)

    def test_startup_notice_points_to_both_in_app_entries(self):
        """The startup dialog should introduce both the purple shortcut and the green tour."""
        self.assertEqual(TEACHER_STARTUP_NOTICE_TITLE, "教师查阅提示")
        for phrase in [
            "尊敬的老师",
            "右上角",
            "紫色按钮",
            "教师快速查阅",
            "新手带练",
            "更贴近真实业务数据",
            "图表结果",
            "不会在关闭弹窗后自动开始任何演示",
        ]:
            self.assertIn(phrase, TEACHER_STARTUP_NOTICE)
        # 已删除外置文档，弹窗不应再引用它
        self.assertNotIn("教师额外阅读", TEACHER_STARTUP_NOTICE)

    def test_startup_status_is_not_teacher_entry(self):
        """The bottom status bar should stay separate from the teacher shortcut."""
        self.assertIn("就绪", STARTUP_STATUS_TEXT)
        self.assertNotIn("教师", STARTUP_STATUS_TEXT)

    def test_completion_notice_explains_final_page_and_return_home(self):
        """The final teacher-only popup should explain the overview page."""
        self.assertEqual(TEACHER_QUICK_DEMO_DONE_TITLE, "教师快速查阅已完成")
        for phrase in [
            "尊敬的老师",
            "教师快速查阅",
            "图表总览",
            "右侧图表目录",
            "导出此图",
            "AI 解读",
            "返回主页",
            "最终状态",
            "图表预览",
        ]:
            self.assertIn(phrase, TEACHER_QUICK_DEMO_DONE_NOTICE)

    def test_home_notice_explains_manual_followup(self):
        """The home popup should invite teachers to continue with the manual."""
        self.assertEqual(TEACHER_QUICK_DEMO_HOME_TITLE, "可以继续体验完整流程")
        for phrase in [
            "尊敬的老师",
            "回到主页",
            "教师快速查阅",
            "加载数据",
            "新手带练",
            "数据清洗",
            "字段映射",
            "RFM",
            "图表总览",
            "不同数据",
        ]:
            self.assertIn(phrase, TEACHER_QUICK_DEMO_HOME_NOTICE)

    def test_completion_notice_flag_only_starts_from_purple_entry(self):
        """Only the purple teacher entry should arm the completion popup."""
        app = SimpleNamespace(
            teacher_startup_notice_seen=False,
            teacher_quick_demo_completion_notice_pending=False,
        )

        self.assertFalse(App.should_show_teacher_quick_demo_completion_notice(app))

        App.mark_teacher_quick_demo_from_purple_entry(app)
        self.assertTrue(app.teacher_startup_notice_seen)
        self.assertTrue(app.teacher_quick_demo_completion_notice_pending)
        self.assertTrue(App.should_show_teacher_quick_demo_completion_notice(app))
        self.assertFalse(App.should_show_teacher_quick_demo_completion_notice(app))

    def test_completion_notice_can_be_cancelled_after_failed_demo(self):
        """A failed teacher flow should not leave a later popup armed."""
        app = SimpleNamespace(teacher_quick_demo_completion_notice_pending=True)

        App.cancel_teacher_quick_demo_completion_notice(app)

        self.assertFalse(App.should_show_teacher_quick_demo_completion_notice(app))

    def test_home_notice_waits_until_any_return_home_after_teacher_flow(self):
        """The manual followup should survive intermediate pages and trigger at home."""
        app = SimpleNamespace(teacher_quick_demo_home_notice_pending=False)

        self.assertFalse(App.should_show_teacher_quick_demo_home_notice(app, "图表总览", "主页"))

        app.teacher_quick_demo_home_notice_pending = True
        self.assertFalse(App.should_show_teacher_quick_demo_home_notice(app, "图表总览", "数据清洗"))
        self.assertTrue(app.teacher_quick_demo_home_notice_pending)
        self.assertFalse(App.should_show_teacher_quick_demo_home_notice(app, "数据清洗", "RFM 分析"))
        self.assertTrue(app.teacher_quick_demo_home_notice_pending)
        self.assertTrue(App.should_show_teacher_quick_demo_home_notice(app, "RFM 分析", "主页"))
        self.assertFalse(App.should_show_teacher_quick_demo_home_notice(app, "商品分析", "主页"))

    def test_home_notice_closing_resets_teacher_demo_state(self):
        """The final home popup should reset demo state when dismissed."""
        app = SimpleNamespace()
        app.reset_teacher_quick_demo_state_for_manual_start = lambda: None

        with patch("gui.intro_dialog.IntroDialog") as intro_dialog:
            App.show_teacher_quick_demo_home_notice(app)

        _, kwargs = intro_dialog.call_args
        self.assertIs(kwargs["on_close"], app.reset_teacher_quick_demo_state_for_manual_start)
        self.assertEqual(kwargs["button_text"], "知道了，继续体验")

    def test_teacher_demo_reset_clears_analysis_state(self):
        """Resetting after the final popup should return the app to a fresh start."""
        statuses = []
        refreshes = []
        page_refreshes = []

        class FakeVar:
            def __init__(self):
                self.value = "old"

            def set(self, value):
                self.value = value

        app = SimpleNamespace(
            loader=object(),
            cleaner=object(),
            rfm_analyzer=object(),
            rfm_df=object(),
            visualizer=object(),
            cleaning_history=[{"old": True}],
            chart_progress={"overview": {"old_chart"}},
            data_filter={"date_from": "old", "date_to": "old", "country": "old"},
            field_mapping={"CustomerID": "CustomerID"},
            mapping_intro_seen=True,
            cleaning_intro_seen=True,
            teacher_quick_demo_completion_notice_pending=True,
            teacher_quick_demo_home_notice_pending=True,
            mapping_summary_var=FakeVar(),
            current_page=SimpleNamespace(on_show=lambda: page_refreshes.append(True)),
        )
        app.reset_data_filter = lambda: setattr(
            app,
            "data_filter",
            {"date_from": None, "date_to": None, "country": None},
        )
        app._refresh_top_bars = lambda: refreshes.append(True)
        app.set_status = lambda text: statuses.append(text)

        App.reset_teacher_quick_demo_state_for_manual_start(app)

        self.assertIsNone(app.loader)
        self.assertIsNone(app.cleaner)
        self.assertIsNone(app.rfm_analyzer)
        self.assertIsNone(app.rfm_df)
        self.assertIsNone(app.visualizer)
        self.assertEqual(app.cleaning_history, [])
        self.assertTrue(all(not generated for generated in app.chart_progress.values()))
        self.assertEqual(app.data_filter, {"date_from": None, "date_to": None, "country": None})
        self.assertIsNone(app.field_mapping)
        self.assertFalse(app.mapping_intro_seen)
        self.assertFalse(app.cleaning_intro_seen)
        self.assertFalse(app.teacher_quick_demo_completion_notice_pending)
        self.assertFalse(app.teacher_quick_demo_home_notice_pending)
        self.assertEqual(app.mapping_summary_var.value, "")
        self.assertEqual(refreshes, [True])
        self.assertEqual(page_refreshes, [True])
        self.assertEqual(statuses, [STARTUP_STATUS_TEXT])


if __name__ == "__main__":
    unittest.main()
