"""商品分析页 —— 商品运营工作台（customtkinter 版本）。"""

from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from analyzer.product_analysis import (
    get_top_quantity,
    get_top_revenue,
    get_price_distribution,
)
from visualization.visualizer import Visualizer
from gui.pages.base_page import BasePage
from gui.widgets import (
    BORDER_WIDTH,
    MetricCard,
    UI_COLORS as COLORS,
    build_workflow_nav,
    mark_chart_progress,
    refresh_workflow_nav,
)


CHART_BOX_SIZE = (720, 520)

INSIGHTS = {
    "empty": "选择上方图表后，这里会显示对应的商品运营洞察。",
    "top_quantity": (
        "• 销量冠军：WORLD WAR 2 GLIDERS ASSTD DESIGNS，全年 54223 件\n"
        "• 销量榜多为低单价小商品，适合做引流款和组合销售\n"
        "• 这类商品应关注库存周转，避免旺季断货"
    ),
    "top_revenue": (
        "• 销售额冠军：REGENCY CAKESTAND 3 TIER，约 £134,770\n"
        "• 销售额榜更能体现高客单价商品和稳定贡献商品\n"
        "• 可优先围绕榜单商品做关联推荐、节日陈列和复购运营"
    ),
    "price_distribution": (
        "• 单价呈明显右偏长尾，大部分商品集中在低价格带\n"
        "• 中位数约 £1.85，说明低价商品是交易主体\n"
        "• 高价商品数量少但可能贡献高毛利，适合单独制定运营策略"
    ),
}


