"""RFM 分析标签页 —— 对应 RFMAnalyzer 类的入口。

功能：
- 一键全分析：调 analyze_all() 一次跑完 3 步
- 3 个分步按钮：calc_rfm / score_rfm / label_customer
- 显示 8 类客户分布（Treeview 小表）
- 显示 RFM 表前 10 行（Treeview）

依赖：self.app.cleaner.df（必须先在【数据清洗】页跑过清洗）
"""

from tkinter import ttk, messagebox
import tkinter as tk

from analyzer.rfm_analyzer import RFMAnalyzer


class RFMPage(ttk.Frame):
    """RFM 分析标签页。"""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.status_var = tk.StringVar(value="状态：尚未分析")
        self._build_ui()

    def _build_ui(self):
        # ───── 顶部操作区 ─────
        action_frame = ttk.Frame(self, padding=10)
        action_frame.pack(fill="x")

        # 第 1 行：一键 + 重置
        row1 = ttk.Frame(action_frame)
        row1.pack(fill="x")
        ttk.Button(
            row1, text="一键全分析 RFM", command=self._on_analyze_all,
            style="Action.TButton",
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            row1, text="重新分析", command=self._on_reset,
            style="Action.TButton",
        ).pack(side="left")

        # 第 2 行：3 个分步按钮
        step_frame = ttk.LabelFrame(action_frame, text="分步执行（答辩演示用）", padding=10)
        step_frame.pack(fill="x", pady=(10, 0))

        step_buttons = [
            ("1. calc_rfm 计算 R/F/M", lambda: self._run_step("calc_rfm")),
            ("2. score_rfm 打分", lambda: self._run_step("score_rfm")),
            ("3. label_customer 贴标签", lambda: self._run_step("label_customer")),
        ]
        for text, cmd in step_buttons:
            ttk.Button(
                step_frame, text=text, command=cmd, style="Action.TButton",
            ).pack(side="left", padx=4)

        # ───── 状态显示 ─────
        status_label = ttk.Label(
            self, textvariable=self.status_var, font=("SimHei", 11), padding=10
        )
        status_label.pack(fill="x")

        # ───── 8 类分布 ─────
        dist_label = ttk.Label(
            self, text="8 类客户分布：", font=("SimHei", 11, "bold"), padding=(10, 5)
        )
        dist_label.pack(anchor="w")

        dist_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        dist_frame.pack(fill="x")
        self.dist_tree = ttk.Treeview(
            dist_frame,
            columns=("type", "count", "ratio"),
            show="headings",
            height=8,
        )
        self.dist_tree.heading("type", text="客户类型")
        self.dist_tree.heading("count", text="人数")
        self.dist_tree.heading("ratio", text="占比")
        self.dist_tree.column("type", width=200, anchor="w")
        self.dist_tree.column("count", width=100, anchor="center")
        self.dist_tree.column("ratio", width=100, anchor="center")
        self.dist_tree.pack(fill="x")

        # ───── RFM 表预览 ─────
        preview_label = ttk.Label(
            self, text="RFM 表预览（前 10 个客户）：", font=("SimHei", 11, "bold"), padding=(10, 5)
        )
        preview_label.pack(anchor="w")

        preview_frame = ttk.Frame(self, padding=10)
        preview_frame.pack(fill="both", expand=True)

        self.rfm_tree = ttk.Treeview(preview_frame, show="headings", height=10)
        xscroll = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.rfm_tree.xview)
        yscroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.rfm_tree.yview)
        self.rfm_tree.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        self.rfm_tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

    # ───── 按钮回调 ─────

    def _ensure_cleaner(self):
        """检查清洗已完整完成。判据是 TotalPrice 列存在（清洗最后一步加的列）。
        这样分步和一键的校验行为一致，避免基于半清洗的数据跑出错误的 RFM 结果。
        """
        if self.app.cleaner is None or self.app.cleaner.df is None:
            messagebox.showwarning(
                "尚未清洗数据",
                "请先在【数据清洗】标签页执行清洗（推荐【一键全清洗】）。",
            )
            return False
        if "TotalPrice" not in self.app.cleaner.df.columns:
            messagebox.showwarning(
                "清洗不完整",
                "RFM 分析需要 TotalPrice 列。\n"
                "请回到【数据清洗】点【一键全清洗】，或确保 5 个分步全部跑完（含【5. 加 TotalPrice】）。",
            )
            return False
        return True

    def _on_analyze_all(self):
        """一键全分析。"""
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
        self._refresh_display()
        self.app.set_status(f"已完成 RFM 分析：{len(analyzer.rfm)} 个客户")

    def _on_reset(self):
        """重新分析：清除已有结果，再次新建 RFMAnalyzer。"""
        if not self._ensure_cleaner():
            return
        self.app.rfm_analyzer = RFMAnalyzer(self.app.cleaner.df)
        self.app.rfm_df = None
        self._refresh_display()
        self.app.set_status("已重置 RFM 分析器")

    def _run_step(self, method_name):
        """运行单个 RFM 分析步骤。"""
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
        # 每步执行后都更新 rfm_df 引用（即使中间步骤也能显示）
        self.app.rfm_df = self.app.rfm_analyzer.rfm
        self._refresh_display()
        self.app.set_status(f"已执行：{method_name}")

    # ───── 显示更新 ─────

    def _refresh_display(self):
        """更新状态 + 8 类分布 + RFM 表预览。"""
        rfm = self.app.rfm_df

        # 清空两个 Treeview
        for item in self.dist_tree.get_children():
            self.dist_tree.delete(item)
        for item in self.rfm_tree.get_children():
            self.rfm_tree.delete(item)

        if rfm is None:
            self.status_var.set("状态：尚未分析")
            return

        self.status_var.set(f"状态：已分析 {len(rfm)} 个客户")

        # ───── 填 8 类分布 ─────
        # 只有 Label 列存在时才能算分布
        if "Label" in rfm.columns:
            counts = rfm["Label"].value_counts()
            total = counts.sum()
            for label, count in counts.items():
                ratio = f"{count / total * 100:.1f}%"
                self.dist_tree.insert("", "end", values=(label, count, ratio))

        # ───── 填 RFM 表预览（前 10 行）─────
        preview = rfm.head(10)
        # CustomerID 是索引，要单独加成第一列
        columns = ["CustomerID"] + list(preview.columns)
        self.rfm_tree["columns"] = columns
        for col in columns:
            self.rfm_tree.heading(col, text=col)
            self.rfm_tree.column(col, width=100, anchor="center")
        for cid, row in preview.iterrows():
            values = [cid] + [self._fmt(v) for v in row]
            self.rfm_tree.insert("", "end", values=values)

    def _fmt(self, v):
        """统一格式化：浮点保留 2 位、整数原样、其他 str()。"""
        if isinstance(v, float):
            return f"{v:.2f}"
        return str(v)
