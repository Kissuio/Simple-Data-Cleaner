"""主页 / 总览仪表盘（customtkinter 版本）。"""

import math
import tkinter as tk

import customtkinter as ctk

from gui.widgets import BORDER_WIDTH, UI_COLORS as COLORS, chart_group_complete


STEPS = [
    ("01", "加载数据", "选择 CSV / Excel 文件", "加载数据"),
    ("02", "数据清洗", "缺失、取消、非商品记录处理", "数据清洗"),
    ("03", "RFM 分群", "计算 R/F/M 并生成 8 类标签", "RFM 分析"),
    ("04", "销售分析", "月度趋势与订单热力图", "销售分析"),
    ("05", "商品分析", "销量、销售额、单价分布", "商品分析"),
    ("06", "图表总览", "9 张图统一浏览 + AI 解读", "图表总览"),
]

ALCHEMY_ROWS = [
    ("缺失过滤", "missing", COLORS["red"], COLORS["red_soft"]),
    ("取消订单", "cancel", COLORS["amber"], COLORS["amber_soft"]),
    ("非商品代码", "non_product", "#7c6aa6", "#f3f0fb"),
    ("保留率", "retention", COLORS["green"], COLORS["green_soft"]),
]

SEGMENT_META = [
    ("重要价值客户", "重要价值", COLORS["amber"], COLORS["amber_soft"]),
    ("重要保持客户", "重要保持", COLORS["green"], COLORS["green_soft"]),
    ("重要发展客户", "重要发展", COLORS["blue"], COLORS["blue_soft"]),
    ("重要挽留客户", "重要挽留", COLORS["red"], COLORS["red_soft"]),
    ("一般价值客户", "一般价值", "#14b8a6", "#f0fdfa"),
    ("一般保持客户", "一般保持", COLORS["purple"], COLORS["purple_soft"]),
    ("一般发展客户", "一般发展", COLORS["blue_hover"], COLORS["blue_soft"]),
    ("一般挽留客户", "一般挽留", COLORS["gray"], COLORS["panel_soft"]),
]


class KpiCard(ctk.CTkFrame):
    """首页 KPI 卡片。"""

    def __init__(self, parent, title, value_var, note_var, accent):
        super().__init__(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        self.accent = accent
        self.soft_color = COLORS["panel_soft"]
        self.grid_columnconfigure(0, weight=1)

        self.top_bar = ctk.CTkFrame(
            self,
            fg_color=accent,
            height=5,
            corner_radius=8,
        )
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.top_bar.grid_propagate(False)

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=("SimHei", 11, "bold"),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.title_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 4))

        self.value_label = ctk.CTkLabel(
            self,
            textvariable=value_var,
            font=("Microsoft YaHei UI", 25, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.value_label.grid(row=2, column=0, sticky="ew", padx=16)

        self.note_label = ctk.CTkLabel(
            self,
            textvariable=note_var,
            font=("SimHei", 10),
            text_color=accent,
            anchor="w",
        )
        self.note_label.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 14))

        for widget in [self, self.top_bar, self.title_label, self.value_label, self.note_label]:
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def set_note_color(self, color):
        self.note_label.configure(text_color=color)

    def set_accent_color(self, color, soft_color):
        self.accent = color
        self.soft_color = soft_color
        self.top_bar.configure(fg_color=color)

    def _on_enter(self, event):
        self.configure(fg_color=self.soft_color, border_color=self.accent)

    def _on_leave(self, event):
        self.configure(fg_color=COLORS["panel_bg"], border_color=COLORS["border"])


