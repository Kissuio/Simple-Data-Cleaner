"""顶部全局筛选栏（单实例，挂在页面容器上方）。

设计：
- 全局只有一个实例（在 window.py 创建），状态直接读写 app.data_filter，
  避免「每页一个筛选条」的多份同步问题；
- 只在 4 个分析页（RFM / 销售 / 商品 / 总览）显示，由 App.show_page 控制显隐；
- 改筛选 → 调 app.set_data_filter()，由它清空下游 RFM/图结果并刷新当前页；
- 日期用「年-月下拉」（候选来自数据范围、粒度到月，贴合月度分析）；
  国家下拉、年候选都来自「清洗后数据」，没有 Country 列时该项自动禁用。

依赖：customtkinter、pandas。配合 gui/window.py 的 get_active_df / set_data_filter。
"""

from tkinter import messagebox

import pandas as pd
import customtkinter as ctk

from gui.widgets import BORDER_WIDTH, UI_COLORS as COLORS


ALL_COUNTRIES = "全部"
NO_COUNTRY = "（无国家列）"
MONTHS = [f"{m:02d}" for m in range(1, 13)]


class FilterBar(ctk.CTkFrame):
    """全局筛选栏：日期范围（年-月下拉）+ 国家。"""

    def __init__(self, master, app):
        super().__init__(
            master,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=0,
            height=52,
        )
        self.app = app
        self.pack_propagate(False)

        # 起止年月（StringVar），国家
        self.year_from_var = ctk.StringVar()
        self.month_from_var = ctk.StringVar(value="01")
        self.year_to_var = ctk.StringVar()
        self.month_to_var = ctk.StringVar(value="12")
        self.country_var = ctk.StringVar(value=ALL_COUNTRIES)
        self.status_var = ctk.StringVar(value="")

        # 数据日期范围（refresh_options 时填）
        self._dmin = None
        self._dmax = None

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="🔎 全局筛选", font=("SimHei", 12, "bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=(16, 12))

        # 日期：从 [年][月] 至 [年][月]
        ctk.CTkLabel(
            self, text="日期 从", font=("SimHei", 11), text_color=COLORS["muted"],
        ).pack(side="left", padx=(0, 4))
        self.year_from_menu = ctk.CTkOptionMenu(
            self, variable=self.year_from_var, values=["--"],
            font=("SimHei", 11), width=78,
        )
        self.year_from_menu.pack(side="left", padx=(0, 2))
        ctk.CTkOptionMenu(
            self, variable=self.month_from_var, values=MONTHS,
            font=("SimHei", 11), width=62,
        ).pack(side="left")

        ctk.CTkLabel(
            self, text="至", font=("SimHei", 11), text_color=COLORS["muted"],
        ).pack(side="left", padx=6)

        self.year_to_menu = ctk.CTkOptionMenu(
            self, variable=self.year_to_var, values=["--"],
            font=("SimHei", 11), width=78,
        )
        self.year_to_menu.pack(side="left", padx=(0, 2))
        ctk.CTkOptionMenu(
            self, variable=self.month_to_var, values=MONTHS,
            font=("SimHei", 11), width=62,
        ).pack(side="left", padx=(0, 12))

        # 国家
        ctk.CTkLabel(
            self, text="国家", font=("SimHei", 11), text_color=COLORS["muted"],
        ).pack(side="left", padx=(0, 4))
        self.country_menu = ctk.CTkOptionMenu(
            self, variable=self.country_var, values=[ALL_COUNTRIES],
            font=("SimHei", 11), width=150,
        )
        self.country_menu.pack(side="left", padx=(0, 12))

        # 按钮
        ctk.CTkButton(
            self, text="应用筛选", command=self._on_apply,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            font=("SimHei", 11, "bold"), height=30, width=90, corner_radius=6,
        ).pack(side="left")
        ctk.CTkButton(
            self, text="清除", command=self._on_clear,
            fg_color=COLORS["gray"], hover_color=COLORS["gray_hover"],
            font=("SimHei", 11, "bold"), height=30, width=70, corner_radius=6,
        ).pack(side="left", padx=8)

        # 「字段映射」：随时重开映射对话框（回显当前映射），改完自动清下游重算。
        # 用琥珀色与蓝色筛选按钮区分——它不是筛选动作，而是切换分析口径。
        ctk.CTkButton(
            self, text="⚙ 字段映射", command=self._on_remap,
            fg_color=COLORS["amber"], hover_color=COLORS.get("amber_hover", COLORS["amber"]),
            font=("SimHei", 11, "bold"), height=30, width=104, corner_radius=6,
        ).pack(side="left")

        # 当前筛选状态（右侧）
        ctk.CTkLabel(
            self, textvariable=self.status_var, font=("SimHei", 11, "bold"),
            text_color=COLORS["blue"],
        ).pack(side="right", padx=16)

    # ───── 显隐 ─────

    def show(self):
        if not self.winfo_ismapped():
            self.pack(side="top", fill="x", before=self.app.container)

    def hide(self):
        if self.winfo_ismapped():
            self.pack_forget()

    # ───── 数据 ─────

    def refresh_options(self):
        """进入分析页时：用映射后数据刷新年候选、国家下拉，并回显当前筛选。

        方案 B：筛选作用在标准列（InvoiceDate / Country）上，故取「映射后」数据；
        未映射时没有标准列可筛，直接返回（筛选栏此时也不显示）。
        """
        df = self.app.mapped_clean_df()
        if df is None:
            return

        if "InvoiceDate" in df.columns:
            try:
                dates = pd.to_datetime(df["InvoiceDate"])
                self._dmin, self._dmax = dates.min(), dates.max()
                years = [str(y) for y in range(self._dmin.year, self._dmax.year + 1)]
                self.year_from_menu.configure(values=years)
                self.year_to_menu.configure(values=years)
            except Exception:
                pass

        if "Country" in df.columns:
            countries = [ALL_COUNTRIES] + sorted(
                df["Country"].dropna().astype(str).unique().tolist()
            )
            self.country_menu.configure(values=countries, state="normal")
        else:
            self.country_menu.configure(values=[NO_COUNTRY], state="disabled")
            self.country_var.set(NO_COUNTRY)

        self._sync_from_app()
        self._update_status()

    def _sync_from_app(self):
        """把 app.data_filter 回显到控件（切页后保持已选筛选）。"""
        f = self.app.data_filter
        # 起始年月：有筛选用筛选值，否则填数据最早年月
        if f.get("date_from") is not None:
            self.year_from_var.set(str(f["date_from"].year))
            self.month_from_var.set(f"{f['date_from'].month:02d}")
        elif self._dmin is not None:
            self.year_from_var.set(str(self._dmin.year))
            self.month_from_var.set(f"{self._dmin.month:02d}")
        # 结束年月：有筛选用筛选值，否则填数据最晚年月
        if f.get("date_to") is not None:
            self.year_to_var.set(str(f["date_to"].year))
            self.month_to_var.set(f"{f['date_to'].month:02d}")
        elif self._dmax is not None:
            self.year_to_var.set(str(self._dmax.year))
            self.month_to_var.set(f"{self._dmax.month:02d}")

        if self.country_menu.cget("state") != "disabled":
            self.country_var.set(f.get("country") or ALL_COUNTRIES)

    def _read_dates(self):
        """从年月下拉构造 (date_from, date_to)；date_to 取该月最后一刻。"""
        yf, mf = int(self.year_from_var.get()), int(self.month_from_var.get())
        yt, mt = int(self.year_to_var.get()), int(self.month_to_var.get())
        date_from = pd.Timestamp(year=yf, month=mf, day=1)
        month_end = pd.Timestamp(year=yt, month=mt, day=1) + pd.offsets.MonthEnd(1)
        date_to = month_end + pd.Timedelta(hours=23, minutes=59, seconds=59)
        return date_from, date_to

    def _on_apply(self):
        try:
            date_from, date_to = self._read_dates()
        except Exception:
            messagebox.showwarning("日期未选择", "请先选择起止年月。")
            return
        if date_from > date_to:
            messagebox.showwarning("日期范围有误", "开始年月不能晚于结束年月。")
            return

        country = self.country_var.get()
        country = None if country in (ALL_COUNTRIES, NO_COUNTRY) else country

        self.app.set_data_filter(date_from=date_from, date_to=date_to, country=country)
        self._update_status()

    def _on_remap(self):
        """重新打开字段映射对话框（回显当前映射）；确认后由 App 清下游并刷新。"""
        self.app.open_field_mapping(show_intro=False)

    def _on_clear(self):
        # 年月恢复到数据全范围
        if self._dmin is not None:
            self.year_from_var.set(str(self._dmin.year))
            self.month_from_var.set(f"{self._dmin.month:02d}")
        if self._dmax is not None:
            self.year_to_var.set(str(self._dmax.year))
            self.month_to_var.set(f"{self._dmax.month:02d}")
        if self.country_menu.cget("state") != "disabled":
            self.country_var.set(ALL_COUNTRIES)
        self.app.set_data_filter()  # 全部置空
        self._update_status()

    def _update_status(self):
        """显示当前是全量还是筛选后子集，以及行数。"""
        active = self.app.get_active_df()
        total = self.app.cleaner.df if self.app.cleaner else None
        if active is None or total is None:
            self.status_var.set("")
            return
        if len(active) == len(total):
            self.status_var.set(f"当前：全部 {len(total):,} 行")
        else:
            self.status_var.set(f"当前：筛选后 {len(active):,} / {len(total):,} 行")
