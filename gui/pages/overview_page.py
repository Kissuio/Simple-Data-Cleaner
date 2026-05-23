"""图表总览标签页 —— Visualizer 8 张图的统一入口。

功能（V1）：
- [一键生成所有 8 张图] 按钮：依次跑全套 plot 方法 → 生成 8 张 PNG 到 output/
- 8 个缩略图横排显示，每个是带图的按钮
- 单击缩略图 → 大图预览
- [导出此图] 按钮：把选中的 PNG 复制到用户选的位置
- [AI 解读 →] 按钮：V1 占位，V2 跳转到 AI 解读页

依赖：cleaner.df（含 TotalPrice）+ rfm_df（含 Label）
"""

import shutil
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from PIL import Image, ImageTk

from analyzer.sales_trend import get_monthly_sales, get_weekday_hour_orders
from analyzer.product_analysis import (
    get_top_quantity, get_top_revenue, get_price_distribution,
)
from visualization.visualizer import Visualizer


# 8 张图清单：(显示名, PNG 文件名)
CHARTS = [
    ("饼图", "label_pie.png"),
    ("柱图", "label_avg_spend.png"),
    ("RFM 散点", "rfm_scatter.png"),
    ("月度趋势", "monthly_trend.png"),
    ("TOP10 销量", "top_quantity.png"),
    ("TOP10 销售额", "top_revenue.png"),
    ("单价分布", "price_distribution.png"),
    ("周热力图", "weekday_hour_heatmap.png"),
]


