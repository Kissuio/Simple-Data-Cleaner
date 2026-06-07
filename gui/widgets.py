"""可复用 UI 组件工具模块。

目前提供：
    build_table(parent, columns, rows) —— 用 customtkinter 拼一个简单表格
    build_workflow_nav(...) / refresh_workflow_nav(...) —— 统一左侧流程导航
    MetricCard —— 统一指标卡片

为什么需要：
    customtkinter 没有原生表格控件（不像 ttk 有 Treeview）。
    项目里多页都需要表格、指标卡和流程导航，统一在这里实现一份，
    避免每页面重复写"循环 CTkLabel + grid 布局"和状态刷新代码。
"""

import customtkinter as ctk


UI_COLORS = {
    "page_bg": "#f5f7fb",
    "panel_bg": "#ffffff",
    "panel_soft": "#f8fafc",
    "border": "#b8c4d6",
    "text": "#1f2937",
    "muted": "#64748b",
    "blue": "#2563eb",
    "blue_hover": "#3b82f6",
    "blue_soft": "#eff6ff",
    "green": "#10b981",
    "green_hover": "#34d399",
    "green_soft": "#ecfdf5",
    "amber": "#f59e0b",
    "amber_soft": "#fffbeb",
    "red": "#ef4444",
    "red_soft": "#fef2f2",
    "purple": "#8b5cf6",
    "purple_hover": "#a78bfa",
    "purple_soft": "#f5f3ff",
    "gray": "#64748b",
    "gray_hover": "#94a3b8",
}

BORDER_WIDTH = 2

NAV_STEPS = [
    ("01", "加载数据", "加载数据"),
    ("02", "数据清洗", "数据清洗"),
    ("03", "RFM 分群", "RFM 分析"),
    ("04", "销售分析", "销售分析"),
    ("05", "商品分析", "商品分析"),
    ("06", "图表总览", "图表总览"),
]

SALES_CHART_KEYS = {"monthly_trend", "weekday_hour_heatmap"}
PRODUCT_CHART_KEYS = {"top_quantity", "top_revenue", "price_distribution"}
OVERVIEW_CHART_KEYS = {
    "label_pie",
    "label_avg_spend",
    "rfm_scatter",
    "monthly_trend",
    "top_quantity",
    "top_revenue",
    "price_distribution",
    "weekday_hour_heatmap",
    "month_heatmap",
}

REQUIRED_CHART_PROGRESS = {
    "sales": SALES_CHART_KEYS,
    "product": PRODUCT_CHART_KEYS,
    "overview": OVERVIEW_CHART_KEYS,
}


def make_chart_progress():
    """创建 GUI 层图表生成进度，不依赖 output 目录里的旧文件。"""
    return {group: set() for group in REQUIRED_CHART_PROGRESS}


def ensure_chart_progress(app):
    progress = getattr(app, "chart_progress", None)
    if progress is None:
        progress = make_chart_progress()
        app.chart_progress = progress

    for group in REQUIRED_CHART_PROGRESS:
        value = progress.setdefault(group, set())
        if not isinstance(value, set):
            progress[group] = set(value)
    return progress


def mark_chart_progress(app, group, keys):
    progress = ensure_chart_progress(app)
    if isinstance(keys, str):
        keys = {keys}
    progress.setdefault(group, set()).update(keys)


def reset_chart_progress(app, groups=None):
    progress = ensure_chart_progress(app)
    targets = groups or REQUIRED_CHART_PROGRESS.keys()
    for group in targets:
        progress.setdefault(group, set()).clear()


def chart_group_complete(app, group):
    required = REQUIRED_CHART_PROGRESS[group]
    generated = ensure_chart_progress(app).get(group, set())
    return required.issubset(generated)