class ProductPage(BasePage):
    """商品分析页。"""

    def __init__(self, master, app):
        super().__init__(
            master,
            app,
            title="商品分析",
            requires="cleaner",
            next_page="图表总览",
        )
        self.current_image = None
        self.metric_vars = {}
        self.nav_items = {}
        self.chart_title_var = ctk.StringVar(value="图表预览")
        self.insight_var = ctk.StringVar(value=INSIGHTS["empty"])
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
        self._build_analysis_area(main)

    def _build_workflow_nav(self, parent):
        return build_workflow_nav(parent, self.app, "商品分析", self.nav_items)

    def _build_metrics(self, parent):
        metrics = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        metrics.grid(row=0, column=0, sticky="ew")
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1, uniform="product_metric")

        specs = [
            ("商品数", "products", COLORS["blue"]),
            ("总销量", "quantity", COLORS["green"]),
            ("单价中位数", "median_price", COLORS["amber"]),
            ("销售额冠军", "top_revenue", COLORS["purple"]),
        ]
        for col, (title, key, accent) in enumerate(specs):
            value_var = ctk.StringVar(value="--")
            note_var = ctk.StringVar(value="等待清洗")
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
            text="商品图表",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            panel,
            text="从销量、销售额和价格带三个角度观察商品结构。",
            font=("SimHei", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        buttons = ctk.CTkFrame(panel, fg_color="transparent", corner_radius=0)
        buttons.grid(row=0, column=1, rowspan=2, sticky="e", padx=18)

        ctk.CTkButton(
            buttons,
            text="TOP10 销量",
            command=self._on_top_quantity,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=112,
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="TOP10 销售额",
            command=self._on_top_revenue,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=126,
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="单价分布",
            command=self._on_price_distribution,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=106,
            corner_radius=6,
        ).pack(side="left")

    def _build_analysis_area(self, parent):
        area = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        area.grid(row=2, column=0, sticky="nsew")
        area.grid_columnconfigure(0, weight=3)
        area.grid_columnconfigure(1, weight=1)
        area.grid_rowconfigure(0, weight=1)

        chart_panel = ctk.CTkFrame(
            area,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        chart_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        chart_panel.grid_columnconfigure(0, weight=1)
        chart_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            chart_panel,
            textvariable=self.chart_title_var,
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        self.image_slot = ctk.CTkFrame(
            chart_panel,
            fg_color="#ffffff",
            corner_radius=8,
            width=CHART_BOX_SIZE[0],
            height=CHART_BOX_SIZE[1],
        )
        self.image_slot.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.image_slot.grid_propagate(False)
        self.image_slot.pack_propagate(False)

        self.image_label = ctk.CTkLabel(
            self.image_slot,
            text="选择图表后将在这里显示 PNG 预览。",
            font=("SimHei", 13),
            text_color=COLORS["muted"],
            fg_color="transparent",
        )
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        insight_panel = ctk.CTkFrame(
            area,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        insight_panel.grid(row=0, column=1, sticky="nsew")
        insight_panel.grid_columnconfigure(0, weight=1)
        insight_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            insight_panel,
            text="商品洞察",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        ctk.CTkLabel(
            insight_panel,
            textvariable=self.insight_var,
            font=("SimHei", 12),
            text_color=COLORS["text"],
            justify="left",
            anchor="nw",
            wraplength=255,
        ).grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

    def on_show(self):
        super().on_show()
        self._refresh_metrics()
        self._refresh_nav_state()

    def _ensure_cleaner(self):
        if self.app.cleaner is None or self.app.cleaner.df is None:
            messagebox.showwarning("尚未清洗数据", "请先在【数据清洗】执行清洗。")
            return False
        if "TotalPrice" not in self.app.cleaner.df.columns:
            messagebox.showwarning("清洗不完整", "商品分析需要 TotalPrice 列。")
            return False
        return True

    def _get_visualizer(self):
        if self.app.visualizer is None:
            self.app.visualizer = Visualizer()
        return self.app.visualizer

    def _on_top_quantity(self):
        """生成「TOP10 热销商品（按销量）」图并展示，同时更新洞察与进度。"""
        if not self._ensure_cleaner():
            return
        try:
            top = get_top_quantity(self.app.cleaner.df)
            path = self._get_visualizer().plot_top_quantity(top)
        except Exception as e:
            messagebox.showerror("生成失败", f"生成 TOP10 销量图时出错：\n{e}")
            return
        self.chart_title_var.set("TOP10 热销商品（按销量）")
        self._show_image(path)
        self.insight_var.set(INSIGHTS["top_quantity"])
        mark_chart_progress(self.app, "product", "top_quantity")
        self._refresh_nav_state()
        self.app.set_status(f"已生成：{path}")

    def _on_top_revenue(self):
        """生成「TOP10 商品（按销售额）」图并展示，同时更新洞察与进度。"""
        if not self._ensure_cleaner():
            return
        try:
            top = get_top_revenue(self.app.cleaner.df)
            path = self._get_visualizer().plot_top_revenue(top)
        except Exception as e:
            messagebox.showerror("生成失败", f"生成 TOP10 销售额图时出错：\n{e}")
            return
        self.chart_title_var.set("TOP10 商品（按销售额）")
        self._show_image(path)
        self.insight_var.set(INSIGHTS["top_revenue"])
        mark_chart_progress(self.app, "product", "top_revenue")
        self._refresh_nav_state()
        self.app.set_status(f"已生成：{path}")

    def _on_price_distribution(self):
        """生成「成交单价分布」图并展示，同时更新洞察与进度。"""
        if not self._ensure_cleaner():
            return
        try:
            prices = get_price_distribution(self.app.cleaner.df)
            path = self._get_visualizer().plot_price_distribution(prices)
        except Exception as e:
            messagebox.showerror("生成失败", f"生成单价分布图时出错：\n{e}")
            return
        self.chart_title_var.set("成交单价分布")
        self._show_image(path)
        self.insight_var.set(INSIGHTS["price_distribution"])
        mark_chart_progress(self.app, "product", "price_distribution")
        self._refresh_nav_state()
        self.app.set_status(f"已生成：{path}")

    def _refresh_metrics(self):
        if self.app.cleaner is None or self.app.cleaner.df is None or "TotalPrice" not in self.app.cleaner.df.columns:
            for key in self.metric_vars:
                self._set_metric(key, "--", "等待清洗")
            return

        df = self.app.cleaner.df
        products = df["StockCode"].nunique()
        quantity = int(df["Quantity"].sum())
        prices = get_price_distribution(df)
        prices = prices[prices > 0]
        median_price = float(prices.median()) if len(prices) else 0
        top_revenue = get_top_revenue(df, n=1)

        if len(top_revenue):
            top_name = str(top_revenue.index[0])
            top_value = float(top_revenue.iloc[0])
        else:
            top_name = "无"
            top_value = 0

        self._set_metric("products", f"{products:,}", "不同商品编码")
        self._set_metric("quantity", f"{quantity:,}", "累计销售件数")
        self._set_metric("median_price", f"£{median_price:.2f}", "成交单价中位数")
        self._set_metric("top_revenue", self._fmt_money(top_value), self._clip(top_name, 20))

    def _refresh_nav_state(self):
        refresh_workflow_nav(self.nav_items, self.app, "商品分析")

    def _show_image(self, path):
        try:
            img = Image.open(path)
            img.thumbnail(CHART_BOX_SIZE)
            ctk_img = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=img.size,
            )
        except Exception as e:
            messagebox.showerror("加载图片失败", f"无法加载 {path}：\n{e}")
            return
        self.image_label.configure(image=ctk_img, text="")
        self.current_image = ctk_img

    def _set_metric(self, key, value, note):
        value_var, note_var = self.metric_vars[key]
        value_var.set(value)
        note_var.set(note)

    def _fmt_money(self, value):
        if value >= 1_000_000:
            return f"£{value / 1_000_000:.2f}M"
        if value >= 1_000:
            return f"£{value / 1_000:.1f}K"
        return f"£{value:.0f}"

    def _clip(self, text, length):
        return text if len(text) <= length else text[: length - 1] + "…"
