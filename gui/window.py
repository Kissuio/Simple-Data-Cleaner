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
import pandas as pd

from gui.widgets import UI_COLORS as COLORS, make_chart_progress


RFM_MAPPING_GUIDE = """一、RFM 是什么

RFM 是一种按客户交易行为进行价值分群的方法：

R · Recency（最近消费）
客户距离最近一次消费过去了多少天。数值越小，说明客户越活跃。

F · Frequency（消费频次）
客户产生过多少个不同订单。数值越大，说明购买越频繁。

M · Monetary（消费金额）
客户累计贡献的销售额。数值越大，说明客户价值通常越高。

本系统以当前筛选数据中的最后交易日 + 1 天作为观察日期，并根据 R、F、M
相对均值的高低组合，将客户分为重要价值、重要保持、重要发展等 8 类。


二、推荐使用流程

1. 加载 CSV 或 Excel 文件。
2. 在「数据清洗」中处理空值、重复记录、取消订单、异常数量和日期格式。
3. 在下一页完成字段映射，把你表中的列告诉系统。
4. 进入「RFM 分析」生成客户分群；销售和商品页可继续生成趋势与榜单。
5. 顶部可以按年月或国家筛选。筛选改变后，需要重新生成 RFM 和图表。


三、字段映射怎么选

RFM 核心字段：

· CustomerID：客户或会员的唯一编号，不能选商品编号。
· InvoiceNo：订单号。同一订单的多个商品明细通常共用一个订单号。
· InvoiceDate：交易或下单时间。清洗时应先转换为日期。
· TotalPrice：每条交易明细的销售额。

如果表中没有销售额列，可以同时映射：

· Quantity：购买数量
· UnitPrice：商品单价

系统会自动计算 TotalPrice = Quantity × UnitPrice。

商品分析还建议映射 Description（商品名称）和 StockCode（商品编码）；
Country（国家/地区）用于顶部地域筛选，没有时可以不映射。


四、映射操作提示

· 下拉框已经根据列名自动给出建议，请结合右侧样例值核对。
· 自动建议不一定正确，尤其要区分客户编号、订单号和商品编号。
· 表中确实不存在的可选字段可以选择「不映射」。
· 确认后不会修改原始文件，只会告诉分析模块每一列的含义。
"""