class WorkflowNavItem(ctk.CTkFrame):
    """左侧流程导航项。"""

    def __init__(self, parent, number, title, target, app, active=False):
        bg = UI_COLORS["blue_soft"] if active else UI_COLORS["panel_bg"]
        border = UI_COLORS["blue"] if active else UI_COLORS["border"]
        super().__init__(
            parent,
            fg_color=bg,
            border_color=border,
            border_width=BORDER_WIDTH,
            corner_radius=8,
            cursor="hand2",
        )
        self.app = app
        self.target = target
        self.active = active
        self.default_bg = bg
        self.default_border = border
        self.grid_columnconfigure(1, weight=1)

        self.number_label = ctk.CTkLabel(
            self,
            text=number,
            width=30,
            height=30,
            fg_color=UI_COLORS["blue"] if active else UI_COLORS["panel_soft"],
            text_color="#ffffff" if active else UI_COLORS["blue"],
            font=("Microsoft YaHei UI", 10, "bold"),
            corner_radius=6,
        )
        self.number_label.grid(row=0, column=0, padx=(10, 8), pady=9)

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=("SimHei", 12, "bold"),
            text_color=UI_COLORS["blue"] if active else UI_COLORS["text"],
            anchor="w",
        )
        self.title_label.grid(row=0, column=1, sticky="ew", pady=9)

        self.status_label = ctk.CTkLabel(
            self,
            text="当前" if active else "未开始",
            width=58,
            height=24,
            fg_color=UI_COLORS["blue_soft"] if active else UI_COLORS["panel_soft"],
            text_color=UI_COLORS["blue"] if active else UI_COLORS["muted"],
            font=("SimHei", 10, "bold"),
            corner_radius=6,
        )
        self.status_label.grid(row=0, column=2, padx=(8, 10), pady=9)

        for widget in [self, self.number_label, self.title_label, self.status_label]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.configure(cursor="hand2")

    def set_state(self, state, active=False):
        self.active = active
        styles = {
            "loaded": ("已导入", UI_COLORS["green"], UI_COLORS["green_soft"]),
            "loading": ("导入中", UI_COLORS["blue"], UI_COLORS["blue_soft"]),
            "failed": ("失败", UI_COLORS["red"], UI_COLORS["red_soft"]),
            "done": ("已完成", UI_COLORS["green"], UI_COLORS["green_soft"]),
            "current": ("当前", UI_COLORS["blue"], UI_COLORS["blue_soft"]),
            "ready": ("下一步", UI_COLORS["blue"], UI_COLORS["blue_soft"]),
            "available": ("可查看", UI_COLORS["green"], UI_COLORS["green_soft"]),
            "pending": ("未开始", UI_COLORS["muted"], UI_COLORS["panel_soft"]),
        }
        text, color, soft = styles[state]
        if active:
            self.default_bg = UI_COLORS["blue_soft"]
            self.default_border = UI_COLORS["blue"]
            number_bg = UI_COLORS["blue"]
            number_fg = "#ffffff"
            title_color = UI_COLORS["blue"]
        else:
            self.default_bg = UI_COLORS["panel_bg"]
            self.default_border = color if state in ("loaded", "done", "available") else UI_COLORS["border"]
            number_bg = UI_COLORS["panel_soft"]
            number_fg = color if state != "pending" else UI_COLORS["blue"]
            title_color = UI_COLORS["text"]

        self.configure(fg_color=self.default_bg, border_color=self.default_border)
        self.number_label.configure(fg_color=number_bg, text_color=number_fg)
        self.title_label.configure(text_color=title_color)
        self.status_label.configure(text=text, fg_color=soft, text_color=color)

    def _on_click(self, event):
        self.app.show_page(self.target)

    def _on_enter(self, event):
        self.configure(fg_color=UI_COLORS["blue_soft"], border_color=UI_COLORS["blue"])
        self.title_label.configure(text_color=UI_COLORS["blue"])

    def _on_leave(self, event):
        self.configure(fg_color=self.default_bg, border_color=self.default_border)
        self.title_label.configure(
            text_color=UI_COLORS["blue"] if self.active else UI_COLORS["text"]
        )


class MetricCard(ctk.CTkFrame):
    """统一指标卡。"""

    def __init__(self, parent, title, value_var, note_var, accent):
        super().__init__(
            parent,
            fg_color=UI_COLORS["panel_bg"],
            border_color=UI_COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=("SimHei", 10, "bold"),
            text_color=UI_COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            self,
            textvariable=value_var,
            font=("Microsoft YaHei UI", 21, "bold"),
            text_color=UI_COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=14)

        ctk.CTkLabel(
            self,
            textvariable=note_var,
            font=("SimHei", 10),
            text_color=accent,
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 12))


