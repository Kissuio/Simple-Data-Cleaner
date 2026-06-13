"""加载页 on_show 同步重绘回归测试。

背景：加载页真正渲染预览表 / 指标 / 字段识别的是 `_refresh_loaded_state`，
它原本只在「选择文件」回调里被调用，导致两种情况下页面不刷新：
① 新手带练直接写入 `app.loader` 后切到本页；② 加载完切去别页再切回本页。
修复后 `on_show` 在已有数据时必须重绘一次。本测试用裸实例（不建 GUI）守住这一行为，
防止以后又把重绘逻辑从 on_show 里漏掉。
"""

import unittest
from types import SimpleNamespace

import pandas as pd

from gui.pages.load_page import LoadPage


class LoadPageOnShowSyncTests(unittest.TestCase):
    def _make_bare_page(self):
        page = LoadPage.__new__(LoadPage)  # 不走 __init__、不建 GUI
        page.requires = None  # 让基类 on_show 成为 no-op，便于隔离测试本页逻辑
        page._nav_calls = []
        page._loaded_calls = []
        page._refresh_nav_state = lambda *a, **k: page._nav_calls.append(True)
        page._refresh_loaded_state = lambda loader: page._loaded_calls.append(loader)
        return page

    def test_on_show_repaints_when_data_already_loaded(self):
        """已有 loader（如带练写入或切回本页）时，on_show 必须重绘已加载状态。"""
        page = self._make_bare_page()
        loader = SimpleNamespace(df=pd.DataFrame({"a": [1, 2]}))
        page.app = SimpleNamespace(loader=loader)

        LoadPage.on_show(page)

        self.assertEqual(page._loaded_calls, [loader], "有数据时应调用 _refresh_loaded_state 重绘")
        self.assertTrue(page._nav_calls, "导航状态也应刷新")

    def test_on_show_skips_repaint_when_no_data(self):
        """尚未加载数据时，on_show 不应调用重绘（避免对 None 取 df 崩溃）。"""
        page = self._make_bare_page()
        page.app = SimpleNamespace(loader=None)

        LoadPage.on_show(page)

        self.assertEqual(page._loaded_calls, [], "无数据时不应调用 _refresh_loaded_state")
        self.assertTrue(page._nav_calls)


if __name__ == "__main__":
    unittest.main()
