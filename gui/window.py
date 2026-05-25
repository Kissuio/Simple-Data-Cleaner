"""GUI 主窗口入口：顶部导航栏（6 按钮平铺） + 中间页面容器 + 底部状态栏。

数据共享：App 实例自身持有 loader / cleaner / rfm_analyzer / rfm_df 等核心对象，
子页面通过 self.app 引用访问，避免每个页面各自管理。

页面切换：所有页面都创建好放在 container 里，通过 pack/pack_forget 切换显示。
"""

import tkinter as tk
from tkinter import ttk

from gui.pages.home_page import HomePage
from gui.pages.cleaner_page import CleanerPage
from gui.pages.rfm_page import RFMPage
from gui.pages.sales_page import SalesPage
from gui.pages.product_page import ProductPage
from gui.pages.overview_page import OverviewPage


class App(tk.Tk):
    """主应用窗口，继承 tk.Tk。"""

    # ═══════════════════════════════════════════════════════════════════
    # 主题配置（后续要换样式/颜色，只改这里）
    # ═══════════════════════════════════════════════════════════════════
    # 注意：ttk 默认主题下，按钮背景色不能直接 configure。
    # 如果要换颜色，先在 _build_ui 里取消 style.theme_use("clam") 的注释，
    # 然后在下面 NAV_BUTTON_BG / NAV_BUTTON_FG 等填颜色值并启用。
    THEME = {
        # ═══ 主背景 ═══
        "window_bg": "#f0f2f5",
        # ═══ 顶部导航按钮（普通态）═══
        "nav_button_font": ("SimHei", 13, "bold"),
        "nav_button_padding": (12, 18),
        "nav_button_bg": "#2c3e50",         # 深蓝灰底
        "nav_button_fg": "#bdc3c7",         # 浅灰字（不抢眼）
        "nav_button_active_bg": "#34495e",  # 鼠标悬停略浅
        "nav_button_active_fg": "#ffffff",
        "nav_button_pressed_bg": "#1a252f", # 按下瞬间更深（视觉反馈）
        # ═══ 顶部导航按钮（当前选中态）═══
        "nav_selected_bg": "#3498db",       # 亮蓝高亮
        "nav_selected_fg": "#ffffff",
        "nav_selected_active_bg": "#5dade2",  # 当前选中按钮悬停时
        # ═══ 各页面动作按钮 ═══
        "action_button_font": ("SimHei", 12, "bold"),
        "action_button_padding": (22, 10),
        "action_button_bg": "#3498db",         # 亮蓝（和选中标签同色，统一）
        "action_button_fg": "#ffffff",
        "action_button_active_bg": "#5dade2",  # 悬停更浅一档
        "action_button_active_fg": "#ffffff",
        "action_button_pressed_bg": "#2874a6", # 按下更深一档
        # ═══ 状态栏 ═══
        "status_bar_bg": "#2c3e50",
        "status_bar_fg": "#ecf0f1",
        # ═══ 主题（True 才能让颜色生效）═══
        "use_clam_theme": True,
    }
    # ═══════════════════════════════════════════════════════════════════

    def __init__(self):
        super().__init__()
        self.title("RFM 客户分群分析系统")
        self.geometry("1300x900")
        self.configure(background=self.THEME["window_bg"])

        # 共享数据对象，子页面通过 self.app.xxx 访问
        self.loader = None
        self.cleaner = None
        self.rfm_analyzer = None
        self.rfm_df = None
        self.visualizer = None

        # 状态栏文本，子页面调 self.app.set_status("...") 更新
        self.status_var = tk.StringVar(value="就绪 - 请在【主页/数据】加载 CSV")

        # 记录当前显示的页面，便于切换时 pack_forget
        self.current_page = None
        # 存所有页面：{标签文字: Page 实例}
        self.pages = {}

        self._build_ui()

    def _build_ui(self):
        """搭骨架：顶部导航栏 + 中间页面容器 + 底部状态栏。"""

        # ───── 自定义导航按钮样式 ─────
        # 所有可配置项从 self.THEME 读，方便后续统一调主题
        style = ttk.Style()
        if self.THEME["use_clam_theme"]:
            # clam 主题允许定制 ttk 控件颜色（默认主题不行）
            style.theme_use("clam")

        # ───── Nav.TButton（普通态导航按钮）─────
        style.configure(
            "Nav.TButton",
            font=self.THEME["nav_button_font"],
            padding=self.THEME["nav_button_padding"],
            background=self.THEME["nav_button_bg"],
            foreground=self.THEME["nav_button_fg"],
            borderwidth=0,
            focusthickness=0,
        )
        # 状态映射：active=hover, pressed=按下
        style.map(
            "Nav.TButton",
            background=[
                ("pressed", self.THEME["nav_button_pressed_bg"]),
                ("active", self.THEME["nav_button_active_bg"]),
            ],
            foreground=[
                ("active", self.THEME["nav_button_active_fg"]),
            ],
        )

        # ───── NavSelected.TButton（当前选中导航按钮）─────
        style.configure(
            "NavSelected.TButton",
            font=self.THEME["nav_button_font"],
            padding=self.THEME["nav_button_padding"],
            background=self.THEME["nav_selected_bg"],
            foreground=self.THEME["nav_selected_fg"],
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "NavSelected.TButton",
            background=[
                ("active", self.THEME["nav_selected_active_bg"]),
            ],
        )

        # ───── Action.TButton（各页面动作按钮）─────
        style.configure(
            "Action.TButton",
            font=self.THEME["action_button_font"],
            padding=self.THEME["action_button_padding"],
            background=self.THEME["action_button_bg"],
            foreground=self.THEME["action_button_fg"],
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "Action.TButton",
            background=[
                ("pressed", self.THEME["action_button_pressed_bg"]),
                ("active", self.THEME["action_button_active_bg"]),
            ],
            foreground=[
                ("active", self.THEME["action_button_active_fg"]),
            ],
        )

        # ───── 整体背景色 ─────
        bg = self.THEME["window_bg"]
        # ttk widget 的背景跟随 style.configure 的 TFrame / TLabel / TLabelframe
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg)
        style.configure("TLabelframe", background=bg)
        style.configure("TLabelframe.Label", background=bg)

        # ───── 顶部导航栏（6 个按钮平铺，像网页 nav） ─────
        nav_bar = ttk.Frame(self)
        nav_bar.pack(fill="x", side="top")

        # ───── 底部状态栏 ─────
        # 先 pack 底部，让中间 container 自动占据剩余空间
        status_bar = tk.Label(
            self,
            textvariable=self.status_var,
            background=self.THEME["status_bar_bg"],
            foreground=self.THEME["status_bar_fg"],
            font=("SimHei", 10),
            relief="flat",
            anchor="w",
            padx=10,
            pady=6,
        )
        status_bar.pack(fill="x", side="bottom")

        # ───── 中间页面容器 ─────
        # 所有 Page 都 pack 在这个 container 里，切换时 pack_forget/pack
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        # ───── 创建 6 个页面实例 ─────
        page_specs = [
            ("主页 / 数据", HomePage),
            ("数据清洗", CleanerPage),
            ("RFM 分析", RFMPage),
            ("销售分析", SalesPage),
            ("商品分析", ProductPage),
            ("图表总览", OverviewPage),
        ]
        for label, PageClass in page_specs:
            self.pages[label] = PageClass(container, app=self)

        # ───── 创建 6 个导航按钮（填满整行）─────
        # 用 dict 保存每个按钮，切换页面时改对应按钮的 style 实现"高亮当前"
        self.nav_buttons = {}
        for label, _ in page_specs:
            btn = ttk.Button(
                nav_bar,
                text=label,
                command=lambda l=label: self.show_page(l),
                style="Nav.TButton",
            )
            btn.pack(side="left", expand=True, fill="both")
            self.nav_buttons[label] = btn

        # 默认显示首页
        self.show_page("主页 / 数据")

    def show_page(self, label):
        """切换到指定标签的页面，并把对应导航按钮高亮。"""
        # 隐藏当前页面（如果有）
        if self.current_page is not None:
            self.current_page.pack_forget()
        # 显示目标页面
        target = self.pages[label]
        target.pack(fill="both", expand=True)
        self.current_page = target
        # 更新导航按钮高亮状态：当前选中→NavSelected，其他→Nav
        for btn_label, btn in self.nav_buttons.items():
            if btn_label == label:
                btn.configure(style="NavSelected.TButton")
            else:
                btn.configure(style="Nav.TButton")

    def set_status(self, text):
        """统一更新底部状态栏文字。子页面调它。"""
        self.status_var.set(text)


def run():
    """GUI 入口函数。被 run_gui.py 调用。"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()
