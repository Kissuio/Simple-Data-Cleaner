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

from pathlib import Path

import customtkinter as ctk
import pandas as pd

from gui.widgets import UI_COLORS as COLORS, chart_group_complete, make_chart_progress
from gui.output_paths import dataset_output_picture_dir


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEACHER_DEMO_DATA_PATH = PROJECT_ROOT / "data" / "online_retail" / "Online Retail.csv"
TEACHER_QUICK_DEMO_TITLE = "教师快速查阅说明"
TEACHER_QUICK_DEMO_GUIDE = """尊敬的老师，您好：

我们设置这个入口，并不是希望替代完整的操作流程，而是考虑到最后验收时，
您可能更希望先直接查看系统最终生成的可视化图像。因此，该按钮会使用内置
Online Retail 数据集，自动建立一份演示状态，并跳转到图表预览页面，
便于您快速检查系统的图像生成结果和分析展示效果。

点击「知道了，开始」后，系统会为您快速跳过以下人工操作步骤：

1. 加载数据
   自动读取项目内置的 Online Retail 主数据集：
   data/online_retail/Online Retail.csv

2. 数据清洗
   自动执行一组适合该数据集的演示清洗：
   · 删除完全重复行
   · 删除关键 RFM 字段为空的记录
   · 清理取消订单及其配对正单
   · 删除数量 ≤ 0、单价 ≤ 0 的异常记录
   · 将交易时间列转换为日期类型

3. 字段映射
   自动确认客户、订单、日期、数量、单价、商品、国家等标准字段。
   其中销售额会根据 Quantity × UnitPrice 自动派生。

4. RFM 分析
   自动完成 R / F / M 计算、均值打分，并生成 8 类客户标签。

5. 图表生成与预览
   自动生成图表总览页的 9 张 PNG 图，并跳转到「图表总览」打开第一张图。

完成后，页面中将呈现：
· 清洗后的 Online Retail 数据状态
· RFM 客户分群结果
· 图表总览中的 9 张可视化图像
· 可继续切换查看的销售、商品与客户分群相关图像

需要说明的是，该入口不会修改原始数据文件，只是在程序运行过程中建立一份
用于快速查阅的演示状态。若需要考察完整交互流程，仍建议按照左侧 6 个步骤
依次操作。
"""
TEACHER_QUICK_DEMO_REMINDER = "尊敬的老师，可点击「教师快速查阅」直接查看图表预览结果。"
TEACHER_STARTUP_NOTICE_TITLE = "教师查阅提示"
TEACHER_STARTUP_NOTICE = """尊敬的老师，您好：

本系统在主页右上角提供了两个查阅入口，您可按需选择：

· 紫色按钮「教师快速查阅」：使用内置 Online Retail 数据集，自动跑完加载、清洗、字段映射、RFM 分析与图表生成，并直接跳转到「图表总览」，便于您先快速查看系统最终产出的图表结果。

· 绿色按钮「新手带练」：使用内置示例数据，在真实页面里一步步带您亲手完成「加载→清洗→映射→RFM→销售→商品→总览」全流程，每一步都会检验是否做到，便于您考察更贴近真实业务数据的完整交互与对不同数据的适配能力。

该提醒仅用于说明入口位置，不会在关闭弹窗后自动开始任何演示。"""
TEACHER_QUICK_DEMO_DONE_TITLE = "教师快速查阅已完成"
TEACHER_QUICK_DEMO_DONE_NOTICE = """尊敬的老师，您好：

系统已通过「教师快速查阅」入口完成 Online Retail 数据的加载、演示清洗、字段映射、RFM 分析与 9 张图表生成，并已跳转到「图表总览」页面。

在这一页，您可以通过右侧图表目录逐张查看可视化结果，也可以使用「导出此图」保存当前图像，或点击「AI 解读」生成面向报告展示的文字解释。

查阅完本页后，请您记得点击左上角「← 返回主页」。主页会集中呈现本次演示的最终状态、流程完成情况与图表预览，便于您从完整项目视角继续查看。"""
TEACHER_QUICK_DEMO_HOME_TITLE = "可以继续体验完整流程"
TEACHER_QUICK_DEMO_HOME_NOTICE = """尊敬的老师，您好：

您已经回到主页。刚才的「教师快速查阅」主要用于让您先看到一次完整产出结果；接下来，您可以从主页选择「加载数据」，选取新的数据文件，亲手体验更完整的数据清洗与分析流程；若希望有人逐步带着操作，也可点绿色按钮「📘 新手带练」，它会用内置示例数据带您一步步走完全流程。

如果希望进一步查看项目设计，请重点观察：数据清洗区是一组可根据数据特征自由组合的工具，执行哪几样、按什么顺序都由您决定；字段映射会决定后续 RFM 与图表分析的口径；图表总览则用于统一查看、导出和解读最终结果。

完成新的数据加载后，您可以根据数据状态选择进入「数据清洗」「RFM 分析」「销售分析」「商品分析」与「图表总览」等模块，继续考察系统在不同数据上的适配能力。"""
STARTUP_STATUS_TEXT = "就绪 - 请选择主页上的「加载数据」开始"


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


