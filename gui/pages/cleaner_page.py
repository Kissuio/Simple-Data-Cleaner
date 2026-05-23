"""数据清洗标签页 —— 对应 DataCleaner 类的入口。

功能：
- 一键全清洗：调 clean_all() 一次跑完 5 步
- 5 个分步按钮：单独跑某一步（答辩演示用）
- 重置：重新创建 DataCleaner，回到未清洗状态
- 数据状态显示：原始行数 / 当前行数
- 清洗日志：滚动显示 cleaner.log
"""

from tkinter import ttk, messagebox
import tkinter as tk

from data_handlers.data_cleaner import DataCleaner


class CleanerPage(ttk.Frame):
    """数据清洗标签页。"""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.info_var = tk.StringVar(value="当前数据状态：尚未加载数据")
        self._build_ui()

    def _build_ui(self):
        """搭页面：顶部按钮区 + 中间数据状态 + 下方日志框。"""

        # ───── 顶部操作区 ─────
        action_frame = ttk.Frame(self, padding=10)
        action_frame.pack(fill="x")

        # 第 1 行：一键全清洗 + 重置
        row1 = ttk.Frame(action_frame)
        row1.pack(fill="x")
        ttk.Button(
            row1, text="一键全清洗", command=self._on_clean_all,
            style="Action.TButton",
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            row1, text="重置", command=self._on_reset,
            style="Action.TButton",
        ).pack(side="left")

        # 第 2 行：5 个分步按钮（用 LabelFrame 包起来，看着像一组）
        step_frame = ttk.LabelFrame(action_frame, text="分步执行（可单独跑某一步，答辩演示用）", padding=10)
        step_frame.pack(fill="x", pady=(10, 0))

        step_buttons = [
            ("1. 删 CustomerID 缺失", lambda: self._run_step("drop_missing_customer_id")),
            ("2. 删取消订单", lambda: self._run_step("drop_cancellations")),
            ("3. 删非产品代码", lambda: self._run_step("drop_non_product_codes")),
            ("4. 时间转换", lambda: self._run_step("convert_date")),
            ("5. 加 TotalPrice", lambda: self._run_step("add_total_price")),
        ]
        for text, cmd in step_buttons:
            ttk.Button(
                step_frame, text=text, command=cmd, style="Action.TButton",
            ).pack(side="left", padx=4)

        # ───── 数据状态显示 ─────
        info_label = ttk.Label(
            self, textvariable=self.info_var, font=("SimHei", 11), padding=10
        )
        info_label.pack(fill="x")

        # ───── 清洗日志 ─────
        log_label = ttk.Label(
            self, text="清洗日志：", font=("SimHei", 11, "bold"), padding=(10, 5)
        )
        log_label.pack(anchor="w")

        log_frame = ttk.Frame(self, padding=10)
        log_frame.pack(fill="both", expand=True)

        # Text 控件：多行文本显示，配 Scrollbar
        self.log_text = tk.Text(log_frame, height=10, font=("SimHei", 10), wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set, state="disabled")

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ───── 按钮回调 ─────

    def _ensure_loader(self):
        """检查数据已加载，未加载则弹框提示。返回 True/False。"""
        if self.app.loader is None or self.app.loader.df is None:
            messagebox.showwarning("数据未加载", "请先在【主页/数据】加载 CSV 文件。")
            return False
        return True

    def _on_clean_all(self):
        """一键全清洗：新建 DataCleaner + clean_all。"""
        if not self._ensure_loader():
            return
        try:
            cleaner = DataCleaner(self.app.loader.df)
            cleaner.clean_all()
        except Exception as e:
            messagebox.showerror("清洗失败", f"执行清洗时出错：\n{e}")
            return
        self.app.cleaner = cleaner
        self._refresh_display()
        self.app.set_status(f"已完成全部清洗：{len(cleaner.df)} 行")

    def _on_reset(self):
        """重置：重新创建 DataCleaner（基于原始数据），回到未清洗状态。
        同时清空下游 RFM 状态，避免页面间数据不一致。
        """
        if not self._ensure_loader():
            return
        self.app.cleaner = DataCleaner(self.app.loader.df)
        # 下游清空：清洗都重置了，RFM 结果当然也不该保留
        self.app.rfm_analyzer = None
        self.app.rfm_df = None
        self._refresh_display()
        self.app.set_status("已重置：cleaner + RFM 结果都清空，回到未清洗状态")

    def _run_step(self, method_name):
        """运行单个清洗步骤。method_name 是 DataCleaner 的方法名。"""
        if not self._ensure_loader():
            return
        # 如果 app.cleaner 还没创建，自动建一个
        if self.app.cleaner is None:
            self.app.cleaner = DataCleaner(self.app.loader.df)
        try:
            method = getattr(self.app.cleaner, method_name)
            method()
        except Exception as e:
            messagebox.showerror("步骤失败", f"执行 {method_name} 时出错：\n{e}")
            return
        self._refresh_display()
        self.app.set_status(f"已执行：{method_name}，当前 {len(self.app.cleaner.df)} 行")

    # ───── 显示更新 ─────

    def _refresh_display(self):
        """更新数据状态 + 清洗日志显示。"""
        loader_df = self.app.loader.df if self.app.loader else None
        cleaner_df = self.app.cleaner.df if self.app.cleaner else None

        # 行数对比
        if loader_df is None:
            self.info_var.set("当前数据状态：尚未加载数据")
        elif cleaner_df is None:
            self.info_var.set(f"当前数据状态：原始 {len(loader_df)} 行（未清洗）")
        else:
            self.info_var.set(
                f"当前数据状态：原始 {len(loader_df)} 行  →  当前 {len(cleaner_df)} 行"
            )

        # 日志：从 cleaner.log 读
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        if self.app.cleaner is not None and self.app.cleaner.log:
            for line in self.app.cleaner.log:
                self.log_text.insert("end", f"- {line}\n")
        else:
            self.log_text.insert("end", "（无日志）")
        self.log_text.configure(state="disabled")
