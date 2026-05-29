"""GUI 主窗口入口（customtkinter 重构版）。

布局：
    ┌────────────────────────────────────────────┐
    │                                            │
    │           (页面容器：主页 或 子页)         │  ← container
    │                                            │
    ├────────────────────────────────────────────┤
    │ 底部状态栏（self.status_var）              │  ← status_bar
    └────────────────────────────────────────────┘

导航逻辑：
    - 默认显示主页（HomePage 仪表盘 6 卡片）
    - 点卡片 → 进对应子页面
    - 子页面顶部「← 返回主页」回到主页（由 BasePage 提供）
    - 子页面顶部「下一步：XXX →」直接跳到下一模块

数据共享：
    App 持有 loader / cleaner / rfm_analyzer / rfm_df / visualizer 等核心对象，
    子页面通过 self.app.xxx 访问。

为什么换 customtkinter：
    用户 2026-05-27 决定用 customtkinter 完全重写界面，因课程允许界面"完全 AI 生成"，
    答辩成本豁免（见 memory collab-pacing 的"GUI/Web 范围豁免"段）。
    customtkinter 提供圆角、阴影、统一字体、亮/暗模式等现代视觉。
"""

import customtkinter as ctk

from gui.widgets import UI_COLORS as COLORS, make_chart_progress


class App(ctk.CTk):
    """主应用窗口（继承 customtkinter.CTk 而非 tk.Tk）。

    CTk 是 customtkinter 重写的窗口类——和 tk.Tk 用法基本一致，
    但 widget 必须用 ctk.CTkXxx 系列，不能混 ttk.（混 tk.Text/ttk.Treeview 可以但视觉割裂）
    """

    # ═══════════════════════════════════════════════════════════════════
    # 主题配置
    # ═══════════════════════════════════════════════════════════════════
    # customtkinter 自带主题系统——通过 set_appearance_mode + set_default_color_theme 配置。
    # 我们仍保留一个 THEME 字典只为辅助色（状态栏、提示横幅等不在 ctk 默认范围内）
    THEME = {
        # ═══ 主背景（窗口本身的色，CTk 默认有 light/dark 模式）═══
        "window_bg_light": COLORS["page_bg"],        # 浅模式整体偏冷白

        # ═══ 状态栏（底部细条）═══
        "status_bar_bg": COLORS["text"],
        "status_bar_fg": "#ffffff",

        # ═══ 顶部条（BasePage 的标题/返回钮容器）═══
        "header_bg": COLORS["panel_bg"],              # 顶部条白底
        "title_fg": COLORS["text"],               # 标题深蓝灰

        # ═══ 返回按钮（深灰克制色——回退是次要动作）═══
        "back_fg": COLORS["gray"],
        "back_hover": COLORS["gray_hover"],
        "back_text": "#ffffff",

        # ═══ 下一步按钮（亮蓝引导色——前进是主要动作）═══
        "next_fg": COLORS["blue"],
        "next_hover": COLORS["blue_hover"],
        "next_text": "#ffffff",

        # ═══ 各页面动作按钮（如「一键全清洗」「查看月度趋势」） ═══
        "action_fg": COLORS["blue"],
        "action_hover": COLORS["blue_hover"],
        "action_text": "#ffffff",

        # ═══ 前置条件提示横幅（黄色 warning） ═══
        "hint_bg": COLORS["amber_soft"],
        "hint_fg": COLORS["amber"],
    }
    # ═══════════════════════════════════════════════════════════════════

    def __init__(self):
        # ───── customtkinter 全局配置（必须在创建窗口前/后调用）─────
        # appearance_mode: "light" / "dark" / "system"——用户选 light
        # color_theme:     "blue" / "green" / "dark-blue"——用户选 blue（与 hover 蓝边框统一）
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        super().__init__()
        self.title("RFM 客户分群分析系统")
        self.geometry("1300x900")

        # ───── 共享数据对象（子页面通过 self.app.xxx 访问） ─────
        self.loader = None
        self.cleaner = None
        self.rfm_analyzer = None
        self.rfm_df = None
        self.visualizer = None
        self.cleaning_history = []
        self.chart_progress = make_chart_progress()

        # ───── 状态栏文本（子页面调 self.app.set_status("...") 更新） ─────
        self.status_var = ctk.StringVar(value="就绪 - 请选择主页上的「加载数据」开始")

        # ───── 当前显示的页面 + 全部页面字典 ─────
        self.current_page = None
        self.pages = {}

        self._build_ui()

    def _build_ui(self):
        """搭骨架：状态栏 → 页面容器 → 注册所有页面 → 显示主页。"""

        # ───── 底部状态栏 ─────
        # 用 CTkLabel 而不是 tk.Label——保持视觉统一
        # height=30 固定高度防被压缩
        status_bar = ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            fg_color=self.THEME["status_bar_bg"],
            text_color=self.THEME["status_bar_fg"],
            font=("SimHei", 10),
            anchor="w",
            corner_radius=0,
            height=30,
        )
        status_bar.pack(fill="x", side="bottom")

        # ───── 中间页面容器 ─────
        # fg_color=transparent 让 container 跟随窗口默认色（light 模式下浅冷白）
        container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        container.pack(fill="both", expand=True)

        # ───── 注册所有页面 ─────
        # 延迟 import 避免循环依赖（各 page 文件可能 from gui.window import App）
        from gui.pages.home_page import HomePage
        from gui.pages.load_page import LoadPage
        from gui.pages.cleaner_page import CleanerPage
        from gui.pages.rfm_page import RFMPage
        from gui.pages.sales_page import SalesPage
        from gui.pages.product_page import ProductPage
        from gui.pages.overview_page import OverviewPage

        page_specs = [
            ("主页",     HomePage),
            ("加载数据", LoadPage),
            ("数据清洗", CleanerPage),
            ("RFM 分析", RFMPage),
            ("销售分析", SalesPage),
            ("商品分析", ProductPage),
            ("图表总览", OverviewPage),
        ]
        for label, PageClass in page_specs:
            self.pages[label] = PageClass(container, app=self)

        # 默认显示主页（仪表盘）
        self.show_page("主页")

    def show_page(self, label):
        """切换到指定页面，并触发 on_show 钩子。

        on_show 由 BasePage 提供：检查前置条件并刷新提示横幅。
        HomePage 也定义了空 on_show，所以这里不用判断类型直接调。
        """
        if self.current_page is not None:
            self.current_page.pack_forget()

        target = self.pages[label]
        target.pack(fill="both", expand=True)
        self.current_page = target

        target.on_show()

    def set_status(self, text):
        """统一更新底部状态栏文字。子页面调它。"""
        self.status_var.set(text)


def run():
    """GUI 入口函数。被 main.py 调用。"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()