class AlchemyRuleIcon(ctk.CTkFrame):
    """炼金炉规则说明里的小图标。"""

    def __init__(self, parent, icon_key, color, bg):
        super().__init__(
            parent,
            fg_color=bg,
            corner_radius=8,
            width=36,
            height=36,
        )
        self.icon_key = icon_key
        self.color = color
        self.bg = bg
        self.grid_propagate(False)

        self.canvas = tk.Canvas(
            self,
            width=36,
            height=36,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self._draw_icon()

    def set_state(self, color, bg):
        self.color = color
        self.bg = bg
        self.configure(fg_color=bg)
        self.canvas.configure(bg=bg)
        self._draw_icon()

    def _draw_icon(self):
        c = self.canvas
        color = self.color
        c.delete("all")

        if self.icon_key == "missing":
            c.create_oval(13, 8, 23, 18, outline=color, width=2)
            c.create_line(18, 18, 18, 29, fill=color, width=2)
            c.create_line(12, 24, 24, 24, fill=color, width=2)
            c.create_line(27, 9, 30, 12, 24, 18, fill=color, width=2)
        elif self.icon_key == "cancel":
            c.create_rectangle(9, 9, 27, 27, outline=color, width=2)
            c.create_line(12, 12, 24, 24, fill=color, width=2)
            c.create_line(24, 12, 12, 24, fill=color, width=2)
        elif self.icon_key == "product":
            c.create_rectangle(10, 14, 26, 28, outline=color, width=2)
            c.create_line(10, 14, 18, 9, 26, 14, fill=color, width=2)
            c.create_line(18, 9, 18, 24, fill=color, width=2)
        elif self.icon_key == "clean":
            c.create_line(8, 9, 28, 9, 22, 18, 22, 26, 16, 30, 16, 18, 8, 9, fill=color, width=2)
            c.create_line(11, 14, 25, 14, fill=color, width=2)
        elif self.icon_key == "analysis":
            c.create_oval(10, 7, 27, 13, outline=color, width=2)
            c.create_rectangle(10, 10, 27, 27, outline=color, width=2)
            c.create_oval(10, 24, 27, 30, outline=color, width=2)
            c.create_line(21, 20, 24, 23, 30, 16, fill=color, width=2)
        else:
            c.create_rectangle(9, 22, 13, 29, fill=color, outline=color)
            c.create_rectangle(16, 16, 20, 29, fill=color, outline=color)
            c.create_rectangle(23, 10, 27, 29, fill=color, outline=color)
            c.create_line(8, 30, 29, 30, fill=color, width=2)


class StepIcon(ctk.CTkFrame):
    """流程导航的纯代码小图标，不依赖图片素材。"""

    def __init__(self, parent, target):
        super().__init__(
            parent,
            fg_color=COLORS["panel_soft"],
            corner_radius=8,
            width=46,
            height=46,
        )
        self.target = target
        self.color = COLORS["blue"]
        self.bg = COLORS["panel_soft"]
        self.grid_propagate(False)

        self.canvas = tk.Canvas(
            self,
            width=46,
            height=46,
            bg=self.bg,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=1, pady=1)
        self.draw()

    def set_state(self, color, bg):
        self.color = color
        self.bg = bg
        self.configure(fg_color=bg)
        self.canvas.configure(bg=bg)
        self.draw()

    def draw(self):
        c = self.canvas
        c.delete("all")
        color = self.color
        target = self.target

        if target == "加载数据":
            c.create_rectangle(14, 10, 30, 34, outline=color, width=2)
            c.create_line(30, 10, 36, 16, 36, 34, 30, 34, fill=color, width=2)
            c.create_line(18, 19, 31, 19, fill=color, width=2)
            c.create_line(18, 25, 31, 25, fill=color, width=2)
        elif target == "数据清洗":
            c.create_line(10, 12, 36, 12, 27, 23, 27, 31, 20, 35, 20, 23, 10, 12, fill=color, width=2)
            c.create_line(14, 18, 32, 18, fill=color, width=2)
        elif target == "RFM 分析":
            points = [(23, 11), (12, 31), (34, 31)]
            c.create_line(points[0], points[1], points[2], points[0], fill=color, width=2)
            for x, y in points:
                c.create_oval(x - 5, y - 5, x + 5, y + 5, outline=color, width=2)
        elif target == "销售分析":
            c.create_line(11, 34, 36, 34, fill=color, width=2)
            c.create_line(11, 34, 11, 11, fill=color, width=2)
            c.create_line(14, 29, 20, 23, 26, 26, 34, 15, fill=color, width=3)
        elif target == "商品分析":
            c.create_rectangle(13, 16, 33, 34, outline=color, width=2)
            c.create_line(13, 16, 23, 10, 33, 16, fill=color, width=2)
            c.create_line(23, 10, 23, 28, fill=color, width=2)
        else:
            c.create_rectangle(12, 25, 17, 34, fill=color, outline=color)
            c.create_rectangle(21, 17, 26, 34, fill=color, outline=color)
            c.create_rectangle(30, 11, 35, 34, fill=color, outline=color)
            c.create_line(10, 36, 37, 36, fill=color, width=2)


class StepCard(ctk.CTkFrame):
    """可点击流程步骤卡片。"""

    def __init__(self, parent, number, title, subtitle, target, app):
        super().__init__(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
            cursor="hand2",
        )
        self.app = app
        self.target = target
        self.default_bg = COLORS["panel_bg"]
        self.default_border = COLORS["border"]
        self.hover_bg = COLORS["blue_soft"]
        self.is_active = False

        self.grid_columnconfigure(1, weight=1)

        self.icon = StepIcon(self, target)
        self.icon.grid(row=0, column=0, rowspan=2, padx=(14, 10), pady=12)

        self.title_label = ctk.CTkLabel(
            self,
            text=f"{number}  {title}",
            font=("SimHei", 14, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.title_label.grid(row=0, column=1, sticky="ew", pady=(13, 0))

        self.subtitle_label = ctk.CTkLabel(
            self,
            text=subtitle,
            font=("SimHei", 10),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.subtitle_label.grid(row=1, column=1, sticky="ew", pady=(0, 13))

        self.state_label = ctk.CTkLabel(
            self,
            text="未开始",
            width=72,
            height=24,
            fg_color=COLORS["panel_soft"],
            text_color=COLORS["muted"],
            font=("SimHei", 10, "bold"),
            corner_radius=6,
        )
        self.state_label.grid(row=0, column=2, rowspan=2, padx=14)

        for widget in [
            self,
            self.icon,
            self.icon.canvas,
            self.title_label,
            self.subtitle_label,
            self.state_label,
        ]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.configure(cursor="hand2")

    def set_state(self, text, color, soft_color, active=False):
        """刷新步骤状态标签。"""
        self.is_active = active
        self.state_label.configure(text=text, text_color=color, fg_color=soft_color)
        if active:
            self.default_bg = COLORS["blue_soft"]
            self.default_border = COLORS["blue"]
            self.configure(fg_color=self.default_bg, border_color=self.default_border)
            self.icon.set_state(COLORS["blue"], COLORS["blue_soft"])
            self.title_label.configure(text_color=COLORS["blue"])
        else:
            self.default_bg = COLORS["panel_bg"]
            self.default_border = COLORS["green"] if color == COLORS["green"] else COLORS["border"]
            self.configure(fg_color=self.default_bg, border_color=self.default_border)
            self.icon.set_state(color, soft_color)
            self.title_label.configure(text_color=COLORS["text"])

    def _on_click(self, event):
        self.app.show_page(self.target)

    def _on_enter(self, event):
        self.configure(fg_color=self.hover_bg, border_color=COLORS["blue"])
        self.title_label.configure(text_color=COLORS["blue"])

    def _on_leave(self, event):
        self.configure(fg_color=self.default_bg, border_color=self.default_border)
        self.title_label.configure(text_color=COLORS["blue"] if self.is_active else COLORS["text"])


class HomePage(ctk.CTkFrame):
    """主页总览。"""

    def __init__(self, master, app):
        super().__init__(master, fg_color=COLORS["page_bg"], corner_radius=0)
        self.app = app
        self.kpi_vars = {}
        self.kpi_cards = {}
        self.step_cards = {}
        self.alchemy_value_vars = {}
        self.alchemy_note_vars = {}
        self.alchemy_bars = {}
        self.alchemy_gauge_canvas = None
        self.alchemy_gauge_value = 0
        self.alchemy_gauge_text = "--"
        self.alchemy_gauge_note_var = ctk.StringVar(value="等待可分析数据")
        self.star_insight_vars = {}
        self.summary_var = ctk.StringVar(value="")
        self.next_action_var = ctk.StringVar(value="")
        self.alchemy_summary_var = ctk.StringVar(value="")
        self.star_summary_var = ctk.StringVar(value="")
        self.star_canvas = None
        self.next_page = "加载数据"
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=0,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_block = ctk.CTkFrame(header, fg_color="transparent", corner_radius=0)
        title_block.grid(row=0, column=0, sticky="w", padx=30, pady=20)

        ctk.CTkLabel(
            title_block,
            text="Online Retail RFM Analysis",
            font=("Microsoft YaHei UI", 28, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text="从交易数据到客户价值分群的可视化分析系统",
            font=("SimHei", 12),
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))

        status_box = ctk.CTkFrame(
            header,
            fg_color=COLORS["blue_soft"],
            border_color="#93c5fd",
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        status_box.grid(row=0, column=1, sticky="e", padx=30, pady=20)

        ctk.CTkLabel(
            status_box,
            textvariable=self.summary_var,
            font=("SimHei", 11, "bold"),
            text_color=COLORS["blue"],
        ).pack(padx=18, pady=10)

    def _build_content(self):
        content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        content.grid(row=1, column=0, sticky="nsew", padx=24, pady=24)
        content.grid_columnconfigure(0, weight=0)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self._build_steps_panel(content)
        self._build_dashboard_panel(content)

    def _build_steps_panel(self, parent):
        panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
            width=390,
        )
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 18))
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text="分析流程",
            font=("SimHei", 17, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 2))

        ctk.CTkLabel(
            panel,
            text="按顺序完成，也可以直接进入任一模块查看状态。",
            font=("SimHei", 10),
            text_color=COLORS["muted"],
            anchor="w",
            wraplength=310,
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        for row, (number, title, subtitle, target) in enumerate(STEPS, start=2):
            card = StepCard(panel, number, title, subtitle, target, self.app)
            card.grid(row=row, column=0, sticky="ew", padx=16, pady=5)
            self.step_cards[target] = card

    def _build_dashboard_panel(self, parent):
        dashboard = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        dashboard.grid(row=0, column=1, sticky="nsew")
        dashboard.grid_columnconfigure(0, weight=1)
        dashboard.grid_rowconfigure(2, weight=1)

        self._build_kpis(dashboard)
        self._build_next_action(dashboard)
        self._build_focus_panels(dashboard)

    def _build_kpis(self, parent):
        kpi_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        kpi_frame.grid(row=0, column=0, sticky="ew")
        for col in range(4):
            kpi_frame.grid_columnconfigure(col, weight=1, uniform="kpi")

        specs = [
            ("原始记录", "raw", COLORS["blue"]),
            ("清洗后记录", "clean", COLORS["green"]),
            ("客户数量", "customer", COLORS["purple"]),
            ("总销售额", "sales", COLORS["amber"]),
        ]
        for col, (title, key, accent) in enumerate(specs):
            value_var = ctk.StringVar(value="--")
            note_var = ctk.StringVar(value="等待数据")
            self.kpi_vars[key] = (value_var, note_var)
            card = KpiCard(kpi_frame, title, value_var, note_var, accent)
            card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))
            self.kpi_cards[key] = card

    def _build_next_action(self, parent):
        action = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        action.grid(row=1, column=0, sticky="ew", pady=16)
        action.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            action,
            text="下一步建议",
            font=("SimHei", 12, "bold"),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 2))

        ctk.CTkLabel(
            action,
            textvariable=self.next_action_var,
            font=("SimHei", 17, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))

        ctk.CTkButton(
            action,
            text="继续当前流程",
            command=self._go_next_step,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"),
            width=130,
            height=36,
            corner_radius=6,
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=18)

    def _build_focus_panels(self, parent):
        focus = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        focus.grid(row=2, column=0, sticky="nsew")
        focus.grid_columnconfigure(0, weight=1)
        focus.grid_columnconfigure(1, weight=1)
        focus.grid_rowconfigure(0, weight=1)

        self._build_alchemy_panel(focus, column=0)
        self._build_star_panel(focus, column=1)

    def _build_alchemy_panel(self, parent, column):
        panel = self._make_focus_panel(parent, column)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        self._build_panel_title(
            panel,
            "数据炼金炉",
            "Raw -> Clean -> Insight",
            COLORS["amber"],
            COLORS["amber_soft"],
        )

        status_pill = ctk.CTkFrame(
            panel,
            fg_color=COLORS["panel_soft"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=8,
        )
        status_pill.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            status_pill,
            textvariable=self.alchemy_summary_var,
            font=("SimHei", 12),
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(padx=12, pady=7)

        content = ctk.CTkFrame(panel, fg_color="transparent", corner_radius=0)
        content.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        rules = ctk.CTkFrame(content, fg_color=COLORS["panel_soft"], corner_radius=8)
        rules.grid(row=0, column=0, sticky="ew")
        for col in range(3):
            rules.grid_columnconfigure(col, weight=1, uniform="alchemy_rule")

        rule_specs = [
            (
                "识别缺失客户",
                "CustomerID 为空不进入 RFM",
                "missing",
                COLORS["blue"],
                COLORS["blue_soft"],
            ),
            (
                "剔除取消订单",
                "C 开头订单及退货记录排除",
                "cancel",
                COLORS["amber"],
                COLORS["amber_soft"],
            ),
            (
                "保留真实商品",
                "过滤邮费、手续费等非商品代码",
                "product",
                COLORS["green"],
                COLORS["green_soft"],
            ),
        ]
        for col, (title, subtitle, icon_key, color, soft) in enumerate(rule_specs):
            rule_card = self._make_clean_rule_card(rules, title, subtitle, icon_key, color, soft)
            rule_card.grid(row=0, column=col, sticky="ew", padx=7, pady=12)

        instrument = ctk.CTkFrame(
            content,
            fg_color="#ffffff",
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        instrument.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        instrument.grid_columnconfigure(0, weight=0, minsize=218)
        instrument.grid_columnconfigure(1, weight=1)
        instrument.grid_rowconfigure(0, weight=1)
        instrument.grid_rowconfigure(1, weight=0)
        instrument.grid_rowconfigure(2, weight=1)

        gauge_wrap = ctk.CTkFrame(instrument, fg_color="#ffffff", corner_radius=8)
        gauge_wrap.grid(row=1, column=0, sticky="ew", padx=(18, 8), pady=18)
        gauge_wrap.grid_columnconfigure(0, weight=1)

        self.alchemy_gauge_canvas = tk.Canvas(
            gauge_wrap,
            width=180,
            height=180,
            bg="#ffffff",
            highlightthickness=0,
            bd=0,
        )
        self.alchemy_gauge_canvas.grid(row=0, column=0, sticky="n", pady=(0, 6))
        self.alchemy_gauge_canvas.bind("<Configure>", lambda event: self._draw_alchemy_gauge())

        ctk.CTkLabel(
            gauge_wrap,
            textvariable=self.alchemy_gauge_note_var,
            font=("SimHei", 11),
            text_color=COLORS["muted"],
            anchor="center",
            justify="center",
            wraplength=180,
        ).grid(row=1, column=0, sticky="ew")

        rows = ctk.CTkFrame(instrument, fg_color="transparent", corner_radius=0)
        rows.grid(row=1, column=1, sticky="ew", padx=(8, 18), pady=18)
        rows.grid_columnconfigure(1, weight=1)

        for row_idx, (title, key, color, soft) in enumerate(ALCHEMY_ROWS[:3]):
            label = ctk.CTkLabel(
                rows,
                text=title,
                font=("SimHei", 13, "bold"),
                text_color=COLORS["text"],
                anchor="w",
                width=92,
            )
            label.grid(row=row_idx, column=0, sticky="w", pady=10)

            bar = ctk.CTkProgressBar(
                rows,
                height=12,
                progress_color=color,
                fg_color=COLORS["panel_soft"],
                corner_radius=8,
            )
            bar.set(0)
            bar.grid(row=row_idx, column=1, sticky="ew", padx=14, pady=10)

            value_var = ctk.StringVar(value="--")
            note_var = ctk.StringVar(value="等待数据")
            self.alchemy_value_vars[key] = value_var
            self.alchemy_note_vars[key] = note_var
            self.alchemy_bars[key] = bar

            ctk.CTkLabel(
                rows,
                textvariable=value_var,
                fg_color=soft,
                text_color=color,
                font=("Microsoft YaHei UI", 13, "bold"),
                corner_radius=6,
                width=104,
                height=32,
            ).grid(row=row_idx, column=2, sticky="e", pady=8)

        ctk.CTkLabel(
            content,
            text="中心看最终保留率，旁边看过滤原因。",
            font=("SimHei", 12),
            text_color=COLORS["muted"],
            anchor="w",
            wraplength=480,
        ).grid(row=2, column=0, sticky="ew", pady=(12, 0))

    def _build_star_panel(self, parent, column):
        panel = self._make_focus_panel(parent, column)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        self._build_panel_title(
            panel,
            "客户星图",
            "RFM Cluster Map",
            COLORS["purple"],
            COLORS["purple_soft"],
        )

        ctk.CTkLabel(
            panel,
            textvariable=self.star_summary_var,
            font=("SimHei", 13),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        canvas_wrap = ctk.CTkFrame(
            panel,
            fg_color="#ffffff",
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        canvas_wrap.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 12))
        canvas_wrap.grid_columnconfigure(0, weight=1)
        canvas_wrap.grid_rowconfigure(0, weight=1)

        self.star_canvas = tk.Canvas(
            canvas_wrap,
            bg="#ffffff",
            highlightthickness=0,
            bd=0,
            height=270,
        )
        self.star_canvas.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.star_canvas.bind("<Configure>", lambda event: self._draw_star_map())

        insights = ctk.CTkFrame(
            panel,
            fg_color="transparent",
            corner_radius=0,
        )
        insights.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        insights.grid_rowconfigure(0, weight=1)
        for col_idx in range(3):
            insights.grid_columnconfigure(col_idx, weight=1, uniform="star_insight")

        specs = [
            ("最大群体", "largest", COLORS["blue"], COLORS["blue_soft"]),
            ("流失风险", "risk", COLORS["red"], COLORS["red_soft"]),
            ("成长潜力", "growth", COLORS["green"], COLORS["green_soft"]),
        ]
        for col, (title, key, accent, soft) in enumerate(specs):
            value_var = ctk.StringVar(value="--")
            note_var = ctk.StringVar(value="等待 RFM")
            self.star_insight_vars[key] = (value_var, note_var)
            card = self._make_star_insight_card(insights, title, value_var, note_var, accent, soft)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))

    def _make_focus_panel(self, parent, column):
        panel = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        panel.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0))
        return panel

    def _build_panel_title(self, parent, title, subtitle, accent, soft):
        heading = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        heading.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        heading.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            heading,
            text=title,
            font=("SimHei", 20, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            heading,
            text=subtitle,
            fg_color=soft,
            text_color=accent,
            font=("Microsoft YaHei UI", 12, "bold"),
            corner_radius=6,
            width=156,
            height=32,
        ).grid(row=0, column=1, sticky="e")

    def _make_clean_rule_card(self, parent, title, subtitle, icon_key, accent, soft):
        card = ctk.CTkFrame(
            parent,
            fg_color="#ffffff",
            border_color=accent,
            border_width=1,
            corner_radius=8,
        )
        card.grid_columnconfigure(1, weight=1)

        icon = AlchemyRuleIcon(card, icon_key, accent, soft)
        icon.grid(row=0, column=0, rowspan=2, padx=(12, 9), pady=12)

        ctk.CTkLabel(
            card,
            text=title,
            fg_color=soft,
            text_color=accent,
            font=("SimHei", 12, "bold"),
            corner_radius=6,
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(12, 4))

        ctk.CTkLabel(
            card,
            text=subtitle,
            font=("SimHei", 10),
            text_color=COLORS["muted"],
            anchor="w",
            wraplength=150,
        ).grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 12))
        return card

    def _make_star_insight_card(self, parent, title, value_var, note_var, accent, soft):
        card = ctk.CTkFrame(
            parent,
            fg_color="#ffffff",
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(0, weight=0)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkFrame(
            card,
            fg_color=accent,
            width=5,
            corner_radius=8,
        ).grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(0, 8), pady=8)

        ctk.CTkLabel(
            card,
            text=title,
            font=("SimHei", 10, "bold"),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(9, 1))

        content = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        content.grid(row=1, column=1, sticky="nsew", padx=(0, 14), pady=(0, 14))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            content,
            textvariable=value_var,
            fg_color=soft,
            text_color=accent,
            font=("Microsoft YaHei UI", 18, "bold"),
            corner_radius=6,
            anchor="center",
            height=42,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(
            content,
            textvariable=note_var,
            font=("SimHei", 13),
            text_color=COLORS["muted"],
            anchor="center",
            justify="center",
            wraplength=220,
        ).grid(row=1, column=0, sticky="nsew")
        return card

    def on_show(self):
        """每次回到主页时刷新 KPI、步骤状态和可视化面板。"""
        self._refresh_overview()

    def _refresh_overview(self):
        loader_ok = self.app.loader is not None and self.app.loader.df is not None
        # 方案 B：清洗完成只看「有清洗后数据」；销售额/客户等需标准列的指标，
        # 要等进入分析做完字段映射（mapped_ok）后才能算。
        cleaner_ok = self.app.cleaner is not None and self.app.cleaner.df is not None
        mapped_ok = self.app.is_mapped()
        rfm_ok = self.app.rfm_df is not None and "Label" in self.app.rfm_df.columns
        sales_done = cleaner_ok and chart_group_complete(self.app, "sales")
        product_done = cleaner_ok and chart_group_complete(self.app, "product")
        overview_done = cleaner_ok and rfm_ok and chart_group_complete(self.app, "overview")

        # 映射后的清洗数据（标准列名），供销售额/客户/炼金炉取数；未映射为 None
        mapped_df = self.app.mapped_clean_df()

        raw_rows = len(self.app.loader.df) if loader_ok else None
        clean_rows = len(self.app.cleaner.df) if cleaner_ok else None
        customer_count = self._customer_count(rfm_ok, mapped_df)
        total_sales = self._total_sales(mapped_df)
        raw_accent, raw_soft = self._kpi_state_color(done=loader_ok, active=not loader_ok)
        clean_accent, clean_soft = self._kpi_state_color(done=cleaner_ok, active=loader_ok and not cleaner_ok)
        customer_accent, customer_soft = self._kpi_state_color(done=rfm_ok, active=cleaner_ok and not rfm_ok)
        sales_accent, sales_soft = self._kpi_state_color(done=mapped_ok, money=True)

        self._set_kpi(
            "raw",
            self._fmt_number(raw_rows),
            "已加载" if loader_ok else "等待导入",
            COLORS["green"] if loader_ok else COLORS["muted"],
            raw_accent,
            raw_soft,
        )
        self._set_kpi(
            "clean",
            self._fmt_number(clean_rows),
            "清洗完成" if cleaner_ok else "等待清洗",
            COLORS["green"] if cleaner_ok else COLORS["muted"],
            clean_accent,
            clean_soft,
        )
        if rfm_ok:
            customer_note = "RFM 客户"
        elif mapped_ok:
            customer_note = "清洗后客户"
        else:
            customer_note = "等待映射"
        self._set_kpi(
            "customer",
            self._fmt_number(customer_count),
            customer_note,
            COLORS["green"] if (rfm_ok or mapped_ok) else COLORS["muted"],
            customer_accent,
            customer_soft,
        )
        self._set_kpi(
            "sales",
            self._fmt_money(total_sales),
            "清洗后销售额" if mapped_ok else "等待映射",
            COLORS["amber"] if mapped_ok else COLORS["muted"],
            sales_accent,
            sales_soft,
        )

        self._refresh_step_states(
            loader_ok,
            cleaner_ok,
            rfm_ok,
            sales_done,
            product_done,
            overview_done,
        )
        self._refresh_alchemy_panel(loader_ok, cleaner_ok, mapped_df)
        self._refresh_star_panel(rfm_ok)

        if overview_done:
            self.summary_var.set("状态：完整流程已完成")
            self.next_action_var.set("可以进入「图表总览」查看 9 张图并尝试 AI 解读。")
            self.next_page = "图表总览"
        elif rfm_ok and sales_done and product_done:
            self.summary_var.set("状态：图表分析待汇总")
            self.next_action_var.set("下一步进入「图表总览」，生成统一报告图表。")
            self.next_page = "图表总览"
        elif rfm_ok and sales_done:
            self.summary_var.set("状态：销售图表已生成")
            self.next_action_var.set("下一步进入「商品分析」，生成销量、销售额和单价分布图。")
            self.next_page = "商品分析"
        elif rfm_ok:
            self.summary_var.set("状态：RFM 分析已完成")
            self.next_action_var.set("下一步进入「销售分析」，生成月度趋势和周热力图。")
            self.next_page = "销售分析"
        elif cleaner_ok:
            self.summary_var.set("状态：数据已清洗")
            self.next_action_var.set("下一步进入「RFM 分析」，生成客户价值分群。")
            self.next_page = "RFM 分析"
        elif loader_ok:
            self.summary_var.set("状态：数据已加载")
            self.next_action_var.set("下一步进入「数据清洗」，处理缺失、取消和非商品记录。")
            self.next_page = "数据清洗"
        else:
            self.summary_var.set("状态：等待加载数据")
            self.next_action_var.set("先进入「加载数据」，选择任意商家交易表的 CSV 或 Excel 文件。")
            self.next_page = "加载数据"

    def _refresh_step_states(
        self,
        loader_ok,
        cleaner_ok,
        rfm_ok,
        sales_done,
        product_done,
        overview_done,
    ):
        done_targets = set()
        active_target = "加载数据"

        if loader_ok:
            done_targets.add("加载数据")
            active_target = "数据清洗"
        if cleaner_ok:
            done_targets.add("数据清洗")
            active_target = "RFM 分析"
        if rfm_ok:
            done_targets.add("RFM 分析")
            active_target = "销售分析"
        if sales_done:
            done_targets.add("销售分析")
        if product_done:
            done_targets.add("商品分析")
        if overview_done:
            done_targets.add("图表总览")

        if rfm_ok:
            if not sales_done:
                active_target = "销售分析"
            elif not product_done:
                active_target = "商品分析"
            elif not overview_done:
                active_target = "图表总览"
            else:
                active_target = None

        for _, _, _, target in STEPS:
            card = self.step_cards[target]
            if target in done_targets:
                card.set_state("已完成", COLORS["green"], COLORS["green_soft"])
            elif target == active_target:
                card.set_state("当前步骤", COLORS["blue"], COLORS["blue_soft"], active=True)
            else:
                card.set_state("未开始", COLORS["muted"], COLORS["panel_soft"])

    def _refresh_alchemy_panel(self, loader_ok, cleaner_ok, mapped_df):
        """数据炼金炉面板：保留率看行数（无需映射），缺失/取消/非商品看标准列（需映射）。"""
        raw_df = self.app.loader.df if loader_ok else None
        cleaner_df = self.app.cleaner.df if cleaner_ok else None
        raw_rows = len(raw_df) if raw_df is not None else 0
        clean_rows = len(cleaner_df) if cleaner_df is not None else 0

        if raw_rows == 0:
            self.alchemy_summary_var.set("等待导入数据")
            self.alchemy_gauge_value = 0
            self.alchemy_gauge_text = "--"
            self.alchemy_gauge_note_var.set("等待可分析数据")
            stats = {"missing": ("--", 0), "cancel": ("--", 0), "non_product": ("--", 0)}
        elif not cleaner_ok:
            self.alchemy_summary_var.set(f"等待清洗  原始 {raw_rows:,} 行")
            self.alchemy_gauge_value = 0
            self.alchemy_gauge_text = "--"
            self.alchemy_gauge_note_var.set("清洗后显示当前可分析数据")
            stats = {"missing": ("待清洗", 0), "cancel": ("待清洗", 0), "non_product": ("待清洗", 0)}
        else:
            # 保留率：清洗后行数 / 原始行数（不依赖列名）
            retention = clean_rows / raw_rows if raw_rows else 0
            self.alchemy_summary_var.set(f"清洗完成  原始 {raw_rows:,} 行 -> 当前 {clean_rows or raw_rows:,} 行")
            self.alchemy_gauge_value = retention
            self.alchemy_gauge_text = f"{retention * 100:.1f}%"
            self.alchemy_gauge_note_var.set(f"当前可分析数据 {clean_rows:,} 行")

            # 缺失客户 / 取消订单 / 非商品代码：需要标准列名，故用「映射后的原始数据」统计。
            # 未映射时这三项显示「待映射」（进入分析做完字段映射后即点亮）。
            if mapped_df is not None and raw_df is not None:
                from data_handlers.field_mapping import apply_field_mapping
                raw_mapped = apply_field_mapping(raw_df, self.app.field_mapping)
                missing = self._missing_customer_count(raw_mapped)
                cancel = self._cancel_order_count(raw_mapped)
                non_product = self._non_product_count(raw_mapped)
                stats = {
                    "missing": (self._fmt_number(missing), self._ratio(missing, raw_rows)),
                    "cancel": (self._fmt_number(cancel), self._ratio(cancel, raw_rows)),
                    "non_product": (self._fmt_number(non_product), self._ratio(non_product, raw_rows)),
                }
            else:
                stats = {"missing": ("待映射", 0), "cancel": ("待映射", 0), "non_product": ("待映射", 0)}

        for key, (text, value) in stats.items():
            self.alchemy_value_vars[key].set(text)
            self.alchemy_bars[key].set(max(0, min(1, value)))
        self._draw_alchemy_gauge()

    def _draw_alchemy_gauge(self):
        if self.alchemy_gauge_canvas is None:
            return

        canvas = self.alchemy_gauge_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 180)
        height = max(canvas.winfo_height(), 180)
        size = min(width, height, 180)
        stroke = 16
        radius = size / 2 - stroke
        cx = width / 2
        cy = height / 2
        x0 = cx - radius
        y0 = cy - radius
        x1 = cx + radius
        y1 = cy + radius
        value = max(0, min(1, self.alchemy_gauge_value))

        canvas.create_oval(
            x0,
            y0,
            x1,
            y1,
            outline=COLORS["panel_soft"],
            width=stroke,
        )
        if value > 0:
            canvas.create_arc(
                x0,
                y0,
                x1,
                y1,
                start=90,
                extent=-360 * value,
                style="arc",
                outline=COLORS["green"],
                width=stroke,
            )

        text_color = COLORS["green"] if value > 0 else COLORS["muted"]
        canvas.create_text(
            cx,
            cy - 10,
            text=self.alchemy_gauge_text,
            fill=text_color,
            font=("Microsoft YaHei UI", 25, "bold"),
        )
        canvas.create_text(
            cx,
            cy + 20,
            text="保留率",
            fill=COLORS["muted"],
            font=("SimHei", 11, "bold"),
        )

    def _refresh_star_panel(self, rfm_ok):
        if not rfm_ok:
            self.star_summary_var.set("完成 RFM 后，8 类客户会在这里被点亮。")
            self._set_star_insight("largest", "--", "等待 RFM")
            self._set_star_insight("risk", "--", "等待 RFM")
            self._set_star_insight("growth", "--", "等待 RFM")
            self._draw_star_map()
            return

        rfm = self.app.rfm_df
        counts = rfm["Label"].value_counts()
        total = int(counts.sum())
        core_labels = {"重要价值客户", "重要保持客户", "重要发展客户", "重要挽留客户"}
        core_count = int(sum(counts.get(label, 0) for label in core_labels))
        core_ratio = core_count / total * 100 if total else 0
        lit_count = sum(1 for label, _, _, _ in SEGMENT_META if counts.get(label, 0) > 0)
        self.star_summary_var.set(f"已点亮 {lit_count}/8 类客户，重要客户占比 {core_ratio:.1f}%")

        self._refresh_star_insights(counts, total)

        self._draw_star_map()

    def _refresh_star_insights(self, counts, total):
        if not total:
            self._set_star_insight("largest", "--", "暂无客户")
            self._set_star_insight("risk", "--", "暂无客户")
            self._set_star_insight("growth", "--", "暂无客户")
            return

        largest_label = str(counts.idxmax())
        largest_pct = counts.get(largest_label, 0) / total * 100
        self._set_star_insight(
            "largest",
            f"{self._short_segment_label(largest_label)} {largest_pct:.0f}%",
            self._segment_action_note(largest_label),
        )

        risk_labels = ("重要挽留客户", "一般挽留客户")
        risk_pct = sum(int(counts.get(label, 0)) for label in risk_labels) / total * 100
        self._set_star_insight(
            "risk",
            f"{risk_pct:.0f}%",
            "挽留客户合计占比",
        )

        growth_labels = ("重要发展客户", "一般发展客户")
        growth_pct = sum(int(counts.get(label, 0)) for label in growth_labels) / total * 100
        self._set_star_insight(
            "growth",
            f"{growth_pct:.0f}%",
            "发展客户合计占比",
        )

    def _set_star_insight(self, key, value, note):
        value_var, note_var = self.star_insight_vars[key]
        value_var.set(value)
        note_var.set(note)

    def _short_segment_label(self, label):
        for full_label, short, _, _ in SEGMENT_META:
            if full_label == label:
                return short
        return label

    def _segment_action_note(self, label):
        notes = {
            "重要价值客户": "核心客群重点维护",
            "重要保持客户": "高价值客户需召回",
            "重要发展客户": "适合提频与加购",
            "重要挽留客户": "优先召回与关怀",
            "一般价值客户": "适合提升客单价",
            "一般保持客户": "低成本持续触达",
            "一般发展客户": "适合转化为高频客户",
            "一般挽留客户": "优先做召回与关怀",
        }
        return notes.get(label, "查看客户策略")

    def _draw_star_map(self):
        if self.star_canvas is None:
            return

        canvas = self.star_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 360)
        height = max(canvas.winfo_height(), 260)
        cx, cy = width / 2, height / 2
        center_radius = 48
        node_rx = 56
        node_ry = 28
        orbit_rx = min(max(136, width * 0.33), width / 2 - node_rx - 32)
        orbit_ry = min(max(82, height * 0.30), height / 2 - node_ry - 18)

        rfm_ok = self.app.rfm_df is not None and "Label" in self.app.rfm_df.columns
        counts = self.app.rfm_df["Label"].value_counts() if rfm_ok else {}
        total = int(counts.sum()) if rfm_ok else 0

        canvas.create_oval(
            cx - orbit_rx,
            cy - orbit_ry,
            cx + orbit_rx,
            cy + orbit_ry,
            outline=COLORS["border"],
            width=2,
        )

        nodes = []
        for idx, (label, short, color, soft) in enumerate(SEGMENT_META):
            angle = math.radians(-90 + idx * 45)
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            x = cx + cos_a * orbit_rx
            y = cy + sin_a * orbit_ry
            count = int(counts.get(label, 0)) if rfm_ok else 0
            pct = count / total if total else 0
            extra = min(14, math.sqrt(pct) * 22) if rfm_ok and count else 0
            rx = node_rx + extra
            ry = node_ry + extra * 0.25
            fill = soft if rfm_ok and count else COLORS["panel_soft"]
            outline = color if rfm_ok and count else COLORS["border"]
            text_color = color if rfm_ok and count else COLORS["muted"]
            line_color = color if rfm_ok and count else COLORS["border"]
            nodes.append((x, y, rx, ry, short, pct, fill, outline, text_color, line_color, cos_a, sin_a))

        for x, y, rx, ry, _, _, _, _, _, line_color, cos_a, sin_a in nodes:
            start_x = cx + cos_a * center_radius
            start_y = cy + sin_a * center_radius
            end_x = x - cos_a * rx
            end_y = y - sin_a * ry
            canvas.create_line(start_x, start_y, end_x, end_y, fill=line_color, width=2)

        for x, y, rx, ry, short, pct, fill, outline, text_color, _, _, _ in nodes:
            canvas.create_oval(
                x - rx,
                y - ry,
                x + rx,
                y + ry,
                fill=fill,
                outline=outline,
                width=3,
            )
            canvas.create_text(
                x,
                y - 7,
                text=short,
                fill=text_color,
                font=("SimHei", 12, "bold"),
            )
            tiny = f"{pct * 100:.0f}%" if rfm_ok and total else "--"
            canvas.create_text(
                x,
                y + 13,
                text=tiny,
                fill=COLORS["muted"],
                font=("Microsoft YaHei UI", 10, "bold"),
            )

        canvas.create_oval(
            cx - center_radius,
            cy - center_radius,
            cx + center_radius,
            cy + center_radius,
            fill=COLORS["blue_soft"],
            outline=COLORS["blue"],
            width=3,
        )
        canvas.create_text(
            cx,
            cy - 6,
            text="RFM",
            fill=COLORS["blue"],
            font=("Microsoft YaHei UI", 18, "bold"),
        )
        canvas.create_text(
            cx,
            cy + 15,
            text="客户中心" if rfm_ok else "待点亮",
            fill=COLORS["muted"],
            font=("SimHei", 11),
        )

    def _missing_customer_count(self, df):
        if "CustomerID" not in df.columns:
            return 0
        return int(df["CustomerID"].isna().sum())

    def _cancel_order_count(self, df):
        if "InvoiceNo" not in df.columns:
            return 0
        return int(df["InvoiceNo"].astype(str).str.startswith("C", na=False).sum())

    def _non_product_count(self, df):
        if "StockCode" not in df.columns:
            return 0
        stock = df["StockCode"].astype(str).str.strip()
        product_mask = stock.str.match(r"^\d{5}[A-Za-z]?$", na=False)
        return int((~product_mask).sum())

    def _customer_count(self, rfm_ok, mapped_df):
        if rfm_ok:
            return len(self.app.rfm_df)
        if mapped_df is not None and "CustomerID" in mapped_df.columns:
            return mapped_df["CustomerID"].nunique()
        return None

    def _total_sales(self, mapped_df):
        if mapped_df is not None and "TotalPrice" in mapped_df.columns:
            return float(mapped_df["TotalPrice"].sum())
        return None

    def _kpi_state_color(self, done=False, active=False, money=False):
        if money and done:
            return COLORS["amber"], COLORS["amber_soft"]
        if done:
            return COLORS["green"], COLORS["green_soft"]
        if active:
            return COLORS["blue"], COLORS["blue_soft"]
        return COLORS["gray_hover"], COLORS["panel_soft"]

    def _set_kpi(self, key, value, note, note_color=None, accent_color=None, accent_soft=None):
        value_var, note_var = self.kpi_vars[key]
        value_var.set(value)
        note_var.set(note)
        if note_color is not None:
            self.kpi_cards[key].set_note_color(note_color)
        if accent_color is not None:
            self.kpi_cards[key].set_accent_color(accent_color, accent_soft or COLORS["panel_soft"])

    def _fmt_number(self, value):
        if value is None:
            return "--"
        return f"{int(value):,}"

    def _fmt_money(self, value):
        if value is None:
            return "--"
        if value >= 1_000_000:
            return f"£{value / 1_000_000:.2f}M"
        if value >= 1_000:
            return f"£{value / 1_000:.1f}K"
        return f"£{value:.0f}"

    def _ratio(self, value, total):
        if not total:
            return 0
        return max(0, min(1, value / total))

    def _go_next_step(self):
        """跳转到当前页配置的下一步页面。"""
        self.app.show_page(self.next_page)
