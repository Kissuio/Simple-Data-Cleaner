"""字段映射对话框（方案 B：进入分析前才弹出）。

目标：
- 本系统不再只认一种列结构，而是支持「任意商家的交易表」；
- 加载、清洗阶段都用原始列名自由操作；进入分析（RFM / 销售 / 商品 / 总览）前，
  把分析需要的标准字段逐一列出，每个给一个下拉，让用户从清洗后表的实际列里
  指认对应关系（如「会员卡号」→ CustomerID）；
- 下拉默认值由 field_mapping.guess_mapping() 自动猜好，多数情况下用户只需确认；
- 每个下拉旁显示选中列的样例值，帮助判断选得对不对。

与旧版的区别（方案 B）：
- 输入是「清洗后的 DataFrame」而非 FileLoader，且**不会改动 df**——
  确认后只把映射字典通过 on_confirm 回传给 App（存到 app.field_mapping），
  真正的重命名 / 派生由 get_active_df → apply_field_mapping 在取数时完成；
- 标准字段表来自 field_mapping.STANDARD_FIELDS，多了「销售额」(TotalPrice) 一项：
  不选时若有数量+单价会自动按「数量 × 单价」派生。

依赖：customtkinter。配合 data_handlers/field_mapping.py 的 guess_mapping。
"""

from tkinter import messagebox

import customtkinter as ctk

from data_handlers.field_mapping import STANDARD_FIELDS, FIELD_USAGE, guess_mapping
from gui.widgets import BORDER_WIDTH, UI_COLORS as COLORS


# 下拉里表示「这个标准字段在我的表里不存在」的占位项
NO_MAP = "（不映射）"