def make_data_filter():
    """返回一份未启用任何条件的全局筛选状态。"""
    return {"date_from": None, "date_to": None, "country": None}


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

        # ═══ 各页面动作按钮（如「派生新列」「查看月度趋势」） ═══
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
        # 启动即最大化：窗口过小会让仪表盘/图表布局拥挤变形，最大化后铺满屏幕
        # 用 after 延迟调用更稳妥（customtkinter 缩放在窗口建好后再 zoomed）
        self.after(0, lambda: self.state("zoomed"))

        # ───── 共享数据对象（子页面通过 self.app.xxx 访问） ─────
        self.loader = None
        self.cleaner = None
        self.rfm_analyzer = None
        self.rfm_df = None
        self.visualizer = None
        self.cleaning_history = []
        self.chart_progress = make_chart_progress()
        # 全局数据筛选条件（作用于「清洗后数据」之上，各分析页通过 get_active_df 取数）。
        # None 表示该维度不筛选；date_from/date_to 为 pandas.Timestamp，country 为国家名。
        self.data_filter = make_data_filter()
        # 字段映射（方案 B：标准化推迟到「进入分析前」才做）。None=尚未映射；
        # 确认映射后存 {标准字段: 实际列名}，get_active_df 据此把清洗后数据
        # 重命名成标准列名、并按需派生 TotalPrice。
        self.field_mapping = None
        # 每份新数据首次映射前展示一次 RFM 与操作说明；手动重映射时不重复弹。
        self.mapping_intro_seen = False
        # 每份新数据首次进入清洗页展示一次工具箱说明。
        self.cleaning_intro_seen = False

        # ───── 状态栏文本（子页面调 self.app.set_status("...") 更新） ─────
        self.status_var = ctk.StringVar(value="就绪 - 请选择主页上的「加载数据」开始")

        # ───── 当前显示的页面 + 全部页面字典 ─────
        self.current_page = None
        self.current_label = None
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

        # ───── 顶部全局筛选栏（单实例，仅分析页显示，由 show_page 控制显隐）─────
        # 延迟 import 避免循环依赖
        from gui.filter_bar import FilterBar
        self.filter_bar = FilterBar(self, app=self)

        # ───── 中间页面容器 ─────
        # fg_color=transparent 让 container 跟随窗口默认色（light 模式下浅冷白）
        self.container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.container.pack(fill="both", expand=True)

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
            self.pages[label] = PageClass(self.container, app=self)

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
        self.current_label = label

        target.on_show()

        # 仅分析页、且已清洗 + 已做字段映射时显示全局筛选栏；其余页隐藏。
        # 方案 B：映射后 get_active_df 才有 InvoiceDate / Country 等标准列供筛选，
        # 未映射时筛选栏没有可用候选，故一并隐藏。
        analysis_pages = {"RFM 分析", "销售分析", "商品分析", "图表总览"}
        if label in analysis_pages and self.is_mapped():
            self.filter_bar.refresh_options()
            self.filter_bar.show()
        else:
            self.filter_bar.hide()

        # 方案 B：进入分析页时若已清洗但尚未映射字段，弹出字段映射对话框。
        # 放在 on_show / 筛选栏之后，让页面先以「等待映射」状态铺好，再叠加模态弹窗。
        if label in analysis_pages and self.needs_mapping():
            self.open_field_mapping()

    def set_status(self, text):
        """统一更新底部状态栏文字。子页面调它。"""
        self.status_var.set(text)

    # ═══════════════════════════════════════════════════════════════════
    # 字段映射（方案 B：进入分析前才把列对应到标准字段）
    # ═══════════════════════════════════════════════════════════════════
    def is_mapped(self):
        """是否已完成字段映射（分析所需标准列名是否可用）。"""
        return bool(self.field_mapping)

    def needs_mapping(self):
        """已清洗但还没做字段映射 —— 进入分析前需要先映射。"""
        return (
            self.cleaner is not None
            and self.cleaner.df is not None
            and not self.field_mapping
        )

    def mapped_clean_df(self):
        """清洗后数据套用字段映射（不含全局筛选），供需要标准列名的地方取数。

        - 未清洗或未映射 → None（调用方据此显示「等待映射」，不要去读标准列）；
        - 已映射 → 重命名为标准列名并按需派生 TotalPrice 的新 df。
        """
        if self.cleaner is None or self.cleaner.df is None or not self.field_mapping:
            return None
        from data_handlers.field_mapping import apply_field_mapping
        return apply_field_mapping(self.cleaner.df, self.field_mapping)

    def missing_fields_for(self, kind):
        """某分析（rfm/sales/product/overview）还缺哪些标准列（软门禁逐页校验）。

        未映射 → 返回该分析所需的全部字段；已映射 → 返回映射/派生后仍缺的字段。
        TotalPrice 由 get_active_df 自动派生，故直接看其输出列即可。
        """
        from data_handlers.field_mapping import ANALYSIS_REQUIRED, missing_required_fields
        df = self.get_active_df()
        if df is None:
            return list(ANALYSIS_REQUIRED.get(kind, []))
        return missing_required_fields(df.columns, kind)

    def open_field_mapping(self, show_intro=True):
        """打开字段映射；每份数据首次进入时先展示 RFM 使用说明。

        参数:
            show_intro: 是否允许展示首次说明。顶部“字段映射”用于调整已有映射时
                传 False，直接进入映射界面。
        """
        if self.cleaner is None or self.cleaner.df is None:
            return

        if show_intro and not self.mapping_intro_seen:
            from gui.intro_dialog import IntroDialog
            self.mapping_intro_seen = True
            IntroDialog(
                self,
                title="开始分析前：认识 RFM 与字段映射",
                body=RFM_MAPPING_GUIDE,
                on_close=lambda: self.open_field_mapping(show_intro=False),
            )
            return

        from gui.mapping_dialog import MappingDialog
        MappingDialog(
            self,
            self.cleaner.df,
            on_confirm=self._on_field_mapping_confirmed,
            current_mapping=self.field_mapping,
            guide_title="RFM 与字段映射说明",
            guide_body=RFM_MAPPING_GUIDE,
        )

    def _on_field_mapping_confirmed(self, mapping):
        """字段映射确认回调：保存映射、清空下游、刷新当前页与筛选栏。"""
        self.field_mapping = mapping
        # 日期列或国家列的来源可能已改变，旧筛选条件不能继续沿用。
        self.reset_data_filter()
        # 映射变化意味着分析口径变了 —— 已算的 RFM 与已生成的图都失效
        self.rfm_analyzer = None
        self.rfm_df = None
        self.chart_progress = make_chart_progress()
        if self.current_page is not None:
            self.current_page.on_show()
        # 映射后分析页才需要筛选栏：刷新候选并显示
        analysis_pages = {"RFM 分析", "销售分析", "商品分析", "图表总览"}
        if self.current_label in analysis_pages:
            self.filter_bar.refresh_options()
            self.filter_bar.show()
        self.set_status("字段映射已确认，可以开始分析")

    def get_active_df(self):
        """返回「清洗后数据」套用全局筛选后的结果，供各分析页统一取数。

        - 未清洗 → None
        - 无筛选 → 直接返回 cleaner.df（不复制，省内存）
        - 有筛选 → 返回按日期 / 国家过滤后的子集
        """
        if self.cleaner is None or self.cleaner.df is None:
            return None
        df = self.cleaner.df
        # 方案 B：把进入分析前确认的字段映射，套到清洗后数据上——
        # 重命名成标准列名并按需派生 TotalPrice；未映射(None)时原样返回，向后兼容。
        if self.field_mapping:
            from data_handlers.field_mapping import apply_field_mapping
            df = apply_field_mapping(df, self.field_mapping)
        f = self.data_filter
        if not any(v is not None for v in f.values()):
            return df

        mask = pd.Series(True, index=df.index)
        if f.get("date_from") is not None and "InvoiceDate" in df.columns:
            mask &= df["InvoiceDate"] >= f["date_from"]
        if f.get("date_to") is not None and "InvoiceDate" in df.columns:
            mask &= df["InvoiceDate"] <= f["date_to"]
        if f.get("country") and "Country" in df.columns:
            mask &= df["Country"] == f["country"]
        return df[mask]

    def reset_data_filter(self):
        """清空日期与国家筛选，不主动刷新页面或修改分析结果。"""
        self.data_filter = make_data_filter()

    def set_data_filter(self, date_from=None, date_to=None, country=None):
        """更新全局筛选条件，清空下游结果并刷新当前页。

        筛选一变，已算的 RFM 结果和已生成的图都失效，
        因此清空 rfm_analyzer / rfm_df / 图进度，让用户在新筛选下重新生成。
        """
        self.data_filter = {
            "date_from": date_from, "date_to": date_to, "country": country
        }
        self.rfm_analyzer = None
        self.rfm_df = None
        self.chart_progress = make_chart_progress()
        if self.current_page is not None:
            self.current_page.on_show()


def run():
    """GUI 入口函数。被 main.py 调用。"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()
