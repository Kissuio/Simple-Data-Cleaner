"""数据清洗页 —— 数据体检工作台（customtkinter 版本）。

本页只负责 GUI 组织：
- 调用 DataCleaner 的既有清洗方法；
- 展示清洗前后行数、删除量、完成状态；
- 展示当前文件清洗日志，并保留切换文件前归档的历史清洗日志。
"""

from tkinter import messagebox

import customtkinter as ctk

from data_handlers.data_cleaner import DataCleaner
from gui.pages.base_page import BasePage
from gui.widgets import (
    BORDER_WIDTH,
    MetricCard,
    UI_COLORS as COLORS,
    build_workflow_nav,
    refresh_workflow_nav,
    reset_chart_progress,
)


CLEAN_STEPS = [
    ("1", "删 CustomerID 缺失", "drop_missing_customer_id"),
    ("2", "删取消订单", "drop_cancellations"),
    ("3", "删非产品代码", "drop_non_product_codes"),
    ("4", "时间转换", "convert_date"),
    ("5", "加 TotalPrice", "add_total_price"),
]

CLEAN_STEP_DETAILS = {
    "drop_missing_customer_id": (
        "删 CustomerID 缺失",
        "删除无法识别客户的交易记录，保证后续可以按 CustomerID 做 RFM 聚合。",
    ),
    "drop_cancellations": (
        "删取消订单",
        "删除 C 开头的取消订单，并同步剔除与其匹配的原始正向订单。",
    ),
    "drop_non_product_codes": (
        "删非产品代码",
        "过滤 POST、DOT、C2、M、BANK CHARGES 等非真实商品记录。",
    ),
    "convert_date": (
        "时间转换",
        "将 InvoiceDate 转换为 datetime，供月度趋势、小时热力图和 Recency 计算使用。",
    ),
    "add_total_price": (
        "加 TotalPrice",
        "新增 TotalPrice = Quantity × UnitPrice，供销售额、RFM-M 和商品销售额分析使用。",
    ),
}


