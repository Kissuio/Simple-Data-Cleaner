"""数据清洗页 —— 数据体检工作台（customtkinter 版本）。

本页只负责 GUI 组织：
- 调用 DataCleaner 的既有清洗方法；
- 展示清洗前后行数、删除量、完成状态；
- 展示当前文件清洗日志，并保留切换文件前归档的历史清洗日志。
"""

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from data_handlers.data_cleaner import DataCleaner
from gui.clean_dialog import CATEGORIES, steps_in_category, CleanStepDialog
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

CLEAN_PREVIEW_ROWS = 10


CLEANING_GUIDE = """一、清洗工具按需取用，没有固定顺序

页面上的「删除行工具」「类型转换工具」「整理 / 派生工具」是三类工具入口，
不必从左到右依次执行，点一次也不会自动跑完整套清洗。

每次点击一个分类后，需要在弹窗顶部选择具体操作，再选择它作用的列和参数。
操作会累积应用在当前数据上；你可以按数据实际情况自由组合、重复使用或跳过。


二、如何决定使用哪些工具

先观察表格的列名、样例值和数据含义，再按问题选择工具：

· 完全重复的记录：使用「删除行工具 → 删重复行」。
· 客户、订单或日期等关键列为空：使用「删空值行」，并只选择需要检查的列。
· 取消订单或特定状态：使用「按文本条件删行」。
· 数量、单价小于等于 0：使用「按数值条件删行」。
· 数字带货币符号、逗号或空格：使用「类型转换工具 → 列转数值」。
· 日期还是普通文本或数字：使用「列转日期」。
· 文本大小写、空格不统一：使用「整理 / 派生工具 → 文本规整」。
· 没有销售额列：使用「派生新列」，计算 数量 × 单价。


三、推荐但不强制的检查顺序

1. 先看关键字段是否存在，并理解每一列代表什么。
2. 处理重复记录和关键字段空值。
3. 把数量、单价、日期转换成正确类型。
4. 按业务含义处理取消单、退货和异常值。
5. 需要时派生销售额等新列。
6. 查看当前清洗日志，确认删除量符合预期，再进入字段映射。

这只是便于检查的建议顺序。不同数据表问题不同，不应机械执行全部工具。


四、撤销、重置与安全性

· 每次有效清洗操作前都会保存快照，可以点击「撤销上一步」。
· 「重置」会回到当前文件刚加载时的原始数据，清空本文件的清洗结果。
· 清洗在内存副本上进行，不会直接修改磁盘里的 CSV 或 Excel 文件。
· 可以在清洗页预览当前清洗结果，并导出为新的 CSV 或 Excel 文件。
· 每次操作后请查看行数变化和日志；删除数量异常时应先撤销并检查参数。
"""


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
        self.preview_title_var = ctk.StringVar(value="当前数据预览（等待数据）")
        self.preview_note_var = ctk.StringVar(value="加载数据后将在这里显示当前清洗结果前 10 行。")
        self.metric_vars = {}
        self.nav_items = {}
        self.preview_table = None
        self.preview_empty_label = None
        self.export_button = None
        self._build_body()

    def _build_body(self):
        """搭页面：流程导航 + 清洗操作 + 结果预览 + 日志。"""
        self.body.configure(fg_color=COLORS["page_bg"])
        self.body.grid_columnconfigure(0, weight=0)
        self.body.grid_columnconfigure(1, weight=1)
        self.body.grid_rowconfigure(0, weight=1)

        nav = self._build_workflow_nav(self.body)
        nav.grid(row=0, column=0, sticky="ns", padx=(24, 18), pady=24)

        main = ctk.CTkFrame(self.body, fg_color="transparent", corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew", padx=(0, 24), pady=24)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=2)
        main.grid_rowconfigure(3, weight=1)

        self._build_metrics(main)
        self._build_action_panel(main)
        self._build_preview_panel(main)
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
            text="清洗说明",
            command=self._show_cleaning_guide,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=96,
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="↩ 撤销上一步",
            command=self._on_undo,
            fg_color=COLORS["amber"],
            hover_color=COLORS.get("amber_hover", COLORS["amber"]),
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

        ctk.CTkLabel(
            panel,
            text=(
                "工具分类（按需取用、顺序自定）：下面每个按钮代表一类可选工具。"
                "点击后再选择具体操作、作用列和参数，可按数据问题自由组合或跳过。"
            ),
            font=("SimHei", 11, "bold"),
            fg_color=COLORS["amber_soft"],
            text_color=COLORS["amber"],
            anchor="w",
            justify="left",
            wraplength=940,
            corner_radius=6,
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 8), ipady=7)

        step_frame = ctk.CTkFrame(panel, fg_color=COLORS["panel_soft"], corner_radius=8)
        step_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 16))
        for col in range(len(CATEGORIES)):
            step_frame.grid_columnconfigure(col, weight=1, uniform="clean_cat")

        for idx, cat in enumerate(CATEGORIES):
            btn = ctk.CTkButton(
                step_frame,
                text=cat["name"] + "工具 …",
                command=lambda c=cat: self._on_category(c),
                fg_color="#ffffff",
                hover_color=COLORS["blue_soft"],
                text_color=COLORS["text"],
                border_color=COLORS["border"],
                border_width=BORDER_WIDTH,
                font=("SimHei", 12, "bold"),
                height=40,
                corner_radius=6,
            )
            btn.grid(row=0, column=idx, sticky="ew", padx=6, pady=10)

    def _build_preview_panel(self, parent):
        """构建当前清洗结果预览和导出入口。"""
        panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        panel.grid(row=2, column=0, sticky="nsew", pady=(0, 16))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            panel,
            textvariable=self.preview_title_var,
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))

        self.export_button = ctk.CTkButton(
            panel,
            text="导出当前数据",
            command=self._on_export_cleaned,
            fg_color=COLORS["green"],
            hover_color=COLORS["green_hover"],
            font=("SimHei", 12, "bold"),
            height=34,
            width=116,
            corner_radius=6,
            state="disabled",
        )
        self.export_button.grid(row=0, column=1, sticky="e", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            panel,
            textvariable=self.preview_note_var,
            font=("SimHei", 11),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 8))

        self.preview_container = ctk.CTkFrame(
            panel,
            fg_color="#ffffff",
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        self.preview_container.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=18, pady=(0, 16))
        self._show_preview_empty("加载数据后将在这里显示当前数据。")

    def _build_log_panels(self, parent):
        logs = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        logs.grid(row=3, column=0, sticky="nsew")
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
        self._maybe_show_cleaning_guide()

    def _maybe_show_cleaning_guide(self):
        """每份已加载数据第一次进入清洗页时自动展示一次说明。"""
        if (
            self.app.loader is not None
            and self.app.loader.df is not None
            and self.app.guided_mode_var.get()
            and not self.app.cleaning_intro_seen
        ):
            self.app.cleaning_intro_seen = True
            self._show_cleaning_guide()

    def _show_cleaning_guide(self):
        """打开可重复查看的清洗工具箱说明页。"""
        from gui.intro_dialog import IntroDialog

        IntroDialog(
            self,
            title="数据清洗工具箱使用说明",
            body=CLEANING_GUIDE,
        )

    def _ensure_loader(self):
        """检查数据已加载。"""
        if self.app.loader is None or self.app.loader.df is None:
            messagebox.showwarning("数据未加载", "请先在【加载数据】页加载 CSV 文件。")
            return False
        return True

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

    def _on_undo(self):
        """撤销上一步清洗：弹出最近快照，恢复到那一步之前（累积式工具箱核心）。"""
        if self.app.cleaner is None or not self.app.cleaner.can_undo:
            messagebox.showinfo("无法撤销", "当前没有可撤销的清洗步骤。")
            return
        before = len(self.app.cleaner.df)
        self.app.cleaner.undo()
        after = len(self.app.cleaner.df)
        # 撤销改变了数据，下游 RFM 与图表进度一并失效
        self.app.rfm_analyzer = None
        self.app.rfm_df = None
        reset_chart_progress(self.app)
        self._refresh_display()
        self.app.set_status(f"已撤销上一步：{before:,} → {after:,} 行")

    def _on_category(self, cat):
        """点一个大类按钮：弹该类的参数对话框（顶部下拉选具体操作，再填参数）。"""
        if not self._ensure_loader():
            return
        if self.app.cleaner is None:
            self.app.cleaner = DataCleaner(self.app.loader.df)
        steps = steps_in_category(cat)
        # 对话框基于「当前」数据的列与取值（可能已清洗几步），让用户照当前状态选
        CleanStepDialog(self, self.app.cleaner.df, steps, cat["name"],
                        on_submit=self._execute_step)

    def _execute_step(self, method_name, kwargs):
        """在当前 cleaner 上执行一把通用刀（累积式，每刀内部已拍快照，可撤销）。"""
        cleaner = self.app.cleaner
        if cleaner is None:
            return
        before = cleaner.row_count
        try:
            getattr(cleaner, method_name)(**kwargs)
        except Exception as e:
            show_friendly_error("清洗失败", e, "执行所选清洗工具", parent=self)
            return
        after = cleaner.row_count
        self.app.rfm_analyzer = None
        self.app.rfm_df = None
        reset_chart_progress(self.app)
        self._refresh_display()
        self.app.set_status(f"已执行 {method_name}：{before:,} → {after:,} 行")

    def _current_result_df(self):
        """返回当前清洗页应展示/导出的数据，以及数据状态标签。"""
        if self.app.cleaner is not None and self.app.cleaner.df is not None:
            return self.app.cleaner.df, "cleaned"
        if self.app.loader is not None and self.app.loader.df is not None:
            return self.app.loader.df, "raw"
        return None, "none"

    def _default_export_name(self):
        """根据当前文件名生成清洗结果导出的默认文件名。"""
        if self.app.loader is None:
            return "cleaned_data.csv"
        path = getattr(self.app.loader, "file_path", "") or ""
        stem = Path(path).stem or "cleaned_data"
        return f"{stem}_cleaned.csv"

    def _export_dataframe(self, df, path):
        """按目标后缀导出 DataFrame；.xlsx 用 Excel，其余默认 CSV。"""
        suffix = Path(path).suffix.lower()
        if suffix == ".xlsx":
            df.to_excel(path, index=False)
        else:
            df.to_csv(path, index=False, encoding="utf-8-sig")

    def _on_export_cleaned(self):
        """导出当前清洗结果，不覆盖原始数据文件。"""
        df, _state = self._current_result_df()
        if df is None:
            messagebox.showwarning("没有可导出数据", "请先在【加载数据】页导入数据。")
            return
        path = filedialog.asksaveasfilename(
            title="导出当前清洗结果",
            defaultextension=".csv",
            filetypes=[
                ("CSV 文件", "*.csv"),
                ("Excel 文件", "*.xlsx"),
                ("所有文件", "*.*"),
            ],
            initialfile=self._default_export_name(),
        )
        if not path:
            return
        try:
            self._export_dataframe(df, path)
        except Exception as e:
            show_friendly_error("导出失败", e, "导出当前清洗结果", parent=self)
            return
        self.app.set_status(f"已导出当前数据：{path}")
        messagebox.showinfo("导出成功", f"已导出 {len(df):,} 行数据到：\n{path}")

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
            # 方案 B：清洗页只管清洗，不再以 TotalPrice 判定「完成」。
            # 做过至少一步清洗（有日志/可撤销）显示「已清洗」，否则「就绪」。
            did_clean = bool(getattr(self.app.cleaner, "log", None)) or self.app.cleaner.can_undo
            state = "已清洗" if did_clean else "就绪"
            self.info_var.set(f"当前数据状态：原始 {raw_rows} 行 → 当前 {current_rows} 行")

        self._set_metric("raw", self._fmt_number(raw_rows), "导入数据")
        self._set_metric("current", self._fmt_number(current_rows), "当前可分析记录")
        self._set_metric("removed", self._fmt_number(removed_rows), "累计删除/过滤")
        self._set_metric("state", state, "清洗流程状态")

        self._refresh_nav_state()
        self._refresh_preview()
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

    def _refresh_preview(self):
        """刷新当前清洗结果预览表。"""
        if not hasattr(self, "preview_container"):
            return
        df, state = self._current_result_df()
        self._clear_preview_content()
        if df is None:
            self.preview_title_var.set("当前数据预览（等待数据）")
            self.preview_note_var.set("加载数据后将在这里显示当前清洗结果前 10 行。")
            self._set_export_enabled(False)
            self._show_preview_empty("请先加载数据。")
            return

        title = "清洗后数据预览" if state == "cleaned" else "原始数据预览（尚未执行清洗）"
        rows_to_show = min(CLEAN_PREVIEW_ROWS, len(df))
        self.preview_title_var.set(f"{title}（前 {rows_to_show} 行）")
        note = f"当前 {len(df):,} 行 × {len(df.columns):,} 列。"
        if state == "raw":
            note += " 还没有执行清洗，导出时会导出原始导入数据的当前副本。"
        else:
            note += " 导出会保存当前清洗结果，不会修改原始文件。"
        self.preview_note_var.set(note)
        self._set_export_enabled(True)

        rows = [
            tuple(str(value) for value in row)
            for _, row in df.head(CLEAN_PREVIEW_ROWS).iterrows()
        ]
        self.preview_table = build_table(
            self.preview_container,
            columns=list(df.columns),
            rows=rows,
            height=240,
        )
        self.preview_table.pack(fill="both", expand=True, padx=2, pady=2)

    def _set_export_enabled(self, enabled):
        if self.export_button is not None:
            self.export_button.configure(state="normal" if enabled else "disabled")

    def _clear_preview_content(self):
        for child in self.preview_container.winfo_children():
            child.destroy()
        self.preview_table = None
        self.preview_empty_label = None

    def _show_preview_empty(self, message):
        self.preview_empty_label = ctk.CTkLabel(
            self.preview_container,
            text=message,
            font=("SimHei", 12),
            text_color=COLORS["muted"],
            justify="center",
        )
        self.preview_empty_label.pack(expand=True, padx=12, pady=12)

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