class MappingDialog(ctk.CTkToplevel):
    """字段映射独立窗口（模态）。

    参数:
        master:          父窗口
        df:              清洗后的 DataFrame（原始列名，本对话框不会改动它）
        on_confirm:      用户确认并通过校验后的回调，签名 on_confirm(mapping: dict)
                         mapping = {标准字段: 实际列名 or None}
        current_mapping: 已有映射（再次打开时回显），dict 或 None
        on_cancel:       用户取消（关闭窗口）时的回调，签名 on_cancel()，可选
    """

    def __init__(
        self,
        master,
        df,
        on_confirm,
        current_mapping=None,
        on_cancel=None,
        guide_title=None,
        guide_body=None,
    ):
        super().__init__(master)
        self.df = df
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.guide_title = guide_title
        self.guide_body = guide_body
        self._confirmed = False

        self.title("字段映射 —— 把你的列对应到标准字段")
        self.geometry("720x720")
        self.configure(fg_color=COLORS["page_bg"])

        self.actual_cols = list(df.columns)
        # 初始建议：优先沿用已有映射，缺的用自动猜测补
        guessed = guess_mapping(self.actual_cols)
        self.suggestion = {}
        for std, _, _ in STANDARD_FIELDS:
            if current_mapping and current_mapping.get(std):
                self.suggestion[std] = current_mapping[std]
            else:
                self.suggestion[std] = guessed.get(std)

        self.menus = {}    # 标准字段 → StringVar（下拉当前值）
        self.samples = {}  # 标准字段 → StringVar（样例值显示）

        self._build_ui()

        # 关闭窗口（点 X）走取消逻辑，避免主界面卡在「待映射」
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.transient(master)
        self.after(100, self._raise_to_front)
        self.grab_set()  # 模态：映射是进入分析的必经步骤

    def _raise_to_front(self):
        self.lift()
        self.focus_force()

    # ───── UI 构建 ─────

    def _build_ui(self):
        # 顶部说明
        head = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        head.pack(fill="x", padx=20, pady=(18, 6))
        ctk.CTkLabel(
            head,
            text="请把你表格里的列，对应到分析需要的标准字段",
            font=("SimHei", 15, "bold"),
            text_color=COLORS["text"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            head,
            text=(
                f"当前清洗后数据 {len(self.actual_cols)} 列、{len(self.df):,} 行。"
                "下拉已自动猜好，多数情况直接点底部「确认映射」即可；猜错的请手动改。"
                "标「必需」=任何分析都要（客户/订单号/日期）；其余按需映射——"
                "缺了不挡确认，进入用到它的分析页时会提示补映射。"
                "金额：映射「销售额」，或同时给「数量」「单价」（自动算销售额），二者至少一种。"
            ),
            font=("SimHei", 11),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=660,
        ).pack(fill="x", pady=(4, 0))

        # 中部：可滚动的映射行列表
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["panel_soft"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=8,
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        options = self.actual_cols + [NO_MAP]
        for std, cn, required in STANDARD_FIELDS:
            self._build_row(scroll, std, cn, required, options)

        # 底部按钮
        action = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        action.pack(fill="x", padx=20, pady=(6, 16))

        ctk.CTkButton(
            action,
            text="确认映射",
            command=self._on_confirm,
            fg_color=COLORS["blue"],
            hover_color=COLORS["blue_hover"],
            font=("SimHei", 13, "bold"),
            height=38,
            width=140,
            corner_radius=6,
        ).pack(side="left")

        ctk.CTkButton(
            action,
            text="一键采用建议",
            command=self._reset_to_guess,
            fg_color=COLORS["gray"],
            hover_color=COLORS["gray_hover"],
            font=("SimHei", 12, "bold"),
            height=38,
            width=130,
            corner_radius=6,
        ).pack(side="left", padx=10)

        if self.guide_body:
            ctk.CTkButton(
                action,
                text="RFM / 映射说明",
                command=self._show_guide,
                fg_color=COLORS["amber"],
                hover_color=COLORS.get("amber_hover", COLORS["amber"]),
                font=("SimHei", 12, "bold"),
                height=38,
                width=145,
                corner_radius=6,
            ).pack(side="left")

        ctk.CTkButton(
            action,
            text="取消",
            command=self._on_close,
            fg_color=COLORS["gray"],
            hover_color=COLORS["gray_hover"],
            font=("SimHei", 12, "bold"),
            height=38,
            width=90,
            corner_radius=6,
        ).pack(side="right")

    def _show_guide(self):
        """在映射窗口上方打开可重复查看的 RFM 与字段说明。"""
        from gui.intro_dialog import IntroDialog

        IntroDialog(
            self,
            title=self.guide_title or "RFM 与字段映射说明",
            body=self.guide_body,
            on_close=self.grab_set,
        )

    def _build_row(self, parent, std, cn, required, options):
        row = ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"],
            border_width=BORDER_WIDTH,
            corner_radius=6,
        )
        row.pack(fill="x", padx=8, pady=4)

        # 左：字段中文名 + 「标准名 · 必需/可选」徽章
        left = ctk.CTkFrame(row, fg_color="transparent", corner_radius=0)
        left.pack(side="left", padx=12, pady=10)
        ctk.CTkLabel(
            left, text=cn, font=("SimHei", 13, "bold"),
            text_color=COLORS["text"], anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text=std, font=("SimHei", 9),
            text_color=COLORS["muted"], anchor="w",
        ).pack(anchor="w")
        # 用途标注：标清这列给哪个分析用（必需=红、金额=琥珀、商品=绿、可选=灰）
        usage = FIELD_USAGE.get(std, "可选")
        if required:
            usage_color = COLORS["red"]
        elif std == "TotalPrice":
            usage_color = COLORS["amber"]
        elif std == "Country":
            usage_color = COLORS["muted"]
        else:
            usage_color = COLORS["green"]
        ctk.CTkLabel(
            left, text=usage, font=("SimHei", 9, "bold"),
            text_color=usage_color, anchor="w", justify="left",
        ).pack(anchor="w", pady=(1, 0))

        # 右：下拉 + 样例值
        right = ctk.CTkFrame(row, fg_color="transparent", corner_radius=0)
        right.pack(side="right", padx=12, pady=8)

        var = ctk.StringVar(value=self.suggestion.get(std) or NO_MAP)
        self.menus[std] = var
        sample_var = ctk.StringVar(value=self._sample_of(var.get()))
        self.samples[std] = sample_var

        ctk.CTkOptionMenu(
            right,
            variable=var,
            values=options,
            command=lambda v, s=std: self.samples[s].set(self._sample_of(v)),
            font=("SimHei", 11),
            width=240,
        ).pack(anchor="e")
        ctk.CTkLabel(
            right, textvariable=sample_var, font=("SimHei", 9),
            text_color=COLORS["muted"], anchor="e",
        ).pack(anchor="e", pady=(2, 0))

    # ───── 逻辑 ─────

    def _sample_of(self, col):
        """取某实际列的第一个非空样例值，给用户判断映射对不对。"""
        if col == NO_MAP or col not in self.df.columns:
            return "（不映射）" if col == NO_MAP else ""
        series = self.df[col].dropna()
        if len(series) == 0:
            return "样例：（整列为空）"
        return f"样例：{series.iloc[0]}"

    def _reset_to_guess(self):
        """把所有下拉恢复成自动猜测的建议值。"""
        for std, var in self.menus.items():
            value = self.suggestion.get(std) or NO_MAP
            var.set(value)
            self.samples[std].set(self._sample_of(value))

    def _collect_mapping(self):
        mapping = {}
        for std, var in self.menus.items():
            value = var.get()
            mapping[std] = None if value == NO_MAP else value
        return mapping

    def _validate(self, mapping):
        """校验映射：必需字段已选、无重复列、销售额可派生。返回错误信息列表。"""
        errors = []

        # 必需字段必须映射
        required = [(std, cn) for std, cn, req in STANDARD_FIELDS if req]
        for std, cn in required:
            if not mapping.get(std):
                errors.append(f"必需字段「{cn}」({std}) 尚未映射。")

        # 同一实际列不能映射到多个标准字段
        seen = {}
        for std, col in mapping.items():
            if not col:
                continue
            if col in seen:
                errors.append(f"列「{col}」被同时指定给 {seen[col]} 和 {std}，请改其一。")
            else:
                seen[col] = std

        # 销售额未映射时，需要数量+单价才能自动派生
        if not mapping.get("TotalPrice"):
            if not (mapping.get("Quantity") and mapping.get("UnitPrice")):
                errors.append(
                    "「销售额」未映射，且缺少「数量」或「单价」无法自动派生 —— "
                    "请映射销售额列，或同时映射数量与单价。"
                )
        return errors

    def _on_confirm(self):
        mapping = self._collect_mapping()
        errors = self._validate(mapping)
        if errors:
            messagebox.showerror("映射有误", "\n".join(errors), parent=self)
            return
        self._confirmed = True
        self.grab_release()
        # 只保留有值的项，回传给 App（存到 app.field_mapping）
        clean = {std: col for std, col in mapping.items() if col}
        self.on_confirm(clean)
        self.destroy()

    def _on_close(self):
        """取消或点 X：通知调用方（若有），不写入任何映射。"""
        if not self._confirmed and self.on_cancel is not None:
            self.on_cancel()
        self.grab_release()
        self.destroy()
