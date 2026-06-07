import unittest

from gui.clean_dialog import TOOLBOX, _ScrollList
from gui.error_messages import friendly_error_message


class _FakeVar:
    """测试多选逻辑用的最小 BooleanVar 替身。"""

    def __init__(self, value=False):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FriendlyErrorTests(unittest.TestCase):
    """验证底层异常会转成可执行的中文指引。"""

    def test_missing_field_points_to_mapping(self):
        message = friendly_error_message(KeyError("InvoiceDate"), "生成销售图")

        self.assertIn("字段没有找到", message)
        self.assertIn("字段映射", message)
        self.assertNotIn("KeyError", message)

    def test_date_error_points_to_date_conversion(self):
        error = AttributeError("Can only use .dt accessor with datetimelike values")
        message = friendly_error_message(error, "生成月度趋势图")

        self.assertIn("日期列", message)
        self.assertIn("列转日期", message)
        self.assertNotIn(".dt accessor", message)

    def test_permission_error_explains_file_occupation(self):
        message = friendly_error_message(PermissionError("Permission denied"), "导出图表")

        self.assertIn("其他软件占用", message)
        self.assertIn("有写入权限的位置", message)

    def test_short_chinese_business_error_is_preserved(self):
        message = friendly_error_message(ValueError("至少需要一条有效交易记录"), "执行分析")

        self.assertIn("至少需要一条有效交易记录", message)
        self.assertIn("你可以这样处理", message)

    def test_unknown_english_error_is_not_shown_directly(self):
        message = friendly_error_message(RuntimeError("backend exploded at line 42"), "当前操作")

        self.assertIn("未识别的数据格式", message)
        self.assertNotIn("backend exploded", message)


class SelectAllTests(unittest.TestCase):
    """验证删空值行提供一键全选，并正确切换全部多选项。"""

    def test_drop_missing_enables_select_all_controls(self):
        step = next(item for item in TOOLBOX if item["key"] == "drop_missing")

        self.assertTrue(step["params"][0]["select_all"])

    def test_select_all_and_clear_all_change_every_option(self):
        changed = []
        fake_list = type("FakeList", (), {})()
        fake_list.multi = True
        fake_list.vars = {
            "CustomerID": _FakeVar(),
            "InvoiceDate": _FakeVar(),
            "Quantity": _FakeVar(),
        }
        fake_list._changed = lambda: changed.append(True)

        _ScrollList.select_all(fake_list)
        self.assertTrue(all(var.get() for var in fake_list.vars.values()))

        _ScrollList.clear_all(fake_list)
        self.assertTrue(all(not var.get() for var in fake_list.vars.values()))
        self.assertEqual(len(changed), 2)


if __name__ == "__main__":
    unittest.main()