def build_workflow_nav(parent, app, active_target, nav_items):
    """构建统一左侧流程导航。"""
    nav = ctk.CTkFrame(
        parent,
        fg_color=UI_COLORS["panel_bg"],
        border_color=UI_COLORS["border"],
        border_width=BORDER_WIDTH,
        corner_radius=8,
        width=280,
    )
    nav.grid_propagate(False)
    nav.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        nav,
        text="项目流程",
        font=("SimHei", 16, "bold"),
        text_color=UI_COLORS["text"],
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", padx=16, pady=(18, 4))

    ctk.CTkLabel(
        nav,
        text="当前页面会以蓝色高亮",
        font=("SimHei", 10),
        text_color=UI_COLORS["muted"],
        anchor="w",
    ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

    last_row = 1
    for row, (number, title, target) in enumerate(NAV_STEPS, start=2):
        item = WorkflowNavItem(
            nav,
            number=number,
            title=title,
            target=target,
            app=app,
            active=target == active_target,
        )
        item.grid(row=row, column=0, sticky="ew", padx=12, pady=4)
        nav_items[target] = item
        last_row = row

    # 弹性空白行把底部按钮推到最下，利用流程项排完后的空白处
    nav.grid_rowconfigure(last_row + 1, weight=1)
    analyze_btn = ctk.CTkButton(
        nav,
        text="分析本页 · 生成提示词",
        command=lambda: _open_analyze(app, active_target),
        fg_color=UI_COLORS["amber"],
        hover_color=UI_COLORS.get("amber_hover", UI_COLORS["amber"]),
        text_color="#ffffff",
        font=("SimHei", 12, "bold"),
        height=38,
        corner_radius=6,
    )
    analyze_btn.grid(row=last_row + 2, column=0, sticky="ew", padx=12, pady=(8, 14))

    return nav


def _open_analyze(app, target):
    """打开「分析本页」提示词弹窗（延迟 import 以避免与 analyze_dialog 循环导入）。"""
    from gui.analyze_dialog import AnalyzeDialog
    AnalyzeDialog(app, app, target)


def refresh_workflow_nav(nav_items, app, active_target, load_state=None):
    """统一刷新左侧流程状态。"""
    if not nav_items:
        return

    loader_ok = app.loader is not None and app.loader.df is not None
    # 方案 B：清洗完成只看「有清洗后数据」，TotalPrice 等标准列在分析前的映射环节才出现
    cleaner_ok = app.cleaner is not None and app.cleaner.df is not None
    rfm_ok = app.rfm_df is not None and "Label" in app.rfm_df.columns
    sales_done = cleaner_ok and chart_group_complete(app, "sales")
    product_done = cleaner_ok and chart_group_complete(app, "product")
    overview_done = cleaner_ok and rfm_ok and chart_group_complete(app, "overview")

    for _, _, target in NAV_STEPS:
        active = target == active_target
        if active:
            if target == "加载数据" and load_state is not None:
                state = load_state
            elif target == "加载数据" and loader_ok:
                state = "loaded"
            else:
                state = "current"
        elif target == "加载数据":
            state = "loaded" if loader_ok else "pending"
        elif target == "数据清洗":
            state = "done" if cleaner_ok else "pending"
        elif target == "RFM 分析":
            state = "done" if rfm_ok else "pending"
        elif target == "销售分析":
            state = "done" if sales_done else "pending"
        elif target == "商品分析":
            state = "done" if product_done else "pending"
        else:
            state = "done" if overview_done else "pending"

        nav_items[target].set_state(state, active=active)


# 表格颜色（与 home_page 的 Card 类风格保持一致）
HEADER_BG = "#dfe4ea"           # 表头浅灰底
HEADER_FG = "#2c3e50"           # 表头深蓝灰字
ROW_BG_ODD = "#ffffff"          # 奇数行白底
ROW_BG_EVEN = "#f8f9fa"         # 偶数行更浅灰（交替条纹）
TEXT_COLOR = "#2c3e50"


def build_table(parent, columns, rows, height=200):
    """构建一个表格（CTkScrollableFrame + CTkLabel grid）。

    Args:
        parent:  父容器（任何 CTk 容器）
        columns: 列名列表，如 ["客户类型", "人数", "占比"]
        rows:    数据行，每行是与 columns 等长的可迭代对象
        height:  表格高度（像素），决定多少行后开始滚动

    Returns:
        CTkScrollableFrame 实例，已填好表头 + 数据行。
        调用方负责 pack / grid 到所需位置。

    使用：
        # 创建并显示
        table = build_table(parent, ["A", "B"], [(1, 2), (3, 4)])
        table.pack(fill="both", expand=True)

        # 需要刷新数据：销毁旧的 + 重建
        if self.table is not None:
            self.table.destroy()
        self.table = build_table(parent, columns, new_rows)
        self.table.pack(fill="both", expand=True)
    """
    # CTkScrollableFrame 自带垂直滚动条；fg_color=transparent 让背景跟随父容器
    table = ctk.CTkScrollableFrame(
        parent,
        fg_color="transparent",
        height=height,
        corner_radius=0,
    )

    # ───── 表头（第 0 行）─────
    for col_idx, col_name in enumerate(columns):
        header = ctk.CTkLabel(
            table,
            text=str(col_name),
            font=("SimHei", 12, "bold"),
            fg_color=HEADER_BG,
            text_color=HEADER_FG,
            anchor="w",
            corner_radius=0,
        )
        # ipadx/ipady 在 CTkLabel 上无效；用 grid 的 padx/pady 控制单元格间距
        # sticky="ew" 让单元格横向填满分配到的宽度
        header.grid(row=0, column=col_idx, sticky="ew", padx=1, pady=(0, 1))

    # ───── 数据行（第 1 行起）─────
    for row_idx, row in enumerate(rows, start=1):
        # 交替行底色（奇数行白 / 偶数行更浅灰）
        bg = ROW_BG_ODD if row_idx % 2 == 1 else ROW_BG_EVEN
        for col_idx, value in enumerate(row):
            cell = ctk.CTkLabel(
                table,
                text=str(value),
                font=("SimHei", 11),
                fg_color=bg,
                text_color=TEXT_COLOR,
                anchor="w",
                corner_radius=0,
            )
            cell.grid(row=row_idx, column=col_idx, sticky="ew", padx=1, pady=0)

    # ───── 列宽：所有列等比例分配空间 ─────
    # weight=1 让 grid 把多余宽度均分给各列；如果某列内容长会自动适应
    for col_idx in range(len(columns)):
        table.grid_columnconfigure(col_idx, weight=1)

    return table
