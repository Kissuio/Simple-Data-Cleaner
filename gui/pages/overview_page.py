"""图表总览页 —— 报告浏览器（customtkinter 版本）。"""

import shutil
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from analyzer.product_analysis import (
    get_price_distribution,
    get_top_quantity,
    get_top_revenue,
)
from analyzer.sales_trend import get_monthly_sales, get_weekday_hour_orders
from visualization.visualizer import Visualizer
from gui.pages.base_page import BasePage
from gui.widgets import (
    BORDER_WIDTH,
    MetricCard,
    UI_COLORS as COLORS,
    OVERVIEW_CHART_KEYS,
    PRODUCT_CHART_KEYS,
    SALES_CHART_KEYS,
    build_workflow_nav,
    mark_chart_progress,
    refresh_workflow_nav,
)


CHART_BOX_SIZE = (720, 540)

CHARTS = [
    ("饼图", "label_pie.png", "RFM 客户 8 类占比", "回答：不同客户类型占整体客户池的比例是多少。"),
    ("柱图", "label_avg_spend.png", "各类客户人均消费", "回答：哪类客户的人均消费金额更高。"),
    ("RFM 散点", "rfm_scatter.png", "RFM 客户分布气泡图", "回答：客户在 Recency / Frequency / Monetary 空间中的分布。"),
    ("月度趋势", "monthly_trend.png", "月度销售趋势", "回答：销售额随月份变化的趋势和旺季峰值。"),
    ("TOP10 销量", "top_quantity.png", "TOP10 热销商品", "回答：哪些商品最走量，适合做引流或补货关注。"),
    ("TOP10 销售额", "top_revenue.png", "TOP10 高销售额商品", "回答：哪些商品贡献最高营收。"),
    ("单价分布", "price_distribution.png", "成交单价分布", "回答：商品价格带集中在哪里，是否存在长尾。"),
    ("周热力图", "weekday_hour_heatmap.png", "订单数热力图", "回答：订单集中在星期几和哪个小时段。"),
]


