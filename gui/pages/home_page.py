"""主页 / 数据加载标签页 —— 对应 FileLoader 类的入口。

功能：
- 选择 CSV 文件（filedialog）
- 自动调用 FileLoader.load_file() 加载
- 显示行列数 + 前 10 行预览（Treeview）
- 加载成功后把 loader 存到 self.app.loader，供其他页面使用
"""

from tkinter import ttk, filedialog, messagebox
import tkinter as tk

from data_handlers.file_loader import FileLoader


class HomePage(ttk.Frame):
    """主页 / 数据加载标签页。"""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.file_path_var = tk.StringVar(value="（未选择）")
        self.info_var = tk.StringVar(value="原始数据信息：尚未加载")
        self._build_ui()

    def _build_ui(self):
        """搭页面：顶部文件选择区 + 中间信息区 + 下方预览表格。"""
        # ───── 文件选择行 ─────
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill="x")

        select_btn = ttk.Button(
            top_frame,
            text="选择 CSV 文件",
            command=self._on_select_file,
            style="Action.TButton",
        )
        select_btn.pack(side="left")

        file_label = ttk.Label(
            top_frame, textvariable=self.file_path_var, foreground="gray"
        )
        file_label.pack(side="left", padx=10)

        # ───── 信息行 ─────
        info_label = ttk.Label(
            self, textvariable=self.info_var, font=("SimHei", 11), padding=10
        )
        info_label.pack(fill="x")

        # ───── 数据预览（Treeview 表格）─────
        preview_label = ttk.Label(
            self, text="数据预览（前 10 行）：", font=("SimHei", 11, "bold"), padding=(10, 5)
        )
        preview_label.pack(anchor="w")

        # Treeview 容器（含横向滚动条）
        preview_frame = ttk.Frame(self, padding=10)
        preview_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(preview_frame, show="headings", height=10)
        # 双滚动条：横向（列宽超出）+ 纵向（虽然只有 10 行通常不需要，但保险起见）
        xscroll = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.tree.xview)
        yscroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)

    def _on_select_file(self):
        """[按钮回调] 选文件 → 加载 → 显示信息和预览。"""
        # 弹出文件选择对话框，限定 CSV/Excel
        path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[
                ("CSV 文件", "*.csv"),
                ("Excel 文件", "*.xlsx *.xls"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            # 用户取消了对话框
            return

        # 显示路径
        self.file_path_var.set(f"文件: {path}")

        # 尝试加载，失败弹错误框
        try:
            loader = FileLoader(path)
            loader.load_file()
        except Exception as e:
            messagebox.showerror("加载失败", f"无法加载文件：\n{e}")
            self.info_var.set("原始数据信息：加载失败")
            return

        # 加载成功，挂到 app 共享，供其他页面用
        self.app.loader = loader
        df = loader.df
        self.info_var.set(f"原始数据信息：行数 {len(df)} / 列数 {len(df.columns)}")

        # 更新表格预览
        self._render_preview(df.head(10))

        # 更新全局状态栏
        self.app.set_status(f"已加载: {path}（{len(df)} 行，{len(df.columns)} 列）")

    def _render_preview(self, df_preview):
        """把 DataFrame 前几行渲染到 Treeview。"""
        # 清空旧数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        # 重新配置列
        self.tree["columns"] = list(df_preview.columns)
        for col in df_preview.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")
        # 插入数据行
        for _, row in df_preview.iterrows():
            # str(v) 处理 NaN / 时间戳 / 数字等各种类型
            values = [str(v) for v in row]
            self.tree.insert("", "end", values=values)
