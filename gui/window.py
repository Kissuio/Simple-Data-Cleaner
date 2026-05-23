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
        # 顶部导航按钮（6 个标签按钮）
        "nav_button_font": ("SimHei", 14, "bold"),
        "nav_button_padding": (15, 20),
        # 颜色配置（需要先切换到 clam 主题才生效，目前是占位）
        "nav_button_bg": None,       # 例: "#2c3e50"  导航按钮背景
        "nav_button_fg": None,       # 例: "#ffffff"  导航按钮文字
        "nav_button_active_bg": None,  # 例: "#34495e"  鼠标悬停/按下时
        "nav_button_active_fg": None,  # 例: "#ffffff"
        # 各页面里的动作按钮（"选择文件" / "执行分析" 等）
        "action_button_font": ("SimHei", 12),
        "action_button_padding": (20, 12),
        # 是否切换主题（True 才能让上面颜色生效）
        "use_clam_theme": False,
    }
    # ═══════════════════════════════════════════════════════════════════

    def __init__(self):
        super().__init__()
        self.title("RFM 客户分群分析系统")
        self.geometry("1300x900")

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

        # 基础样式：字体 + padding
        style_kwargs = {
            "font": self.THEME["nav_button_font"],
            "padding": self.THEME["nav_button_padding"],
        }
        # 颜色：只有非 None 才传，避免覆盖系统默认
        if self.THEME["nav_button_bg"]:
            style_kwargs["background"] = self.THEME["nav_button_bg"]
        if self.THEME["nav_button_fg"]:
            style_kwargs["foreground"] = self.THEME["nav_button_fg"]
        style.configure("Nav.TButton", **style_kwargs)

        # 鼠标悬停/按下时的颜色（map 而非 configure）
        if self.THEME["nav_button_active_bg"] or self.THEME["nav_button_active_fg"]:
            map_kwargs = {}
            if self.THEME["nav_button_active_bg"]:
                map_kwargs["background"] = [("active", self.THEME["nav_button_active_bg"])]
            if self.THEME["nav_button_active_fg"]:
                map_kwargs["foreground"] = [("active", self.THEME["nav_button_active_fg"])]
            style.map("Nav.TButton", **map_kwargs)

        # ───── 各页面动作按钮样式 ─────
        style.configure(
            "Action.TButton",
            font=self.THEME["action_button_font"],
            padding=self.THEME["action_button_padding"],
        )

        # ───── 顶部导航栏（6 个按钮平铺，像网页 nav） ─────
        nav_bar = ttk.Frame(self)
        nav_bar.pack(fill="x", side="top")

        # ───── 底部状态栏 ─────
        # 先 pack 底部，让中间 container 自动占据剩余空间
        status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding=(8, 4),
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
        for label, _ in page_specs:
            # lambda 默认参数 trick：捕获当前 label，否则所有按钮都指向最后一个
            btn = ttk.Button(
                nav_bar,
                text=label,
                command=lambda l=label: self.show_page(l),
                style="Nav.TButton",
            )
            # side="left" + expand=True + fill="both" → 6 个按钮平分整行宽度
            btn.pack(side="left", expand=True, fill="both")

        # 默认显示首页
        self.show_page("主页 / 数据")

    def show_page(self, label):
        """切换到指定标签的页面。"""
        # 隐藏当前页面（如果有）
        if self.current_page is not None:
            self.current_page.pack_forget()
        # 显示目标页面
        target = self.pages[label]
        target.pack(fill="both", expand=True)
        self.current_page = target

    def set_status(self, text):
        """统一更新底部状态栏文字。子页面调它。"""
        self.status_var.set(text)


def run():
    """GUI 入口函数。被 run_gui.py 调用。"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()