class ChartListItem(ctk.CTkButton):
    """右侧图表目录按钮。"""

    def __init__(self, parent, name, title, command):
        super().__init__(
            parent,
            text=f"{name}\n{title}",
            command=command,
            fg_color="#ffffff",
            hover_color=COLORS["blue_soft"],
            text_color=COLORS["text"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            font=("SimHei", 11, "bold"),
            anchor="w",
            height=54,
            corner_radius=8,
        )
        self.generated = False

    def set_generated(self, generated, selected=False):
        self.generated = generated
        if selected:
            self.configure(
                fg_color=COLORS["blue_soft"],
                border_color=COLORS["blue"],
                text_color=COLORS["blue"],
            )
        elif generated:
            self.configure(
                fg_color=COLORS["green_soft"],
                border_color=COLORS["green"],
                text_color=COLORS["text"],
            )
        else:
            self.configure(
                fg_color="#ffffff",
                border_color=COLORS["border"],
                text_color=COLORS["text"],
            )


class OverviewPage(BasePage):
    """图表总览页。流程终点，不传 next_page。"""

    def __init__(self, master, app):
        super().__init__(
            master,
            app,
            title="图表总览",
            requires="rfm+cleaner",
        )
        self.current_image = None
        self.current_index = -1
        self.chart_buttons = []
        self.nav_items = {}
        self.metric_vars = {}
        self.chart_title_var = ctk.StringVar(value="图表预览")
        self.selected_var = ctk.StringVar(value="尚未选择图表")
        self.explain_var = ctk.StringVar(value="先生成图表，再从右侧目录选择一张查看。")
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
        self._build_report_area(main)

    def _build_workflow_nav(self, parent):
        return build_workflow_nav(parent, self.app, "图表总览", self.nav_items)

    def _build_metrics(self, parent):
        metrics = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        metrics.grid(row=0, column=0, sticky="ew")
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1, uniform="overview_metric")

        specs = [
            ("已生成图表", "generated", COLORS["blue"]),
            ("当前选择", "selected", COLORS["purple"]),
            ("数据状态", "data_state", COLORS["green"]),
            ("输出目录", "output", COLORS["amber"]),
        ]
        for col, (title, key, accent) in enumerate(specs):
            value_var = ctk.StringVar(value="--")
            note_var = ctk.StringVar(value="等待生成")
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
            text="报告操作",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            panel,
            text="一键生成 8 张图后，可在右侧目录逐张查看、导出或交给 AI 解读。",
            font=("SimHei", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        buttons = ctk.CTkFrame(panel, fg_color="transparent", corner_radius=0)
        buttons.grid(row=0, column=1, rowspan=2, sticky="e", padx=18)

        ctk.CTkButton(
            buttons,
            text="生成全部图表",
            command=self._on_generate_all,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=128,
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="导出此图",
            command=self._on_export,
            fg_color=COLORS["green"],
            hover_color=COLORS["green_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=104,
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="AI 解读",
            command=self._on_ai,
            fg_color=COLORS["purple"],
            hover_color=COLORS["purple_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=96,
            corner_radius=6,
        ).pack(side="left")

    def _build_report_area(self, parent):
        area = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        area.grid(row=2, column=0, sticky="nsew")
        # column=0 吃完剩余宽度；column=1 锁定 320 不再被右侧栏内容变化牵动，
        # 这样点目录按钮触发的 customtkinter 重绘不会重新分配 column=0 大小，
        # 左侧 preview_panel / image_slot 的边框就不会"挥动"。
        area.grid_columnconfigure(0, weight=1)
        area.grid_columnconfigure(1, weight=0, minsize=320)
        area.grid_rowconfigure(0, weight=1)

        preview_panel = ctk.CTkFrame(
            area,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        preview_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        preview_panel.grid_columnconfigure(0, weight=1)
        preview_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            preview_panel,
            textvariable=self.chart_title_var,
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        # 【诊断】image_slot 改成透明 + 无圆角，绕开 customtkinter canvas 重绘可能引起的颤动。
        # preview_panel 自身就是白底，image_slot 透明视觉效果不变。
        self.image_slot = ctk.CTkFrame(
            preview_panel,
            fg_color="transparent",
            corner_radius=0,
            width=CHART_BOX_SIZE[0],
            height=CHART_BOX_SIZE[1],
        )
        self.image_slot.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.image_slot.grid_propagate(False)
        self.image_slot.pack_propagate(False)

        self.image_label = ctk.CTkLabel(
            self.image_slot,
            text="生成图表后，从右侧目录选择一张进行预览。",
            font=("SimHei", 13),
            text_color=COLORS["muted"],
            fg_color="transparent",
        )
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        side = ctk.CTkFrame(area, fg_color="transparent", corner_radius=0)
        side.grid(row=0, column=1, sticky="nsew")
        side.grid_columnconfigure(0, weight=1)
        side.grid_rowconfigure(0, weight=2)
        side.grid_rowconfigure(1, weight=1)

        self._build_chart_list(side)
        self._build_explain_panel(side)

    def _build_chart_list(self, parent):
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
            text="图表目录",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent", corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        scroll.grid_columnconfigure(0, weight=1)

        self.chart_buttons = []
        for index, (name, _, title, _) in enumerate(CHARTS):
            button = ChartListItem(
                scroll,
                name=name,
                title=title,
                command=lambda idx=index: self._show_chart(idx),
            )
            button.grid(row=index, column=0, sticky="ew", pady=4)
            self.chart_buttons.append(button)

    def _build_explain_panel(self, parent):
        panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        panel.grid(row=1, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            panel,
            text="图表说明",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 4))

        ctk.CTkLabel(
            panel,
            textvariable=self.selected_var,
            font=("SimHei", 11, "bold"),
            text_color=COLORS["blue"],
            anchor="w",
            wraplength=260,
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(
            panel,
            textvariable=self.explain_var,
            font=("SimHei", 12),
            text_color=COLORS["text"],
            justify="left",
            anchor="nw",
            wraplength=260,
        ).grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))

    def on_show(self):
        super().on_show()
        self._refresh_chart_status()
        self._refresh_nav_state()

    def _ensure_data(self):
        """检查 cleaner（含 TotalPrice）+ rfm_df（含 Label）齐备。"""
        if self.app.cleaner is None or self.app.cleaner.df is None or "TotalPrice" not in self.app.cleaner.df.columns:
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

    def _on_generate_all(self):
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
        mark_chart_progress(self.app, "sales", SALES_CHART_KEYS)
        mark_chart_progress(self.app, "product", PRODUCT_CHART_KEYS)
        mark_chart_progress(self.app, "overview", OVERVIEW_CHART_KEYS)
        self._refresh_chart_status()
        self._refresh_nav_state()
        self._show_chart(0)
        self.app.set_status("8 张图全部生成完成（output/ 目录）")

    def _show_chart(self, index):
        name, fname, title, explanation = CHARTS[index]
        path = Path("output") / fname
        if not path.exists():
            messagebox.showinfo(
                "图未生成",
                f"图【{name}】尚未生成。\n请先点【生成全部图表】。",
            )
            return
        try:
            img = Image.open(path)
            img.thumbnail(CHART_BOX_SIZE)
            ctk_img = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=img.size,
            )
        except Exception as e:
            messagebox.showerror("加载失败", f"无法加载 {path}：\n{e}")
            return

        self.image_label.configure(image=ctk_img, text="")
        self.current_image = ctk_img
        # 增量切换按钮选中态：只动旧+新两个按钮，避免 _refresh_chart_status
        # 循环 configure 8 个按钮触发右侧栏 layout 重排（颤动主因）
        self._select_chart_button(index)
        self.current_index = index
        self.chart_title_var.set(title)
        self.selected_var.set(f"当前选中：{name}")
        self.explain_var.set(f"{explanation}\n\n文件：{path}")
        self._set_metric("selected", name, "当前预览")

    def _on_export(self):
        """导出选中图到用户指定位置。"""
        if self.current_index < 0:
            messagebox.showwarning("未选择", "请先从右侧图表目录选中一张图。")
            return
        name, fname, _, _ = CHARTS[self.current_index]
        src = Path("output") / fname
        if not src.exists():
            messagebox.showwarning("图未生成", "当前图表文件不存在，请重新生成。")
            return
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
        """弹出 AI 解读独立窗口。"""
        from gui.ai_dialog import AIDialog

        AIDialog(self, self.app)

    def _select_chart_button(self, new_index):
        """只切换"旧选中 → 取消、新选中 → 选中"两个按钮。

        相比 _refresh_chart_status 全量循环 8 个 configure，这里只动 2 个，
        customtkinter 重绘代价小得多，右侧栏几何不会被牵动。
        generated（绿框）状态由 _refresh_chart_status 在 on_show / 生成全部图后统一刷。
        """
        old_index = self.current_index
        if 0 <= old_index < len(self.chart_buttons):
            _, old_fname, _, _ = CHARTS[old_index]
            old_generated = (Path("output") / old_fname).exists()
            self.chart_buttons[old_index].set_generated(old_generated, selected=False)
        if 0 <= new_index < len(self.chart_buttons):
            _, new_fname, _, _ = CHARTS[new_index]
            new_generated = (Path("output") / new_fname).exists()
            self.chart_buttons[new_index].set_generated(new_generated, selected=True)

    def _refresh_chart_status(self):
        generated_count = 0
        for index, (_, fname, _, _) in enumerate(CHARTS):
            generated = (Path("output") / fname).exists()
            if generated:
                generated_count += 1
            selected = index == self.current_index
            if index < len(self.chart_buttons):
                self.chart_buttons[index].set_generated(generated, selected=selected)

        self._set_metric("generated", f"{generated_count}/8", "output 目录")
        if self.current_index >= 0:
            self._set_metric("selected", CHARTS[self.current_index][0], "当前预览")
        else:
            self._set_metric("selected", "--", "尚未选择")

        data_ready = (
            self.app.cleaner is not None
            and self.app.cleaner.df is not None
            and self.app.rfm_df is not None
            and "Label" in self.app.rfm_df.columns
        )
        self._set_metric("data_state", "已就绪" if data_ready else "待准备", "清洗 + RFM")
        self._set_metric("output", "output/", "PNG 文件")

    def _refresh_nav_state(self):
        refresh_workflow_nav(self.nav_items, self.app, "图表总览")

    def _set_metric(self, key, value, note):
        value_var, note_var = self.metric_vars[key]
        value_var.set(value)
        note_var.set(note)