# 需要字段映射 + 顶部筛选/摘要条的分析页
ANALYSIS_PAGES = {"RFM 分析", "销售分析", "商品分析", "图表总览"}


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
        # 整体放大界面（含字号），回应「字太小」的反馈；试验值，可调
        ctk.set_widget_scaling(1.12)

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
        # 过程自动提示开关（恒为关）：关=用自己数据时不自动弹清洗/映射说明，
        # 界面清爽。新手教学改由主页「新手带练」用示例数据一步步带练承载；
        # 清洗页/映射窗里的手动「说明」按钮仍可随时点开。保留此变量供软门禁复用。
        self.guided_mode_var = ctk.BooleanVar(value=False)
        # 启动提示每次打开程序只展示一次，与教师快速通道本身分开。
        self.teacher_startup_notice_seen = False
        # 只有从主页右上角紫色按钮进入的自动演示，成功到达图表总览后才消费这个提醒。
        self.teacher_quick_demo_completion_notice_pending = False
        # 只有教师快速通道成功进入图表总览后，下一次回到主页才弹出后续手册提醒。
        self.teacher_quick_demo_home_notice_pending = False

        # ───── 状态栏文本（子页面调 self.app.set_status("...") 更新） ─────
        self.status_var = ctk.StringVar(value=STARTUP_STATUS_TEXT)
        # 分析页顶部「映射摘要条」文本：显示当前文件 / 行数 / 关键字段映射，
        # 便于一眼核对「金额」等是否接错列（防止把销售额错映射到商品编码等数字列）。
        self.mapping_summary_var = ctk.StringVar(value="")

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

        # ───── 映射摘要条（单实例，仅分析页且已映射时显示，由 _refresh_top_bars 控制）─────
        self.mapping_bar = ctk.CTkLabel(
            self,
            textvariable=self.mapping_summary_var,
            fg_color=COLORS["blue_soft"],
            text_color=COLORS["text"],
            font=("SimHei", 11),
            anchor="w",
            corner_radius=0,
            height=26,
        )

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
        self.after(500, self.show_teacher_startup_notice)

    def show_page(self, label):
        """切换到指定页面，并触发 on_show 钩子。

        on_show 由 BasePage 提供：检查前置条件并刷新提示横幅。
        HomePage 也定义了空 on_show，所以这里不用判断类型直接调。
        """
        previous_label = self.current_label
        target = self.pages[label]
        show_teacher_home_notice = self.should_show_teacher_quick_demo_home_notice(previous_label, label)

        if self.current_page is not None:
            self.current_page.pack_forget()

        target.pack(fill="both", expand=True)
        self.current_page = target
        self.current_label = label

        target.on_show()

        # 顶部条（映射摘要 + 全局筛选）：仅分析页且已映射时显示
        self._refresh_top_bars()

        # 方案 B：进入分析页时若已清洗但尚未映射字段，弹出字段映射对话框。
        # 放在 on_show / 顶部条之后，让页面先以「等待映射」状态铺好，再叠加模态弹窗。
        if label in ANALYSIS_PAGES and self.needs_mapping():
            self.open_field_mapping()

        if show_teacher_home_notice:
            self.after(120, self.show_teacher_quick_demo_home_notice)

    def set_status(self, text):
        """统一更新底部状态栏文字。子页面调它。"""
        self.status_var.set(text)

    def output_picture_dir(self):
        """返回当前数据集对应的图表输出文件夹。"""
        file_path = getattr(self.loader, "file_path", None) if self.loader is not None else None
        return dataset_output_picture_dir(file_path, base_dir=PROJECT_ROOT / "output")

    def get_visualizer(self):
        """返回写入当前数据集专属图片文件夹的 Visualizer。"""
        from visualization.visualizer import Visualizer

        output_dir = self.output_picture_dir()
        current_dir = getattr(self.visualizer, "output_dir", None)
        if self.visualizer is None or Path(current_dir) != output_dir:
            self.visualizer = Visualizer(output_dir=output_dir)
        return self.visualizer

    def start_guided_tour(self):
        """新手带练：用内置示例数据，在真实页面上一步步带着走完整流程。

        与「教师快速查阅」（一键自动跑完只看结果）不同，这里逐步停下来讲解、
        由用户点「执行这一步」推进，面向第一次使用的学生。
        """
        from gui.guided_tour import GuidedTour

        # 已经打开则置前，不重复开
        existing = getattr(self, "_guided_tour", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return
        self._guided_tour = GuidedTour(self)

    def show_teacher_startup_notice(self):
        """启动时提示教师先体验快速查阅入口，但不自动执行演示。"""
        if self.teacher_startup_notice_seen:
            return
        self.teacher_startup_notice_seen = True

        from gui.intro_dialog import IntroDialog

        IntroDialog(
            self,
            title=TEACHER_STARTUP_NOTICE_TITLE,
            body=TEACHER_STARTUP_NOTICE,
            button_text="我知道了",
        )

    def mark_teacher_quick_demo_from_purple_entry(self):
        """记录教师快速查阅由主页紫色入口启动。"""
        self.teacher_startup_notice_seen = True
        self.teacher_quick_demo_completion_notice_pending = True
        self.teacher_quick_demo_home_notice_pending = False

    def should_show_teacher_quick_demo_completion_notice(self):
        """若教师快速查阅完成提醒处于待显示状态，则消费并返回 True。"""
        if not self.teacher_quick_demo_completion_notice_pending:
            return False
        self.teacher_quick_demo_completion_notice_pending = False
        return True

    def cancel_teacher_quick_demo_completion_notice(self):
        """取消教师快速查阅完成提醒，避免失败流程后残留弹窗状态。"""
        self.teacher_quick_demo_completion_notice_pending = False
        self.teacher_quick_demo_home_notice_pending = False

    def show_teacher_quick_demo_completion_notice(self):
        """教师快速查阅成功到达图表总览后，提醒教师本页用途与返回主页。"""
        if not self.should_show_teacher_quick_demo_completion_notice():
            return
        self.teacher_quick_demo_home_notice_pending = True

        from gui.intro_dialog import IntroDialog

        IntroDialog(
            self,
            title=TEACHER_QUICK_DEMO_DONE_TITLE,
            body=TEACHER_QUICK_DEMO_DONE_NOTICE,
            button_text="知道了，继续查看",
        )

    def should_show_teacher_quick_demo_home_notice(self, previous_label, next_label):
        """仅在教师快速通道完成后，第一次从非主页回到主页时消费后续提醒。"""
        if not self.teacher_quick_demo_home_notice_pending:
            return False
        if previous_label not in (None, "主页") and next_label == "主页":
            self.teacher_quick_demo_home_notice_pending = False
            return True
        return False

    def show_teacher_quick_demo_home_notice(self):
        """教师快速通道完成后回到主页，提示继续按手册选择数据分析。"""
        from gui.intro_dialog import IntroDialog

        IntroDialog(
            self,
            title=TEACHER_QUICK_DEMO_HOME_TITLE,
            body=TEACHER_QUICK_DEMO_HOME_NOTICE,
            on_close=self.reset_teacher_quick_demo_state_for_manual_start,
            button_text="知道了，继续体验",
        )

    def reset_teacher_quick_demo_state_for_manual_start(self):
        """关闭教师通道最终提示后，清空演示流程占用的内存状态。"""
        self.loader = None
        self.cleaner = None
        self.rfm_analyzer = None
        self.rfm_df = None
        self.visualizer = None
        self.cleaning_history = []
        self.chart_progress = make_chart_progress()
        self.reset_data_filter()
        self.field_mapping = None
        self.mapping_intro_seen = False
        self.cleaning_intro_seen = False
        self.teacher_quick_demo_completion_notice_pending = False
        self.teacher_quick_demo_home_notice_pending = False

        if "mapping_summary_var" in self.__dict__:
            self.mapping_summary_var.set("")
        refresh_top_bars = getattr(self, "_refresh_top_bars", None)
        if callable(refresh_top_bars):
            refresh_top_bars()
        current_page = getattr(self, "current_page", None)
        if current_page is not None:
            current_page.on_show()
        set_status = getattr(self, "set_status", None)
        if callable(set_status):
            set_status(STARTUP_STATUS_TEXT)

    def open_teacher_quick_demo_intro(self):
        """打开教师快速查阅说明；用户确认后自动跑完整演示流程。"""
        self.mark_teacher_quick_demo_from_purple_entry()

        from gui.intro_dialog import IntroDialog

        IntroDialog(
            self,
            title=TEACHER_QUICK_DEMO_TITLE,
            body=TEACHER_QUICK_DEMO_GUIDE,
            on_close=self.run_teacher_quick_demo,
        )

    def run_teacher_quick_demo(self):
        """加载 Online Retail，自动清洗、映射、RFM、生成图表并跳到总览页。"""
        from tkinter import messagebox

        from analyzer.rfm_analyzer import RFMAnalyzer
        from data_handlers.data_cleaner import DataCleaner
        from data_handlers.field_mapping import guess_mapping
        from data_handlers.file_loader import FileLoader
        from gui.error_messages import show_friendly_error

        path = TEACHER_DEMO_DATA_PATH
        if not path.exists():
            self.cancel_teacher_quick_demo_completion_notice()
            messagebox.showwarning(
                "演示数据不存在",
                f"未找到教师快速查阅使用的数据文件：\n{path}\n\n"
                "请先确认 data/online_retail/Online Retail.csv 是否存在。",
                parent=self,
            )
            return

        try:
            self.set_status("教师快速查阅：正在加载 Online Retail 数据...")
            self.update_idletasks()

            loader = FileLoader(str(path))
            loader.load_file()

            self.loader = loader
            self.cleaner = None
            self.rfm_analyzer = None
            self.rfm_df = None
            self.visualizer = None
            self.chart_progress = make_chart_progress()
            self.reset_data_filter()
            self.field_mapping = None
            self.mapping_intro_seen = True
            self.cleaning_intro_seen = True

            self.set_status("教师快速查阅：正在执行演示清洗...")
            self.update_idletasks()

            cleaner = DataCleaner(loader.df)
            cleaner.drop_duplicates()
            cleaner.drop_missing([
                "CustomerID",
                "InvoiceNo",
                "InvoiceDate",
                "Quantity",
                "UnitPrice",
            ])
            cleaner.drop_cancellation_pairs(
                invoice_col="InvoiceNo",
                customer_col="CustomerID",
                code_col="StockCode",
                price_col="UnitPrice",
                qty_col="Quantity",
                prefix="C",
            )
            cleaner.drop_by_range("Quantity", "<=", 0)
            cleaner.drop_by_range("UnitPrice", "<=", 0)
            cleaner.convert_date("InvoiceDate")
            self.cleaner = cleaner

            self.set_status("教师快速查阅：正在确认字段映射并计算 RFM...")
            self.update_idletasks()

            self.field_mapping = guess_mapping(cleaner.df.columns)
            self.rfm_analyzer = RFMAnalyzer(self.get_active_df())
            self.rfm_df = self.rfm_analyzer.analyze_all()

            self.set_status("教师快速查阅：正在生成 9 张图表...")
            self.show_page("图表总览")
            self.update_idletasks()
            overview = self.pages.get("图表总览")
            if overview is not None:
                overview._on_generate_all()
            if not chart_group_complete(self, "overview"):
                self.cancel_teacher_quick_demo_completion_notice()
                self.set_status("教师快速查阅：清洗和 RFM 已完成，但图表未全部生成，请查看提示后重试。")
                return
            self.set_status(
                f"教师快速查阅完成：已清洗 {len(self.cleaner.df):,} 行数据，"
                f"生成 {len(self.rfm_df):,} 个客户的 RFM 结果，并打开图表总览。"
            )
            self.after(100, self.show_teacher_quick_demo_completion_notice)
        except Exception as e:
            self.cancel_teacher_quick_demo_completion_notice()
            show_friendly_error("教师快速查阅失败", e, "自动完成演示流程", parent=self)

    def mapping_summary_text(self):
        """生成顶部「映射摘要条」文字：当前文件 · 行数 · 客户/订单/日期/金额来源。

        金额来源专门标清——映射对了是「数量×单价(自动)」或某总价列，
        若误把销售额接到商品编码/订单号等数字列，在这里一眼可见。
        """
        if not self.field_mapping or self.cleaner is None or self.cleaner.df is None:
            return ""
        m = self.field_mapping
        fname = "未知文件"
        if self.loader is not None:
            path = getattr(self.loader, "file_path", "") or ""
            fname = path.replace("\\", "/").split("/")[-1] or "未知文件"
        rows = len(self.cleaner.df)
        if m.get("TotalPrice"):
            money = f"金额={m['TotalPrice']}"
        elif m.get("Quantity") and m.get("UnitPrice"):
            money = f"金额={m['Quantity']}×{m['UnitPrice']}(自动)"
        else:
            money = "金额=未设"
        return (
            f"📄 {fname} · {rows:,} 行   ｜   "
            f"客户={m.get('CustomerID', '-')}   订单={m.get('InvoiceNo', '-')}   "
            f"日期={m.get('InvoiceDate', '-')}   {money}"
        )

    def _refresh_top_bars(self):
        """按「当前页是否分析页 + 是否已映射」显隐顶部的映射摘要条与全局筛选栏。"""
        if "filter_bar" not in self.__dict__ or "mapping_bar" not in self.__dict__:
            return
        if self.current_label in ANALYSIS_PAGES and self.is_mapped():
            self.filter_bar.refresh_options()
            self.filter_bar.show()
            self.mapping_summary_var.set(self.mapping_summary_text())
            if not self.mapping_bar.winfo_ismapped():
                # 放在筛选栏上方
                self.mapping_bar.pack(side="top", fill="x", before=self.filter_bar)
        else:
            self.filter_bar.hide()
            if self.mapping_bar.winfo_ismapped():
                self.mapping_bar.pack_forget()

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
            # 未映射时返回全部所需字段；元组「其中之一即可」转成 A|B 供中文提示使用。
            return ["|".join(c) if isinstance(c, tuple) else c
                    for c in ANALYSIS_REQUIRED.get(kind, [])]
        return missing_required_fields(df.columns, kind)

    # 各分析需要「是数值」的列（日期单独判断）
    _NUMERIC_NEEDS = {
        "rfm": ["TotalPrice"],
        "sales": ["TotalPrice"],
        "product": ["Quantity", "UnitPrice", "TotalPrice"],
        "overview": ["Quantity", "UnitPrice", "TotalPrice"],
    }
    _DATE_NEEDS = {"rfm", "sales", "overview"}

    def type_guidance(self, kind):
        """进入某分析前检查关键列类型是否就绪；未就绪返回一段「分步导向」中文提示，否则 None。

        方案 B 下清洗用原始列、类型转换由用户在清洗页手动做。日期还是文本时 RFM/趋势会
        算不出（报底层错），这里在分析入口提前拦一道，用「去哪点、点什么」的两步指引代替报错。
        """
        import pandas as pd
        df = self.get_active_df()
        if df is None:
            return None
        if kind in self._DATE_NEEDS and "InvoiceDate" in df.columns \
                and not pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
            return (
                "「交易时间」列现在还是文本，时间相关分析无法进行。\n\n"
                "请按两步处理：\n"
                "1）打开【数据清洗】页\n"
                "2）点「转换列类型 …」→ 选「列转日期」→ 选你的交易时间列 → 确认\n\n"
                "完成后回到本页再点一次即可。"
            )
        for col, cn in (("Quantity", "数量"), ("UnitPrice", "单价"), ("TotalPrice", "销售额")):
            if col in self._NUMERIC_NEEDS.get(kind, []) and col in df.columns \
                    and not pd.api.types.is_numeric_dtype(df[col]):
                return (
                    f"「{cn}」列现在还是文本，金额无法计算。\n\n"
                    "请按两步处理：\n"
                    "1）打开【数据清洗】页\n"
                    "2）点「转换列类型 …」→ 选「列转数值」→ 选相关列 → 确认\n\n"
                    "完成后回到本页再点一次即可。"
                )
        return None

    def require_types_ready(self, kind):
        """类型就绪则 True；否则弹「分步导向」提示（可一键跳到数据清洗页）并返回 False。"""
        guide = self.type_guidance(kind)
        if not guide:
            return True
        from tkinter import messagebox
        go = messagebox.askyesno("需要先转换列类型", guide + "\n\n现在就去【数据清洗】页吗？")
        if go:
            self.show_page("数据清洗")
        return False

    def open_field_mapping(self, show_intro=True):
        """打开字段映射；每份数据首次进入时先展示 RFM 使用说明。

        参数:
            show_intro: 是否允许展示首次说明。顶部“字段映射”用于调整已有映射时
                传 False，直接进入映射界面。
        """
        if self.cleaner is None or self.cleaner.df is None:
            return

        if show_intro and self.guided_mode_var.get() and not self.mapping_intro_seen:
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
        # 映射后分析页才需要顶部条：刷新映射摘要 + 筛选栏并显示
        self._refresh_top_bars()
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
