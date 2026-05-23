"""商品分析标签页 —— 对应 product_analysis.py 函数模块的入口。

功能：
- [TOP10 销量] 按钮：调 get_top_quantity + plot_top_quantity
- [TOP10 销售额] 按钮：调 get_top_revenue + plot_top_revenue
- [单价分布] 按钮：调 get_price_distribution + plot_price_distribution
- 图片在 GUI 内嵌预览（PIL）+ 业务洞察文字

依赖：self.app.cleaner.df（需要清洗完成，含 TotalPrice / Description / Quantity / UnitPrice）
"""

from tkinter import ttk, messagebox
import tkinter as tk
from PIL import Image, ImageTk

from analyzer.product_analysis import (
    get_top_quantity, get_top_revenue, get_price_distribution,
)
from visualization.visualizer import Visualizer


# 业务洞察文字（report 现成材料，分点列表）
INSIGHTS = {
    "top_quantity": (
        "• 销量冠军：WORLD WAR 2 GLIDERS ASSTD DESIGNS（玩具滑翔机），全年 54223 件\n"
        "• 单价低、走量快，属薄利多销型\n"
        "• 销量榜多为低单价小商品（玩具、爆米花筒、包装盒等）"
    ),
    "top_revenue": (
        "• 销售额冠军：REGENCY CAKESTAND 3 TIER（三层蛋糕架），£134,770\n"
        "• 单价高、量价齐升，属高客单价稳销型\n"
        "• 销售额榜多为家居装饰类、节日礼品类商品\n"
        "• 两榜交集 4 个「明星商品」（量价齐升）：WHITE HANGING HEART / JUMBO BAG RED RETROSPOT / "
        "ASSORTED COLOUR BIRD ORNAMENT / RABBIT NIGHT LIGHT"
    ),
    "price_distribution": (
        "• 双峰分布：主峰约 £1-2（最高 7 万+笔），次峰约 £4\n"
        "• 99% 商品单价 < £13，中位数 £1.85\n"
        "• 最大值 £649.5，但 >£100 仅 101 笔（占比万分之 2.6）\n"
        "• 典型电商右偏长尾分布，图用 log x 轴 + np.logspace 等距 bins 处理"
    ),
}


class ProductPage(ttk.Frame):
    """商品分析标签页。"""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        # PhotoImage 必须保留引用（Tkinter 著名坑）
        self.current_photo = None
        self.insight_var = tk.StringVar(value="（请点击上方按钮生成图表）")
        self._build_ui()

    def _build_ui(self):
        # ───── 顶部操作区 ─────
        action_frame = ttk.Frame(self, padding=10)
        action_frame.pack(fill="x")
        ttk.Button(
            action_frame, text="TOP10 销量", command=self._on_top_quantity,
            style="Action.TButton",
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            action_frame, text="TOP10 销售额", command=self._on_top_revenue,
            style="Action.TButton",
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            action_frame, text="单价分布", command=self._on_price_distribution,
            style="Action.TButton",
        ).pack(side="left")

        # ───── 图片预览区 ─────
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
                "商品分析需要 TotalPrice 列。\n请回到【数据清洗】点【一键全清洗】。",
            )
            return False
        return True

    def _get_visualizer(self):
        """懒加载共享 Visualizer 实例。"""
        if self.app.visualizer is None:
            self.app.visualizer = Visualizer()
        return self.app.visualizer

    def _on_top_quantity(self):
        if not self._ensure_cleaner():
            return
        try:
            top = get_top_quantity(self.app.cleaner.df)
            path = self._get_visualizer().plot_top_quantity(top)
        except Exception as e:
            messagebox.showerror("生成失败", f"生成 TOP10 销量图时出错：\n{e}")
            return
        self._show_image(path)
        self.insight_var.set(INSIGHTS["top_quantity"])
        self.app.set_status(f"已生成：{path}")

    def _on_top_revenue(self):
        if not self._ensure_cleaner():
            return
        try:
            top = get_top_revenue(self.app.cleaner.df)
            path = self._get_visualizer().plot_top_revenue(top)
        except Exception as e:
            messagebox.showerror("生成失败", f"生成 TOP10 销售额图时出错：\n{e}")
            return
        self._show_image(path)
        self.insight_var.set(INSIGHTS["top_revenue"])
        self.app.set_status(f"已生成：{path}")

    def _on_price_distribution(self):
        if not self._ensure_cleaner():
            return
        try:
            prices = get_price_distribution(self.app.cleaner.df)
            path = self._get_visualizer().plot_price_distribution(prices)
        except Exception as e:
            messagebox.showerror("生成失败", f"生成单价分布图时出错：\n{e}")
            return
        self._show_image(path)
        self.insight_var.set(INSIGHTS["price_distribution"])
        self.app.set_status(f"已生成：{path}")

    # ───── 图片显示 ─────

    def _show_image(self, path):
        """加载 PNG 并显示到 image_label。"""
        try:
            img = Image.open(path)
            img.thumbnail((1180, 650))
            photo = ImageTk.PhotoImage(img)
        except Exception as e:
            messagebox.showerror("加载图片失败", f"无法加载 {path}：\n{e}")
            return
        self.image_label.configure(image=photo, text="")
        # 关键：保留引用防 GC
        self.current_photo = photo