class OverviewPage(ttk.Frame):
    """图表总览标签页。"""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        # 保留 PhotoImage 引用，否则全被 GC 回收（Tkinter 著名坑）
        self.thumb_photos = []        # 8 个缩略图
        self.current_photo = None     # 大图预览
        self.current_index = -1        # 当前选中的图 index（-1 表示未选）
        self.selected_var = tk.StringVar(value="（尚未选择图表，请先生成）")
        self._build_ui()

    def _build_ui(self):
        # ───── 顶部操作行 ─────
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Button(
            top, text="一键生成所有 8 张图", command=self._on_generate_all,
            style="Action.TButton",
        ).pack(side="left")
        ttk.Button(
            top, text="AI 解读 →", command=self._on_ai,
            style="Action.TButton",
        ).pack(side="right")

        # ───── 缩略图条（8 个图文按钮横排） ─────
        thumb_frame = ttk.Frame(self, padding=(10, 0, 10, 5))
        thumb_frame.pack(fill="x")
        self.thumb_buttons = []
        for i, (name, _) in enumerate(CHARTS):
            # lambda idx=i 捕获当前 i，避免闭包陷阱
            btn = ttk.Button(
                thumb_frame,
                text=name,
                command=lambda idx=i: self._show_chart(idx),
                compound="top",  # 图在上、文字在下
                width=14,
            )
            btn.pack(side="left", padx=2)
            self.thumb_buttons.append(btn)

        # ───── 大图预览区 ─────
        self.image_label = ttk.Label(
            self, text="（点击上方缩略图查看大图）",
            anchor="center", font=("SimHei", 12), foreground="gray",
        )
        self.image_label.pack(fill="both", expand=True, padx=10, pady=5)

        # ───── 底部操作行 ─────
        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill="x")
        ttk.Label(
            bottom, textvariable=self.selected_var, font=("SimHei", 11)
        ).pack(side="left")
        ttk.Button(
            bottom, text="导出此图...", command=self._on_export,
            style="Action.TButton",
        ).pack(side="right")

    # ───── 数据校验 ─────

    def _ensure_data(self):
        """检查 cleaner（含 TotalPrice） + rfm_df（含 Label）齐备。"""
        if self.app.cleaner is None or "TotalPrice" not in self.app.cleaner.df.columns:
            messagebox.showwarning(
                "数据未准备",
                "请先在【数据清洗】点【一键全清洗】（需要 TotalPrice 列）。",
            )
            return False
        if self.app.rfm_df is None or "Label" not in self.app.rfm_df.columns:
            messagebox.showwarning(
                "数据未准备",
                "请先在【RFM 分析】点【一键全分析】（需要 Label 列）。",
            )
            return False
        return True

    def _get_visualizer(self):
        if self.app.visualizer is None:
            self.app.visualizer = Visualizer()
        return self.app.visualizer

    # ───── 按钮回调 ─────

    def _on_generate_all(self):
        """一键生成所有 8 张图。"""
        if not self._ensure_data():
            return
        viz = self._get_visualizer()
        df = self.app.cleaner.df
        rfm = self.app.rfm_df
        try:
            viz.plot_label_pie(rfm)
            viz.plot_label_avg_spend(rfm)
            viz.plot_rfm_scatter(rfm)
            viz.plot_monthly_trend(get_monthly_sales(df))
            viz.plot_top_quantity(get_top_quantity(df))
            viz.plot_top_revenue(get_top_revenue(df))
            viz.plot_price_distribution(get_price_distribution(df))
            viz.plot_weekday_hour_heatmap(get_weekday_hour_orders(df))
        except Exception as e:
            messagebox.showerror("生成失败", f"生成过程中出错：\n{e}")
            return
        # 把生成好的 PNG 加载成缩略图显示到按钮上
        self._refresh_thumbs()
        self.app.set_status("8 张图全部生成完成（output/ 目录）")

    def _refresh_thumbs(self):
        """把 8 张 PNG 加载成缩略图，配到对应按钮。"""
        self.thumb_photos = []  # 清空旧引用
        for i, (name, fname) in enumerate(CHARTS):
            path = f"output/{fname}"
            try:
                img = Image.open(path)
                img.thumbnail((130, 80))
                photo = ImageTk.PhotoImage(img)
            except Exception:
                continue
            self.thumb_buttons[i].configure(image=photo)
            self.thumb_photos.append(photo)

    def _show_chart(self, index):
        """点缩略图 → 加载大图到预览区。"""
        name, fname = CHARTS[index]
        path = f"output/{fname}"
        if not Path(path).exists():
            messagebox.showinfo(
                "图未生成",
                f"图【{name}】尚未生成。\n请先点【一键生成所有 8 张图】。",
            )
            return
        try:
            img = Image.open(path)
            # 大图预览：留出顶部按钮+缩略图条+底部按钮+状态栏的空间
            img.thumbnail((1180, 580))
            photo = ImageTk.PhotoImage(img)
        except Exception as e:
            messagebox.showerror("加载失败", f"无法加载 {path}：\n{e}")
            return
        self.image_label.configure(image=photo, text="")
        self.current_photo = photo
        self.current_index = index
        self.selected_var.set(f"当前选中：{name}（{path}）")

    def _on_export(self):
        """导出选中的图到用户指定位置（shutil.copy）。"""
        if self.current_index < 0:
            messagebox.showwarning("未选择", "请先点上方缩略图选中一张图。")
            return
        name, fname = CHARTS[self.current_index]
        src = f"output/{fname}"
        dst = filedialog.asksaveasfilename(
            title=f"导出 {name}",
            defaultextension=".png",
            filetypes=[("PNG 图片", "*.png"), ("所有文件", "*.*")],
            initialfile=fname,
        )
        if not dst:
            return
        try:
            shutil.copy(src, dst)
        except Exception as e:
            messagebox.showerror("导出失败", str(e))
            return
        self.app.set_status(f"已导出 {name} → {dst}")
        messagebox.showinfo("导出成功", f"图已保存到：\n{dst}")

    def _on_ai(self):
        """V1 占位：弹消息提示，V2 改成跳转到 AI 解读页。"""
        messagebox.showinfo(
            "AI 解读（V2 功能）",
            "AI 解读功能将在 V2 实现。\n届时点击此按钮会跳转到 AI 解读页面。",
        )
