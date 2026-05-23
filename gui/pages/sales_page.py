"""销售分析标签页 —— 对应 sales_trend.py 函数模块的入口。

功能：
- [查看月度趋势] 按钮：调 get_monthly_sales + plot_monthly_trend → 显示 PNG
- [查看周热力图] 按钮：调 get_weekday_hour_orders + plot_weekday_hour_heatmap → 显示 PNG
- 图片在 GUI 内嵌预览（PIL 加载 + 等比缩放）
- 业务洞察文字随当前图变化

依赖：self.app.cleaner.df（需要清洗完成，含 InvoiceDate datetime / TotalPrice / InvoiceNo）
"""

from tkinter import ttk, messagebox
import tkinter as tk
from PIL import Image, ImageTk

from analyzer.sales_trend import get_monthly_sales, get_weekday_hour_orders
from visualization.visualizer import Visualizer


# 业务洞察文字（report 现成材料，每张图配一段，分点列表更易读）
INSIGHTS = {
    "monthly_trend": (
        "• 销售额从 2010-12 起波动上升，9-11 月明显爬升至全年峰值\n"
        "• 11 月峰值约 ￡1,150,000（对应西方圣诞季备货高峰）\n"
        "• 12 月数据截至 2011-12-09 未完整，图中已用 .iloc[:-1] 切掉残月"
    ),
    "weekday_hour_heatmap": (
        "• 全周订单峰值：周三 12 点 604 单 / 次峰：周四 12 点 580 单\n"
        "• 周六完全不营业（整行为 0）\n"
        "• 凌晨 0-6 点 + 深夜 21-23 点都不营业\n"
        "• 周四 17-20 点异常活跃（其他工作日傍晚都接近 0）\n"
        "• 周日营业时段更短（仅 10-16 点）\n"
        "• 用订单数（InvoiceNo.nunique）而非销售额，避免大额订单偏差"
    ),
}


class SalesPage(ttk.Frame):
    """销售分析标签页。"""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        # PhotoImage 必须保留引用，否则被 GC 回收 → 图不显示（Tkinter 著名坑）
        self.current_photo = None
        self.insight_var = tk.StringVar(value="（请点击上方按钮生成图表）")
        self._build_ui()

    def _build_ui(self):
        # ───── 顶部操作区 ─────
        action_frame = ttk.Frame(self, padding=10)
        action_frame.pack(fill="x")
        ttk.Button(
            action_frame, text="查看月度趋势", command=self._on_monthly_trend,
            style="Action.TButton",
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            action_frame, text="查看周热力图", command=self._on_weekday_hour,
            style="Action.TButton",
        ).pack(side="left")

        # ───── 图片预览区 ─────
        # 用 Label 显示图片。无图时显示占位文字。
        self.image_label = ttk.Label(
            self,
            text="（图表将显示在这里）",
            anchor="center",
            font=("SimHei", 12),
            foreground="gray",
        )
        self.image_label.pack(fill="both", expand=True, padx=10, pady=5)

        # ───── 业务洞察文字 ─────
        insight_frame = ttk.LabelFrame(self, text="业务洞察", padding=15)
        insight_frame.pack(fill="x", padx=10, pady=(5, 10))
        insight_label = ttk.Label(
            insight_frame,
            textvariable=self.insight_var,
            wraplength=1000,
            justify="left",
            font=("SimHei", 12),
        )
        insight_label.pack(fill="x", anchor="w", padx=5, pady=5)

    # ───── 按钮回调 ─────

    def _ensure_cleaner(self):
        """检查清洗完整（依赖 TotalPrice 列）。"""
        if self.app.cleaner is None or self.app.cleaner.df is None:
            messagebox.showwarning(
                "尚未清洗数据",
                "请先在【数据清洗】标签页执行清洗（推荐【一键全清洗】）。",
            )
            return False
        if "TotalPrice" not in self.app.cleaner.df.columns:
            messagebox.showwarning(
                "清洗不完整",
                "销售分析需要 TotalPrice 列。\n请回到【数据清洗】点【一键全清洗】。",
            )
            return False
        return True

    def _get_visualizer(self):
        """懒加载共享 Visualizer 实例。"""
        if self.app.visualizer is None:
            self.app.visualizer = Visualizer()
        return self.app.visualizer

    def _on_monthly_trend(self):
        """生成 + 显示月度趋势图。"""
        if not self._ensure_cleaner():
            return
        try:
            monthly = get_monthly_sales(self.app.cleaner.df)
            path = self._get_visualizer().plot_monthly_trend(monthly)
        except Exception as e:
            messagebox.showerror("生成失败", f"生成月度趋势图时出错：\n{e}")
            return
        self._show_image(path)
        self.insight_var.set(INSIGHTS["monthly_trend"])
        self.app.set_status(f"已生成：{path}")

    def _on_weekday_hour(self):
        """生成 + 显示周热力图。"""
        if not self._ensure_cleaner():
            return
        try:
            pivot = get_weekday_hour_orders(self.app.cleaner.df)
            path = self._get_visualizer().plot_weekday_hour_heatmap(pivot)
        except Exception as e:
            messagebox.showerror("生成失败", f"生成周热力图时出错：\n{e}")
            return
        self._show_image(path)
        self.insight_var.set(INSIGHTS["weekday_hour_heatmap"])
        self.app.set_status(f"已生成：{path}")

    # ───── 图片显示 ─────

    def _show_image(self, path):
        """加载 PNG 并显示到 image_label。"""
        try:
            img = Image.open(path)
            # 等比缩放到适配当前窗口的预览区
            img.thumbnail((1180, 650))
            photo = ImageTk.PhotoImage(img)
        except Exception as e:
            messagebox.showerror("加载图片失败", f"无法加载 {path}：\n{e}")
            return
        self.image_label.configure(image=photo, text="")
        # 关键：保留引用，否则 photo 被 Python GC 回收，图就消失
        self.current_photo = photo
