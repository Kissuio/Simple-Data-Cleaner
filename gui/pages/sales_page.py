"""销售分析页 —— 销售图表工作台（customtkinter 版本）。"""

from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from analyzer.sales_trend import (
    get_monthly_sales,
    get_weekday_hour_orders,
    get_month_orders,
)
from analyzer.insights import (
    monthly_trend_insight,
    weekday_hour_insight,
    month_insight,
)
from gui.error_messages import show_friendly_error
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
    "empty": "选择上方图表后，这里会显示对应的业务洞察（按当前数据现算）。",
}


class SalesPage(BasePage):
    """销售分析页。"""

    def __init__(self, master, app):
        super().__init__(
            master,
            app,
            title="销售分析",
            requires="cleaner",
            next_page="商品分析",
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
        return build_workflow_nav(parent, self.app, "销售分析", self.nav_items)

    def _build_metrics(self, parent):
        metrics = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        metrics.grid(row=0, column=0, sticky="ew")
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1, uniform="sales_metric")

        specs = [
            ("销售额", "sales", COLORS["blue"]),
            ("订单数", "orders", COLORS["green"]),
            ("月份数", "months", COLORS["amber"]),
            ("活跃时段", "active_hours", COLORS["purple"]),
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
            text="销售图表",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            panel,
            text="从时间维度查看销售额趋势和订单高峰时段。",
            font=("SimHei", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        buttons = ctk.CTkFrame(panel, fg_color="transparent", corner_radius=0)
        buttons.grid(row=0, column=1, rowspan=2, sticky="e", padx=18)

        ctk.CTkButton(
            buttons,
            text="月度趋势",
            command=self._on_monthly_trend,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=110,
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="周热力图",
            command=self._on_weekday_hour,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=110,
            corner_radius=6,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="年月分布",
            command=self._on_month,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            height=36,
            width=120,
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
            text="业务洞察",
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
        """检查清洗 + 字段映射就绪（方案 B：分析前需先把列映射到标准字段）。"""
        if self.app.cleaner is None or self.app.cleaner.df is None:
            messagebox.showwarning("尚未清洗数据", "请先在【数据清洗】执行清洗。")
            return False
        if not self.app.is_mapped():
            self.app.open_field_mapping()
            return False
        missing = self.app.missing_fields_for("sales")
        if missing:
            from data_handlers.field_mapping import FIELD_CN
            names = "、".join(FIELD_CN.get(c, c) for c in missing)
            messagebox.showwarning(
                "字段不足",
                f"「销售分析」还需要这些字段：{names}\n请点顶部「⚙ 字段映射」补上对应列。",
            )
            return False
        if not self.app.require_types_ready("sales"):
            return False
        return True

    def _get_visualizer(self):
        return self.app.get_visualizer()

    def _on_monthly_trend(self):
        """生成「月度销售趋势」图并展示，同时更新洞察与进度。"""
        if not self._ensure_cleaner():
            return
        try:
            monthly = get_monthly_sales(self.app.get_active_df())
            path = self._get_visualizer().plot_monthly_trend(monthly)
        except Exception as e:
            show_friendly_error("生成失败", e, "生成月度趋势图", parent=self)
            return
        self.chart_title_var.set("月度销售趋势")
        self._show_image(path)
        self.insight_var.set(monthly_trend_insight(monthly))
        mark_chart_progress(self.app, "sales", "monthly_trend")
        self._refresh_nav_state()
        self.app.set_status(f"已生成：{path}")

    def _on_weekday_hour(self):
        """生成「订单数热力图（星期 × 小时）」并展示，同时更新洞察与进度。"""
        if not self._ensure_cleaner():
            return
        try:
            pivot = get_weekday_hour_orders(self.app.get_active_df())
            path = self._get_visualizer().plot_weekday_hour_heatmap(pivot)
        except Exception as e:
            show_friendly_error("生成失败", e, "生成星期与小时热力图", parent=self)
            return
        self.chart_title_var.set("订单数热力图（星期 × 小时）")
        self._show_image(path)
        self.insight_var.set(weekday_hour_insight(pivot))
        mark_chart_progress(self.app, "sales", "weekday_hour_heatmap")
        self._refresh_nav_state()
        self.app.set_status(f"已生成：{path}")

    def _on_month(self):
        """生成「各月份订单数分布（季节性）」并展示——多年合并看 12 个月旺淡季。"""
        if not self._ensure_cleaner():
            return
        try:
            pivot = get_month_orders(self.app.get_active_df())
            path = self._get_visualizer().plot_month_heatmap(pivot)
        except Exception as e:
            show_friendly_error("生成失败", e, "生成年月订单分布图", parent=self)
            return
        self.chart_title_var.set("各年各月订单数分布")
        self._show_image(path)
        self.insight_var.set(month_insight(pivot))
        mark_chart_progress(self.app, "sales", "month_heatmap")
        self._refresh_nav_state()
        self.app.set_status(f"已生成：{path}")

    def _refresh_metrics(self):
        # 方案 B + 软门禁：未映射 / 缺销售所需列时，显示提示而不取数（避免 KeyError）
        if not self.app.is_mapped():
            note = "等待清洗" if self.app.cleaner is None else "等待映射"
            for key in self.metric_vars:
                self._set_metric(key, "--", note)
            return
        if self.app.missing_fields_for("sales"):
            for key in self.metric_vars:
                self._set_metric(key, "--", "缺字段")
            return
        if self.app.type_guidance("sales"):
            for key in self.metric_vars:
                self._set_metric(key, "--", "待转换列类型")
            return

        df = self.app.get_active_df()
        total_sales = float(df["TotalPrice"].sum())
        orders = df["InvoiceNo"].nunique()
        months = df["InvoiceDate"].dt.strftime("%Y-%m").nunique()
        pivot = get_weekday_hour_orders(df)
        active_hours = int((pivot > 0).sum().sum())

        self._set_metric("sales", self._fmt_money(total_sales), "清洗后销售额")
        self._set_metric("orders", f"{orders:,}", "独立订单数")
        self._set_metric("months", f"{months}", "覆盖月份")
        self._set_metric("active_hours", f"{active_hours}", "有订单的星期×小时")

    def _refresh_nav_state(self):
        refresh_workflow_nav(self.nav_items, self.app, "销售分析")

    def _show_image(self, path):
        """加载 PNG 并显示到 image_label。"""
        try:
            img = Image.open(path)
            img.thumbnail(CHART_BOX_SIZE)
            ctk_img = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=img.size,
            )
        except Exception as e:
            show_friendly_error("加载图片失败", e, "打开生成的图表", parent=self)
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
