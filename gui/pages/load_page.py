"""加载数据页 —— 文件导入工作台（customtkinter 版本）。

页面目标：
- 让"选择文件 → 字段校验 → 数据预览"形成清楚的一步式工作流；
- 在导入后给出记录数、字段数、文件类型、文件大小等基础信息；
- 把必需字段/可选字段的检查结果直接展示出来，便于答辩说明数据准备过程。
"""

from pathlib import Path
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

from data_handlers.file_loader import FileLoader
from gui.error_messages import show_friendly_error
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


REQUIRED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
]
OPTIONAL_COLUMNS = ["Country"]


class ValidationRow(ctk.CTkFrame):
    """字段校验行。"""

    def __init__(self, parent, column_name, required=True):
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.required = required

        ctk.CTkLabel(
            self,
            text=column_name,
            font=("Microsoft YaHei UI", 12, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(
            self,
            text="待检查",
            width=72,
            height=24,
            fg_color=COLORS["panel_soft"],
            text_color=COLORS["muted"],
            font=("SimHei", 10, "bold"),
            corner_radius=6,
        )
        self.status_label.grid(row=0, column=1, padx=(8, 0))

    def set_state(self, state):
        if state == "ok":
            self.status_label.configure(
                text="自动识别", fg_color=COLORS["green_soft"], text_color=COLORS["green"]
            )
        elif state == "to_map":
            self.status_label.configure(
                text="待映射", fg_color=COLORS["amber_soft"], text_color=COLORS["amber"]
            )
        elif state == "missing_required":
            self.status_label.configure(
                text="缺失", fg_color=COLORS["red_soft"], text_color=COLORS["red"]
            )
        elif state == "missing_optional":
            self.status_label.configure(
                text="可选缺失", fg_color=COLORS["amber_soft"], text_color=COLORS["amber"]
            )
        else:
            self.status_label.configure(
                text="待检查", fg_color=COLORS["panel_soft"], text_color=COLORS["muted"]
            )


class LoadPage(BasePage):
    """加载数据页。"""

    def __init__(self, master, app):
        super().__init__(
            master,
            app,
            title="加载数据",
            requires=None,
            next_page="数据清洗",
        )

        self.file_path_var = ctk.StringVar(value="尚未选择文件")
        self.file_hint_var = ctk.StringVar(value="支持 .csv / .xlsx，导入后直接进入清洗；进入分析时再做字段映射。")
        self.load_state_var = ctk.StringVar(value="等待导入")
        self.preview_title_var = ctk.StringVar(value="数据预览（等待导入）")
        self.metric_vars = {}
        self.validation_rows = {}
        self.nav_items = {}
        self.table = None
        self.empty_label = None

        self._build_body()

    def _build_body(self):
        """搭建导入工作台。"""
        self.body.configure(fg_color=COLORS["page_bg"])
        self.body.grid_columnconfigure(0, weight=0)
        self.body.grid_columnconfigure(1, weight=1)
        self.body.grid_rowconfigure(0, weight=1)

        nav = self._build_workflow_nav(self.body)
        nav.grid(row=0, column=0, sticky="ns", padx=(24, 18), pady=24)

        main = ctk.CTkFrame(self.body, fg_color="transparent", corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 24), pady=24)
        main.grid_columnconfigure(0, weight=0)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(
            main,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
            width=330,
        )
        left.grid(row=0, column=0, sticky="ns", padx=(0, 18))
        left.grid_propagate(False)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(main, fg_color="transparent", corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        self._build_import_panel(left)
        self._build_metrics(right)
        self._build_preview_panel(right)

    def _build_workflow_nav(self, parent):
        return build_workflow_nav(parent, self.app, "加载数据", self.nav_items)

    def _build_import_panel(self, parent):
        ctk.CTkLabel(
            parent,
            text="文件导入",
            font=("SimHei", 18, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 4))

        ctk.CTkLabel(
            parent,
            text="选择任意商家的交易表（.csv / .xlsx），导入后保留原始列名直接清洗；进入分析时再把列映射到标准字段。",
            font=("SimHei", 11),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=300,
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 16))

        ctk.CTkButton(
            parent,
            text="选择数据文件",
            command=self._on_select_file,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 13, "bold"),
            height=42,
            corner_radius=6,
        ).grid(row=2, column=0, sticky="ew", padx=20)

        file_card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_soft"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        file_card.grid(row=3, column=0, sticky="ew", padx=20, pady=16)
        file_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            file_card,
            textvariable=self.load_state_var,
            font=("SimHei", 11, "bold"),
            text_color=COLORS["blue"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            file_card,
            textvariable=self.file_path_var,
            font=("SimHei", 11),
            text_color=COLORS["text"],
            anchor="w",
            justify="left",
            wraplength=285,
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 4))

        ctk.CTkLabel(
            file_card,
            textvariable=self.file_hint_var,
            font=("SimHei", 10),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=285,
        ).grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))

        self._build_validation_panel(parent)

    def _build_validation_panel(self, parent):
        ctk.CTkLabel(
            parent,
            text="字段识别预览",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=4, column=0, sticky="ew", padx=20, pady=(2, 6))

        ctk.CTkLabel(
            parent,
            text="下面是按列名自动识别的结果。「待映射」不影响清洗，进入分析时手动指认即可。",
            font=("SimHei", 10),
            text_color=COLORS["muted"],
            anchor="w",
            wraplength=300,
        ).grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 8))

        rows = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        rows.grid(row=6, column=0, sticky="ew", padx=20)
        rows.grid_columnconfigure(0, weight=1)

        row_index = 0
        for column in REQUIRED_COLUMNS:
            row = ValidationRow(rows, column, required=True)
            row.grid(row=row_index, column=0, sticky="ew", pady=3)
            self.validation_rows[column] = row
            row_index += 1

        ctk.CTkLabel(
            rows,
            text="可选字段",
            font=("SimHei", 10, "bold"),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=row_index, column=0, sticky="ew", pady=(10, 3))
        row_index += 1

        for column in OPTIONAL_COLUMNS:
            row = ValidationRow(rows, column, required=False)
            row.grid(row=row_index, column=0, sticky="ew", pady=3)
            self.validation_rows[column] = row
            row_index += 1

    def _build_metrics(self, parent):
        metric_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        metric_frame.grid(row=0, column=0, sticky="ew")
        for col in range(4):
            metric_frame.grid_columnconfigure(col, weight=1, uniform="load_metric")

        specs = [
            ("记录数", "rows", COLORS["blue"]),
            ("字段数", "columns", COLORS["green"]),
            ("文件类型", "file_type", COLORS["amber"]),
            ("文件大小", "file_size", COLORS["blue"]),
        ]
        for col, (title, key, accent) in enumerate(specs):
            value_var = ctk.StringVar(value="--")
            note_var = ctk.StringVar(value="等待导入")
            self.metric_vars[key] = (value_var, note_var)
            card = MetricCard(metric_frame, title, value_var, note_var, accent)
            card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))

        summary = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        summary.grid(row=1, column=0, sticky="ew", pady=16)
        summary.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            summary,
            text="导入说明",
            font=("SimHei", 12, "bold"),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 2))

        ctk.CTkLabel(
            summary,
            text=(
                "加载成功后会自动清空旧的清洗结果和 RFM 结果，避免不同数据文件之间互相污染。"
                "本系统保留你表格的原始列名直接清洗；进入分析（RFM / 销售 / 商品 / 总览）时，"
                "会弹出字段映射窗口、自动猜好列对应（如「会员卡号」→ CustomerID），猜错可手动调整——"
                "因此不同商家、不同列名的交易表都能分析。"
            ),
            font=("SimHei", 12),
            text_color=COLORS["text"],
            anchor="w",
            justify="left",
            wraplength=800,
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))

    def _build_preview_panel(self, parent):
        preview_panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        preview_panel.grid(row=2, column=0, sticky="nsew")
        preview_panel.grid_columnconfigure(0, weight=1)
        preview_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            preview_panel,
            textvariable=self.preview_title_var,
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))

        self.table_container = ctk.CTkFrame(
            preview_panel,
            fg_color="#ffffff",
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        self.table_container.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))

        self._show_empty_preview("选择文件后将在这里显示前 10 行数据。")

    def _on_select_file(self):
        """选文件 → 读入原始列 → 直接进入清洗（方案 B：字段映射推迟到分析入口）。"""
        path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[
                ("CSV 文件", "*.csv"),
                ("Excel 文件", "*.xlsx"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return

        self.file_path_var.set(path)
        self._enter_loading_state(path)

        # 只把文件读进来——保留原始列名，不在此改名、不弹映射。
        try:
            loader = FileLoader(path)
            loader.load_file()
        except Exception as e:
            self._clear_loaded_state()
            self.load_state_var.set("导入失败")
            self.file_hint_var.set("请按错误提示检查文件，再重新选择。")
            show_friendly_error("加载失败", e, "读取数据文件", parent=self)
            return

        # 写入 app 并刷新主界面；字段映射在进入分析页时再做。
        self._reset_downstream_state()
        self.app.loader = loader
        self._refresh_loaded_state(loader)
        self._refresh_nav_state()
        self.app.set_status(
            f"已加载: {loader.file_path}（{len(loader.df)} 行，{len(loader.df.columns)} 列）"
        )

    def on_show(self):
        """进入本页时刷新左侧流程状态。"""
        super().on_show()
        self._refresh_nav_state()

    def _refresh_loaded_state(self, loader):
        df = loader.df
        path = Path(loader.file_path)

        self.load_state_var.set("导入成功")
        self.file_path_var.set(str(path))
        self.file_hint_var.set("已读入原始列，可以进入「数据清洗」；进入分析时再做字段映射。")

        self._set_metric("rows", f"{len(df):,}", "原始交易记录")
        self._set_metric("columns", f"{len(df.columns):,}", "已识别字段")
        self._set_metric("file_type", path.suffix.upper().lstrip("."), "数据格式")
        self._set_metric("file_size", self._format_size(path), "本地文件")

        self._refresh_validation(loader)
        self.preview_title_var.set("数据预览（前 10 行）")
        self._render_preview(df.head(10))

    def _refresh_validation(self, loader):
        """按列名自动识别每个标准字段对应哪一列，给映射前的预览。

        方案 B：这里不再「校验」是否缺列（缺列也能正常清洗），而是展示自动识别结果——
        识别到 → 绿「自动识别」；没识别到 → 必需字段标黄「待映射」，可选字段标「可选缺失」。
        真正的指认在进入分析页时的字段映射对话框里完成。
        """
        from data_handlers.field_mapping import guess_mapping
        guess = guess_mapping(loader.df.columns)
        for column in REQUIRED_COLUMNS:
            state = "ok" if guess.get(column) else "to_map"
            self.validation_rows[column].set_state(state)
        for column in OPTIONAL_COLUMNS:
            state = "ok" if guess.get(column) else "missing_optional"
            self.validation_rows[column].set_state(state)

    def _mark_validation_failure(self, loader):
        if loader is None or loader.df is None:
            for row in self.validation_rows.values():
                row.set_state("pending")
            return
        self._refresh_validation(loader)

    def _render_preview(self, df_preview):
        """用 build_table 渲染 DataFrame 前几行。"""
        self._clear_preview_content()

        rows = [
            tuple(str(v) for v in row)
            for _, row in df_preview.iterrows()
        ]

        self.table = build_table(
            self.table_container,
            columns=list(df_preview.columns),
            rows=rows,
            height=410,
        )
        self.table.pack(fill="both", expand=True, padx=2, pady=2)

    def _reset_downstream_state(self):
        """换文件前清空所有依赖旧数据集的状态，包括全局筛选。"""
        self._archive_current_cleaning_log()
        self.app.cleaner = None
        self.app.rfm_analyzer = None
        self.app.rfm_df = None
        self.app.visualizer = None
        self.app.reset_data_filter()
        # 方案 B：换文件后旧映射作废（新表列名可能完全不同），进入分析时重新映射
        self.app.field_mapping = None
        self.app.mapping_intro_seen = False
        self.app.cleaning_intro_seen = False
        reset_chart_progress(self.app)

    def _clear_loaded_state(self):
        self._reset_downstream_state()
        self.app.loader = None
        for key in self.metric_vars:
            self._set_metric(key, "--", "等待导入")
        self.preview_title_var.set("数据预览（导入失败）")
        self._show_empty_preview("当前文件未能导入，请重新选择 CSV 或 XLSX 文件。")
        self._refresh_nav_state(load_state="failed")

    def _enter_loading_state(self, path):
        """开始导入前清空旧显示，避免重复导入时残留旧表格。"""
        self._reset_downstream_state()
        self.app.loader = None
        self.load_state_var.set("导入中")
        self.file_hint_var.set("正在读取文件...")
        self.preview_title_var.set("数据预览（正在导入）")
        for key in self.metric_vars:
            self._set_metric(key, "--", "读取中")
        for row in self.validation_rows.values():
            row.set_state("pending")
        self._show_empty_preview(f"正在导入：{Path(path).name}")
        self._refresh_nav_state(load_state="loading")

    def _refresh_nav_state(self, load_state=None):
        refresh_workflow_nav(self.nav_items, self.app, "加载数据", load_state=load_state)

    def _archive_current_cleaning_log(self):
        """重新导入前归档当前清洗日志，避免切换文件后日志丢失。"""
        cleaner = self.app.cleaner
        if cleaner is None or not getattr(cleaner, "log", None):
            return

        loader = self.app.loader
        file_path = getattr(loader, "file_path", "未知文件")
        raw_rows = len(loader.df) if loader is not None and loader.df is not None else None
        clean_rows = len(cleaner.df) if cleaner.df is not None else None
        entry = {
            "file_path": file_path,
            "archived_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_rows": raw_rows,
            "clean_rows": clean_rows,
            "log": list(cleaner.log),
        }

        history = getattr(self.app, "cleaning_history", None)
        if history is None:
            self.app.cleaning_history = []
            history = self.app.cleaning_history

        if history and history[-1]["file_path"] == entry["file_path"] and history[-1]["log"] == entry["log"]:
            return
        history.append(entry)

    def _clear_preview_content(self):
        """直接清空预览容器内所有子组件，避免多次导入叠加旧 widget。"""
        for child in self.table_container.winfo_children():
            child.destroy()
        self.table = None
        self.empty_label = None

    def _show_empty_preview(self, message):
        self._clear_preview_content()
        self.empty_label = ctk.CTkLabel(
            self.table_container,
            text=message,
            font=("SimHei", 13),
            text_color=COLORS["muted"],
        )
        self.empty_label.pack(expand=True)

    def _set_metric(self, key, value, note):
        value_var, note_var = self.metric_vars[key]
        value_var.set(value)
        note_var.set(note)

    def _format_size(self, path):
        try:
            size = path.stat().st_size
        except OSError:
            return "--"
        if size >= 1024 * 1024:
            return f"{size / 1024 / 1024:.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} B"
