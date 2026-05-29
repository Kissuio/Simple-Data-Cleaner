"""RFM 分析页 —— 客户分群工作台（customtkinter 版本）。

本页只改 GUI 展示：
- 调用现有 RFMAnalyzer 完成 RFM 计算、打分、贴标签；
- 用 8 类客户矩阵替代单纯表格，让分群结果更适合答辩展示；
- 保留分布表和 RFM 预览表，便于检查明细。
"""

from tkinter import messagebox

import customtkinter as ctk

from analyzer.rfm_analyzer import RFMAnalyzer
from gui.pages.base_page import BasePage
from gui.widgets import (
    BORDER_WIDTH,
    MetricCard,
    UI_COLORS as COLORS,
    build_table,
    build_workflow_nav,
    refresh_workflow_nav,
    reset_chart_progress,
)


RFM_STEPS = [
    ("1", "计算 R/F/M", "calc_rfm"),
    ("2", "均值打分", "score_rfm"),
    ("3", "生成标签", "label_customer"),
]

SEGMENT_ORDER = [
    "重要价值客户",
    "重要保持客户",
    "重要发展客户",
    "重要挽留客户",
    "一般价值客户",
    "一般保持客户",
    "一般发展客户",
    "一般挽留客户",
]

SEGMENT_META = {
    "重要价值客户": ("#f59e0b", "#fffbeb", "高价值核心客群，适合会员权益、专属活动和重点维护。"),
    "重要保持客户": ("#10b981", "#ecfdf5", "价值高但近期不够活跃，适合召回提醒和专属优惠。"),
    "重要发展客户": ("#2563eb", "#eff6ff", "近期活跃且金额高，可通过复购激励提升频次。"),
    "重要挽留客户": ("#ef4444", "#fef2f2", "历史价值高但流失风险明显，适合强召回和关怀。"),
    "一般价值客户": ("#14b8a6", "#f0fdfa", "表现稳定但金额偏低，可通过组合推荐提升客单价。"),
    "一般保持客户": ("#8b5cf6", "#f5f3ff", "频次或金额尚可，适合低成本维系和周期触达。"),
    "一般发展客户": ("#3b82f6", "#eff6ff", "近期有互动但价值未释放，适合新人引导和加购推荐。"),
    "一般挽留客户": ("#64748b", "#f8fafc", "低价值且低活跃，建议自动化触达，控制营销成本。"),
}