class CleanerPage(BasePage):
    """数据清洗页。"""

    def __init__(self, master, app):
        super().__init__(
            master,
            app,
            title="数据清洗",
            requires="loader",
            next_page="RFM 分析",
        )
        self.info_var = ctk.StringVar(value="当前数据状态：尚未加载数据")
        self.metric_vars = {}
        self.nav_items = {}
        self._build_body()

    def _build_body(self):
        """搭页面：流程导航 + 清洗操作 + 日志。"""
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
        self._build_log_panels(main)

    def _build_workflow_nav(self, parent):
        return build_workflow_nav(parent, self.app, "数据清洗", self.nav_items)

    def _build_metrics(self, parent):
        metrics = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        metrics.grid(row=0, column=0, sticky="ew")
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1, uniform="clean_metric")

        specs = [
            ("原始记录", "raw", COLORS["blue"]),
            ("当前记录", "current", COLORS["green"]),
            ("删除记录", "removed", COLORS["red"]),
            ("清洗状态", "state", COLORS["amber"]),
        ]
        for col, (title, key, accent) in enumerate(specs):
            value_var = ctk.StringVar(value="--")
            note_var = ctk.StringVar(value="等待数据")
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
            text="清洗操作",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            panel,
            textvariable=self.info_var,
            font=("SimHei", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        buttons = ctk.CTkFrame(panel, fg_color="transparent", corner_radius=0)
        buttons.grid(row=0, column=1, rowspan=2, sticky="e", padx=18)

        ctk.CTkButton(
            buttons,
            text="一键全清洗",
            command=self._on_clean_all,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=120,
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="重置",
            command=self._on_reset,
            fg_color=COLORS["gray"],
            hover_color=COLORS["gray_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=82,
            corner_radius=6,
        ).pack(side="left")

        step_frame = ctk.CTkFrame(panel, fg_color=COLORS["panel_soft"], corner_radius=8)
        step_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 16))
        for col in range(5):
            step_frame.grid_columnconfigure(col, weight=1, uniform="clean_step")

        for col, (number, text, method_name) in enumerate(CLEAN_STEPS):
            btn = ctk.CTkButton(
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
            )
            btn.grid(row=0, column=col, sticky="ew", padx=6, pady=10)

    def _build_log_panels(self, parent):
        logs = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        logs.grid(row=2, column=0, sticky="nsew")
        logs.grid_columnconfigure(0, weight=1)
        logs.grid_columnconfigure(1, weight=1)
        logs.grid_rowconfigure(0, weight=1)

        current_panel = self._make_log_panel(logs, "当前清洗日志", 0)
        history_panel = self._make_log_panel(logs, "历史清洗日志", 1)

        self.log_text = ctk.CTkTextbox(
            current_panel,
            font=("SimHei", 13),
            fg_color="#ffffff",
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.history_text = ctk.CTkTextbox(
            history_panel,
            font=("SimHei", 12),
            fg_color="#ffffff",
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
            wrap="word",
        )
        self.history_text.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def _make_log_panel(self, parent, title, column):
        panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        panel.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0))

        ctk.CTkLabel(
            panel,
            text=title,
            font=("SimHei", 14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(fill="x", padx=14, pady=(14, 8))
        return panel

    def on_show(self):
        """进入本页时刷新提示、指标和日志。"""
        super().on_show()
        self._refresh_display()

    def _ensure_loader(self):
        """检查数据已加载。"""
        if self.app.loader is None or self.app.loader.df is None:
            messagebox.showwarning("数据未加载", "请先在【加载数据】页加载 CSV 文件。")
            return False
        return True

    def _on_clean_all(self):
        """一键全清洗。"""
        if not self._ensure_loader():
            return
        previous_log = self._current_cleaning_log()
        try:
            cleaner = DataCleaner(self.app.loader.df)
            if previous_log:
                cleaner.log.append("【保留记录】一键全清洗前，本文件已经执行过以下分步操作：")
                cleaner.log.extend(previous_log)
                cleaner.log.append("【一键全清洗】从原始数据重新执行标准 5 步流程，下面是本次结果：")
            else:
                cleaner.log.append("【一键全清洗】从原始数据执行标准 5 步流程。")

            for _, _, method_name in CLEAN_STEPS:
                self._run_clean_method(cleaner, method_name)
            cleaner.log.append("=== 全部清洗步骤完成 ===")
        except Exception as e:
            messagebox.showerror("清洗失败", f"执行清洗时出错：\n{e}")
            return
        self.app.cleaner = cleaner
        self.app.rfm_analyzer = None
        self.app.rfm_df = None
        reset_chart_progress(self.app)
        self._refresh_display()
        self.app.set_status(f"已完成全部清洗：{len(cleaner.df)} 行")

    def _on_reset(self):
        """重置：重新创建 DataCleaner，并清空下游 RFM 状态。"""
        if not self._ensure_loader():
            return
        self.app.cleaner = DataCleaner(self.app.loader.df)
        self.app.rfm_analyzer = None
        self.app.rfm_df = None
        reset_chart_progress(self.app)
        self._refresh_display()
        self.app.set_status("已重置：cleaner + RFM 结果都清空，回到未清洗状态")

    def _run_step(self, method_name):
        """运行单个清洗步骤。"""
        if not self._ensure_loader():
            return
        if self.app.cleaner is None:
            self.app.cleaner = DataCleaner(self.app.loader.df)
        try:
            self._run_clean_method(self.app.cleaner, method_name)
        except Exception as e:
            messagebox.showerror("步骤失败", f"执行 {method_name} 时出错：\n{e}")
            return
        self.app.rfm_analyzer = None
        self.app.rfm_df = None
        reset_chart_progress(self.app)
        self._refresh_display()
        self.app.set_status(f"已执行：{method_name}，当前 {len(self.app.cleaner.df)} 行")

    def _run_clean_method(self, cleaner, method_name):
        """给独立清洗函数补 GUI 层步骤说明，再执行原函数。"""
        title, detail = CLEAN_STEP_DETAILS[method_name]
        before = len(cleaner.df) if cleaner.df is not None else 0
        cleaner.log.append(f"【步骤】{title}")
        cleaner.log.append(f"说明：{detail}")
        method = getattr(cleaner, method_name)
        method()
        after = len(cleaner.df) if cleaner.df is not None else 0
        cleaner.log.append(f"结果：{before:,} → {after:,}，变化 {before - after:,} 行")

    def _current_cleaning_log(self):
        if self.app.cleaner is None or not self.app.cleaner.log:
            return []
        return list(self.app.cleaner.log)

    def _refresh_display(self):
        """更新指标、导航和日志显示。"""
        loader_df = self.app.loader.df if self.app.loader else None
        cleaner_df = self.app.cleaner.df if self.app.cleaner else None

        if loader_df is None:
            raw_rows = None
            current_rows = None
            removed_rows = None
            state = "未加载"
            self.info_var.set("当前数据状态：尚未加载数据")
        elif cleaner_df is None:
            raw_rows = len(loader_df)
            current_rows = len(loader_df)
            removed_rows = 0
            state = "待清洗"
            self.info_var.set(f"当前数据状态：原始 {raw_rows} 行（未清洗）")
        else:
            raw_rows = len(loader_df)
            current_rows = len(cleaner_df)
            removed_rows = raw_rows - current_rows
            state = "已清洗" if "TotalPrice" in cleaner_df.columns else "进行中"
            self.info_var.set(f"当前数据状态：原始 {raw_rows} 行 → 当前 {current_rows} 行")

        self._set_metric("raw", self._fmt_number(raw_rows), "导入数据")
        self._set_metric("current", self._fmt_number(current_rows), "当前可分析记录")
        self._set_metric("removed", self._fmt_number(removed_rows), "累计删除/过滤")
        self._set_metric("state", state, "清洗流程状态")

        self._refresh_nav_state()
        self._refresh_current_log()
        self._refresh_history_log()

    def _refresh_nav_state(self):
        refresh_workflow_nav(self.nav_items, self.app, "数据清洗")

    def _refresh_current_log(self):
        self.log_text.delete("1.0", "end")
        if self.app.cleaner is not None and self.app.cleaner.log:
            file_name = self._current_file_name()
            self.log_text.insert("end", f"【当前文件】{file_name}\n\n")
            for line in self.app.cleaner.log:
                self.log_text.insert("end", f"• {line}\n")
        else:
            self.log_text.insert("end", "（当前文件暂无清洗日志）")

    def _refresh_history_log(self):
        self.history_text.delete("1.0", "end")
        history = getattr(self.app, "cleaning_history", [])
        if not history:
            self.history_text.insert("end", "（切换文件后，上一份文件的清洗日志会保留在这里）")
            return

        for idx, entry in enumerate(reversed(history), start=1):
            file_name = entry.get("file_path", "未知文件").split("\\")[-1]
            self.history_text.insert("end", f"#{idx} {file_name}\n")
            self.history_text.insert("end", f"归档时间：{entry.get('archived_at', '-')}\n")
            raw_rows = self._fmt_number(entry.get("raw_rows"))
            clean_rows = self._fmt_number(entry.get("clean_rows"))
            self.history_text.insert("end", f"行数：{raw_rows} → {clean_rows}\n")
            for line in entry.get("log", []):
                self.history_text.insert("end", f"  • {line}\n")
            self.history_text.insert("end", "\n")

    def _current_file_name(self):
        if self.app.loader is None:
            return "未知文件"
        path = getattr(self.app.loader, "file_path", "未知文件")
        return path.split("\\")[-1]

    def _set_metric(self, key, value, note):
        value_var, note_var = self.metric_vars[key]
        value_var.set(value)
        note_var.set(note)

    def _fmt_number(self, value):
        if value is None:
            return "--"
        return f"{int(value):,}"