class SegmentCard(ctk.CTkFrame):
    """8 类客户矩阵卡片。"""

    def __init__(self, parent, label):
        accent, soft, suggestion = SEGMENT_META[label]
        super().__init__(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=accent,
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        self.label = label
        self.count_var = ctk.StringVar(value="--")
        self.percent_var = ctk.StringVar(value="等待标签")
        self.spend_var = ctk.StringVar(value="人均 --")

        ctk.CTkLabel(
            self,
            text=label,
            fg_color=soft,
            text_color=accent,
            font=("SimHei", 12, "bold"),
            corner_radius=6,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(10, 6))

        row = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        row.pack(fill="x", padx=10)

        ctk.CTkLabel(
            row,
            textvariable=self.count_var,
            font=("Microsoft YaHei UI", 22, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            textvariable=self.percent_var,
            font=("SimHei", 10, "bold"),
            text_color=accent,
            anchor="e",
        ).pack(side="right", pady=(7, 0))

        ctk.CTkLabel(
            self,
            textvariable=self.spend_var,
            font=("SimHei", 10),
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(fill="x", padx=10, pady=(2, 4))

        ctk.CTkLabel(
            self,
            text=suggestion,
            font=("SimHei", 10),
            text_color=COLORS["text"],
            justify="left",
            anchor="nw",
            wraplength=170,
        ).pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def set_values(self, count, percent, avg_spend):
        self.count_var.set(f"{int(count):,}")
        self.percent_var.set(f"{percent:.1f}%")
        self.spend_var.set(f"人均消费 £{avg_spend:,.0f}")

    def clear(self):
        self.count_var.set("--")
        self.percent_var.set("等待标签")
        self.spend_var.set("人均 --")


class RFMPage(BasePage):
    """RFM 分析页。"""

    def __init__(self, master, app):
        super().__init__(
            master,
            app,
            title="RFM 分析",
            requires="cleaner",
            next_page="销售分析",
        )
        self.status_var = ctk.StringVar(value="状态：尚未分析")
        self.metric_vars = {}
        self.nav_items = {}
        self.segment_cards = {}
        self.dist_table = None
        self.rfm_table = None

        self._build_body()

    def _build_body(self):
        self.body.configure(fg_color=COLORS["page_bg"])
        self.body.grid_columnconfigure(0, weight=0)
        self.body.grid_columnconfigure(1, weight=1)
        self.body.grid_rowconfigure(0, weight=1)

        nav = self._build_workflow_nav(self.body)
        nav.grid(row=0, column=0, sticky="ns", padx=(24, 18), pady=24)

        main = ctk.CTkFrame(self.body, fg_color="transparent", corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 24), pady=24)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        self._build_metrics(main)
        self._build_action_panel(main)
        self._build_content(main)

    def _build_workflow_nav(self, parent):
        return build_workflow_nav(parent, self.app, "RFM 分析", self.nav_items)

    def _build_metrics(self, parent):
        metrics = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        metrics.grid(row=0, column=0, sticky="ew")
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1, uniform="rfm_metric")

        specs = [
            ("客户数", "customers", COLORS["blue"]),
            ("平均 Recency", "recency", COLORS["amber"]),
            ("平均 Frequency", "frequency", COLORS["green"]),
            ("平均 Monetary", "monetary", COLORS["purple"]),
        ]
        for col, (title, key, accent) in enumerate(specs):
            value_var = ctk.StringVar(value="--")
            note_var = ctk.StringVar(value="等待 RFM")
            self.metric_vars[key] = (value_var, note_var)
            card = MetricCard(metrics, title, value_var, note_var, accent)
            card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))

    def _build_action_panel(self, parent):
        panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        panel.grid(row=1, column=0, sticky="ew", pady=16)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text="RFM 分析流程",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            panel,
            textvariable=self.status_var,
            font=("SimHei", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        buttons = ctk.CTkFrame(panel, fg_color="transparent", corner_radius=0)
        buttons.grid(row=0, column=1, rowspan=2, sticky="e", padx=18)

        ctk.CTkButton(
            buttons,
            text="一键全分析",
            command=self._on_analyze_all,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=120,
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="重新分析",
            command=self._on_reset,
            fg_color=COLORS["gray"],
            hover_color=COLORS["gray_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=92,
            corner_radius=6,
        ).pack(side="left")

        step_frame = ctk.CTkFrame(panel, fg_color=COLORS["panel_soft"], corner_radius=8)
        step_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 16))
        for col in range(3):
            step_frame.grid_columnconfigure(col, weight=1, uniform="rfm_step")

        for col, (number, text, method_name) in enumerate(RFM_STEPS):
            ctk.CTkButton(
                step_frame,
                text=f"{number}. {text}",
                command=lambda m=method_name: self._run_step(m),
                fg_color="#ffffff",
                hover_color=COLORS["blue_soft"],
                text_color=COLORS["text"],
                border_color=COLORS["border"],
                border_width=BORDER_WIDTH,
                font=("SimHei", 11, "bold"),
                height=34,
                corner_radius=6,
            ).grid(row=0, column=col, sticky="ew", padx=6, pady=10)

    def _build_content(self, parent):
        content = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        matrix_panel = ctk.CTkFrame(
            content,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        matrix_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        matrix_panel.grid_columnconfigure(0, weight=1)
        matrix_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            matrix_panel,
            text="8 类客户分群矩阵",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        matrix = ctk.CTkFrame(matrix_panel, fg_color="transparent", corner_radius=0)
        matrix.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        for col in range(4):
            matrix.grid_columnconfigure(col, weight=1, uniform="segment_col")
        for row in range(2):
            matrix.grid_rowconfigure(row, weight=1, uniform="segment_row")

        for index, label in enumerate(SEGMENT_ORDER):
            row, col = divmod(index, 4)
            card = SegmentCard(matrix, label)
            card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            self.segment_cards[label] = card

        side = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        side.grid(row=0, column=1, sticky="nsew")
        side.grid_columnconfigure(0, weight=1)
        side.grid_rowconfigure(0, weight=1)
        side.grid_rowconfigure(1, weight=1)

        self._build_distribution_panel(side)
        self._build_preview_panel(side)

    def _build_distribution_panel(self, parent):
        panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        panel.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            panel,
            text="客户类型分布",
            font=("SimHei", 14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        self.dist_container = ctk.CTkFrame(
            panel,
            fg_color="#ffffff",
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        self.dist_container.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

    def _build_preview_panel(self, parent):
        panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            panel,
            text="RFM 明细预览",
            font=("SimHei", 14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        self.rfm_container = ctk.CTkFrame(
            panel,
            fg_color="#ffffff",
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        self.rfm_container.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

    def on_show(self):
        super().on_show()
        self._refresh_display()

    def _ensure_cleaner(self):
        """检查清洗完整（依赖 TotalPrice 列）。"""
        if self.app.cleaner is None or self.app.cleaner.df is None:
            messagebox.showwarning(
                "尚未清洗数据",
                "请先在【数据清洗】页执行清洗（推荐【一键全清洗】）。",
            )
            return False
        if "TotalPrice" not in self.app.cleaner.df.columns:
            messagebox.showwarning(
                "清洗不完整",
                "RFM 分析需要 TotalPrice 列。\n请回到【数据清洗】点【一键全清洗】。",
            )
            return False
        return True

    def _on_analyze_all(self):
        if not self._ensure_cleaner():
            return
        try:
            analyzer = RFMAnalyzer(self.app.cleaner.df)
            analyzer.analyze_all()
        except Exception as e:
            messagebox.showerror("分析失败", f"执行 RFM 分析时出错：\n{e}")
            return
        self.app.rfm_analyzer = analyzer
        self.app.rfm_df = analyzer.rfm
        reset_chart_progress(self.app, groups=("overview",))
        self._refresh_display()
        self.app.set_status(f"已完成 RFM 分析：{len(analyzer.rfm)} 个客户")

    def _on_reset(self):
        if not self._ensure_cleaner():
            return
        self.app.rfm_analyzer = RFMAnalyzer(self.app.cleaner.df)
        self.app.rfm_df = None
        reset_chart_progress(self.app, groups=("overview",))
        self._refresh_display()
        self.app.set_status("已重置 RFM 分析器")

    def _run_step(self, method_name):
        if not self._ensure_cleaner():
            return
        if self.app.rfm_analyzer is None:
            self.app.rfm_analyzer = RFMAnalyzer(self.app.cleaner.df)
        try:
            method = getattr(self.app.rfm_analyzer, method_name)
            method()
        except Exception as e:
            messagebox.showerror("步骤失败", f"执行 {method_name} 时出错：\n{e}")
            return
        self.app.rfm_df = self.app.rfm_analyzer.rfm
        reset_chart_progress(self.app, groups=("overview",))
        self._refresh_display()
        self.app.set_status(f"已执行：{method_name}")

    def _refresh_display(self):
        """更新指标、矩阵和表格。"""
        rfm = self.app.rfm_df
        self._clear_container(self.dist_container)
        self._clear_container(self.rfm_container)
        for card in self.segment_cards.values():
            card.clear()

        if rfm is None:
            self.status_var.set("状态：尚未分析")
            self._set_metric("customers", "--", "等待 RFM")
            self._set_metric("recency", "--", "等待计算")
            self._set_metric("frequency", "--", "等待计算")
            self._set_metric("monetary", "--", "等待计算")
            self._show_empty(self.dist_container, "完成贴标签后显示 8 类客户分布。")
            self._show_empty(self.rfm_container, "点击「一键全分析」或分步执行后显示 RFM 明细。")
            self._refresh_nav_state()
            return

        self.status_var.set(f"状态：已生成 RFM 表，共 {len(rfm)} 个客户")
        self._set_metric("customers", f"{len(rfm):,}", "客户总数")
        self._set_metric("recency", f"{rfm['Recency'].mean():.1f} 天", "越低越活跃")
        self._set_metric("frequency", f"{rfm['Frequency'].mean():.1f}", "平均订单频次")
        self._set_metric("monetary", f"£{rfm['Monetary'].mean():,.0f}", "平均消费金额")

        if "Label" in rfm.columns:
            self._refresh_segment_matrix(rfm)
            self._refresh_distribution_table(rfm)
        else:
            self._show_empty(self.dist_container, "已计算 RFM 原始值，继续执行「均值打分」和「生成标签」。")

        self._refresh_rfm_table(rfm)
        self._refresh_nav_state()

    def _refresh_segment_matrix(self, rfm):
        counts = rfm["Label"].value_counts()
        total = counts.sum()
        avg_spend = rfm.groupby("Label")["Monetary"].mean()
        for label in SEGMENT_ORDER:
            count = counts.get(label, 0)
            percent = count / total * 100 if total else 0
            spend = avg_spend.get(label, 0)
            self.segment_cards[label].set_values(count, percent, spend)

    def _refresh_distribution_table(self, rfm):
        counts = rfm["Label"].value_counts()
        total = counts.sum()
        avg_spend = rfm.groupby("Label")["Monetary"].mean()
        rows = []
        for label in SEGMENT_ORDER:
            count = counts.get(label, 0)
            percent = count / total * 100 if total else 0
            rows.append((label, count, f"{percent:.1f}%", f"£{avg_spend.get(label, 0):,.0f}"))

        self.dist_table = build_table(
            self.dist_container,
            columns=["客户类型", "人数", "占比", "人均消费"],
            rows=rows,
            height=210,
        )
        self.dist_table.pack(fill="both", expand=True, padx=2, pady=2)

    def _refresh_rfm_table(self, rfm):
        preview = rfm.head(10)
        columns = ["CustomerID"] + list(preview.columns)
        rows = [
            tuple([cid] + [self._fmt(v) for v in row])
            for cid, row in preview.iterrows()
        ]
        self.rfm_table = build_table(
            self.rfm_container,
            columns=columns,
            rows=rows,
            height=250,
        )
        self.rfm_table.pack(fill="both", expand=True, padx=2, pady=2)

    def _refresh_nav_state(self):
        refresh_workflow_nav(self.nav_items, self.app, "RFM 分析")

    def _clear_container(self, container):
        for child in container.winfo_children():
            child.destroy()

    def _show_empty(self, parent, message):
        ctk.CTkLabel(
            parent,
            text=message,
            font=("SimHei", 12),
            text_color=COLORS["muted"],
            wraplength=320,
            justify="center",
        ).pack(expand=True, padx=12, pady=12)

    def _set_metric(self, key, value, note):
        value_var, note_var = self.metric_vars[key]
        value_var.set(value)
        note_var.set(note)

    def _fmt(self, value):
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)
