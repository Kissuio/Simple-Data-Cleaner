"""清洗工具箱的参数对话框：点一把通用刀的按钮后弹出，让用户选「作用在哪列、什么参数」。

设计要点：
- 每把刀需要的参数由 TOOLBOX 里的 schema 描述，对话框据此动态生成控件——
  不写死任何表结构，换什么表都从该表的实际列里选；
- 选列、选值都用 CTkScrollableFrame 做成**带滚动条**的单选/多选列表，
  避免列很多、或某列取值上千时，原生下拉把菜单顶出屏幕；
- 选了文本列后，「值」的候选会刷成该列的实际取值（截断 + 仍可手输）。

配合 data_handlers/data_cleaner.py 的通用原语方法（方法名 = TOOLBOX 每项的 key）。
"""

from tkinter import messagebox

import customtkinter as ctk

from gui.widgets import BORDER_WIDTH, UI_COLORS as COLORS


# 「值」候选最多列这么多项；超过则截断（用户仍可在输入框手动输入）
VALUE_CANDIDATE_LIMIT = 300

# 弹窗高度控制：删除行工具箱含高级多参数工具，原本会撑到 840，视觉上过长。
CLEAN_DIALOG_WIDTH = 560
CLEAN_DIALOG_BASE_HEIGHT = 250
CLEAN_DIALOG_DEFAULT_MAX_HEIGHT = 840
CLEAN_DIALOG_DELETE_ROW_MAX_HEIGHT = 590
CLEAN_DIALOG_PARAM_HEIGHTS = {
    "single_col": 150,
    "multi_col": 195,
    "value": 195,
    "choice": 70,
    "number": 70,
    "text": 70,
}


# 通用清洗工具箱。每项：
#   key   —— DataCleaner 上的方法名
#   label —— 按钮文字（通用动作，不绑表结构、不编号）
#   hint  —— 一句说明
#   params—— 参数 schema；kind ∈ single_col / multi_col / choice / number / text / value
TOOLBOX = [
    {"key": "drop_duplicates", "label": "删重复行",
     "hint": "删除完全重复的整行（无需选列）。", "params": []},

    {"key": "drop_missing", "label": "删空值行",
     "hint": "选哪些列：这些列为空就删掉该行。",
     "params": [{"name": "columns", "kind": "multi_col",
                 "title": "对哪些列检查空值", "select_all": True}]},

    {"key": "drop_by_text", "label": "按文本条件删行",
     "hint": "如：发票号「开头是」C（删取消单）、状态「等于」已取消、编码「在清单中」黑名单。",
     "params": [
         {"name": "column", "kind": "single_col", "title": "作用的列"},
         {"name": "op", "kind": "choice", "title": "条件",
          "choices": [("等于", "equals"), ("包含", "contains"),
                      ("开头是", "startswith"), ("在清单中(逗号分隔)", "in_list")]},
         {"name": "value", "kind": "value", "title": "值（可点下方候选填入）", "depends": "column"},
     ]},

    {"key": "drop_by_range", "label": "按数值条件删行",
     "hint": "如：数量 ≤ 0、单价 ≤ 0。",
     "params": [
         {"name": "column", "kind": "single_col", "title": "作用的列"},
         {"name": "op", "kind": "choice", "title": "比较",
          "choices": [("≤", "<="), ("<", "<"), ("≥", ">="), (">", ">"), ("=", "==")]},
         {"name": "threshold", "kind": "number", "title": "阈值", "default": "0"},
     ]},

    {"key": "coerce_numeric", "label": "列转数值",
     "hint": "把 \"1,200\" / \"￥10.5\" 这类脏字符串转成纯数字（换商家表常用）。",
     "params": [{"name": "columns", "kind": "multi_col",
                 "title": "转哪些列为数值（不选=默认 数量/单价）",
                 "default_cols": ["Quantity", "UnitPrice"], "optional": True}]},

    {"key": "normalize_text", "label": "文本规整",
     "hint": "去首尾空格、压缩连续空格；可统一大小写（不选列=全部文本列）。",
     "params": [
         {"name": "columns", "kind": "multi_col",
          "title": "规整哪些列（不选=全部文本列）", "optional": True},
         {"name": "case", "kind": "choice", "title": "大小写",
          "choices": [("不变", ""), ("全大写", "upper"), ("全小写", "lower")]},
     ]},

    {"key": "convert_date", "label": "列转日期",
     "hint": "把某列解析成日期（供月度趋势 / Recency 用）。",
     "params": [{"name": "column", "kind": "single_col", "title": "日期列",
                 "default_cols": ["InvoiceDate"]}]},

    {"key": "derive_column", "label": "派生新列",
     "hint": "新列 = 列A 运算 列B，如 TotalPrice = 数量 × 单价。",
     "params": [
         {"name": "new_col", "kind": "text", "title": "新列名", "default": "TotalPrice"},
         {"name": "col_a", "kind": "single_col", "title": "列 A", "default_cols": ["Quantity"]},
         {"name": "op", "kind": "choice", "title": "运算",
          "choices": [("×", "*"), ("＋", "+"), ("－", "-"), ("÷", "/")]},
         {"name": "col_b", "kind": "single_col", "title": "列 B", "default_cols": ["UnitPrice"]},
     ]},

    {"key": "drop_cancellation_pairs", "label": "高级·删取消单+配对正单",
     "hint": "删取消单及其对应的原始正单。需指定 5 个列，缺列会自动跳过。",
     "params": [
         {"name": "invoice_col", "kind": "single_col", "title": "发票号列",
          "default_cols": ["InvoiceNo"]},
         {"name": "customer_col", "kind": "single_col", "title": "客户列",
          "default_cols": ["CustomerID"]},
         {"name": "code_col", "kind": "single_col", "title": "商品编码列",
          "default_cols": ["StockCode"]},
         {"name": "price_col", "kind": "single_col", "title": "单价列",
          "default_cols": ["UnitPrice"]},
         {"name": "qty_col", "kind": "single_col", "title": "数量列",
          "default_cols": ["Quantity"]},
         {"name": "prefix", "kind": "text", "title": "取消单前缀", "default": "C"},
     ]},
]


# 把 9 把刀按大类分组：GUI 上每类合并成一个按钮，点开在弹窗顶部下拉选具体操作
CATEGORIES = [
    {"name": "删除行", "keys": [
        "drop_duplicates", "drop_missing", "drop_by_text",
        "drop_by_range", "drop_cancellation_pairs"]},
    {"name": "转换列类型", "keys": ["coerce_numeric", "convert_date"]},
    {"name": "整理 / 派生", "keys": ["normalize_text", "derive_column"]},
]


def steps_in_category(cat):
    """取某大类下的 step 列表（按 keys 顺序）。"""
    by_key = {s["key"]: s for s in TOOLBOX}
    return [by_key[k] for k in cat["keys"] if k in by_key]


def clean_dialog_param_height(param):
    """Estimate the vertical space needed by one parameter control."""
    return CLEAN_DIALOG_PARAM_HEIGHTS.get(param["kind"], 90)


def clean_dialog_height(steps, title):
    """Estimate dialog height for a cleaning toolbox category."""
    max_params_height = max(
        (sum(clean_dialog_param_height(p) for p in step["params"]) for step in steps),
        default=0,
    )
    max_height = (
        CLEAN_DIALOG_DELETE_ROW_MAX_HEIGHT
        if title == "删除行"
        else CLEAN_DIALOG_DEFAULT_MAX_HEIGHT
    )
    return min(max_height, CLEAN_DIALOG_BASE_HEIGHT + max_params_height)


class _ScrollList(ctk.CTkFrame):
    """单选/多选列表（普通容器、自身不滚动）。

    刻意不自带滚动条：由对话框「参数区」的外层统一滚动，避免内外两层滚动框
    嵌套（在内层列表上滚时外层跟着动）。列/候选很多时，靠外层那一条滚动条滚到。
    """

    def __init__(self, master, options, multi=False, preselect=None, on_change=None):
        super().__init__(
            master, fg_color="#ffffff",
            border_color=COLORS["border"], border_width=BORDER_WIDTH, corner_radius=6,
        )
        self.multi = multi
        self.on_change = on_change
        self._sel = ctk.StringVar(value="")
        self.vars = {}
        self._render(options, preselect or [])

    def _render(self, options, preselect):
        for w in self.winfo_children():
            w.destroy()
        self.vars = {}
        if self.multi:
            for opt in options:
                v = ctk.BooleanVar(value=opt in preselect)
                ctk.CTkCheckBox(
                    self, text=opt, variable=v, font=("SimHei", 11),
                    command=self._changed,
                ).pack(anchor="w", padx=8, pady=2)
                self.vars[opt] = v
        else:
            init = preselect[0] if preselect else (options[0] if options else "")
            self._sel.set(init)
            for opt in options:
                ctk.CTkRadioButton(
                    self, text=opt, variable=self._sel, value=opt,
                    font=("SimHei", 11), command=self._changed,
                ).pack(anchor="w", padx=8, pady=2)

    def set_options(self, options):
        """刷新候选项（「值」候选随所选列变化时用）；尽量保留当前选择。"""
        cur = self.get()
        keep = [cur] if (not self.multi and cur in options) else []
        self._render(options, keep)

    def _changed(self):
        if self.on_change:
            self.on_change(self.get())

    def select_all(self):
        """选中多选列表里的全部候选项。"""
        if not self.multi:
            return
        for var in self.vars.values():
            var.set(True)
        self._changed()

    def clear_all(self):
        """清空多选列表里的全部选择。"""
        if not self.multi:
            return
        for var in self.vars.values():
            var.set(False)
        self._changed()

    def get(self):
        if self.multi:
            return [k for k, v in self.vars.items() if v.get()]
        return self._sel.get()


class CleanStepDialog(ctk.CTkToplevel):
    """清洗大类的参数对话框（模态）：顶部下拉选该类下的具体操作，下方填参数。

    参数:
        master:    父窗口
        df:        当前（已清洗到此刻）的 DataFrame，用来列出可选列与取值候选
        steps:     同一大类下的 step 列表（每个含 key/label/hint/params）
        title:     大类名（窗口标题用）
        on_submit: 点「执行」并通过校验后的回调，签名 on_submit(method_name, kwargs)
    """

    def __init__(self, master, df, steps, title, on_submit):
        super().__init__(master)
        self.df = df
        self.columns = list(df.columns)
        self.steps = steps
        self.step = steps[0]      # 当前选中的操作（顶部下拉切换）
        self.on_submit = on_submit

        self._getters = {}        # 参数名 -> 取值函数
        self._value_var = None    # 「值」输入框的 StringVar
        self._value_list = None   # 「值」候选滚动列表

        self.title(f"清洗 —— {title}")
        # 高度按该类里「参数最多」的操作估，避免切换操作时窗口忽高忽低；
        # 删除行工具箱参数最多，初始高度单独压短，靠内部滚动承载完整内容。
        h = clean_dialog_height(steps, title)
        self.geometry(f"{CLEAN_DIALOG_WIDTH}x{h}")
        self.configure(fg_color=COLORS["page_bg"])

        self._build()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.transient(master)
        self.after(100, self._raise_to_front)
        self.grab_set()  # 模态

    def _raise_to_front(self):
        self.lift()
        self.focus_force()

    # 各类参数控件的估高（用于对话框自适应高度）
    _PARAM_H = CLEAN_DIALOG_PARAM_HEIGHTS

    def _param_height(self, p):
        return clean_dialog_param_height(p)

    # ───── UI ─────

    def _build(self):
        head = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        head.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            head, text="操作", font=("SimHei", 12, "bold"),
            text_color=COLORS["text"], anchor="w",
        ).pack(fill="x")
        self._op_var = ctk.StringVar(value=self.step["label"])
        ctk.CTkOptionMenu(
            head, variable=self._op_var, values=[s["label"] for s in self.steps],
            command=self._on_pick_op, font=("SimHei", 12), width=320,
        ).pack(anchor="w", pady=(2, 6))
        self._hint_var = ctk.StringVar(value=self.step["hint"])
        ctk.CTkLabel(
            head, textvariable=self._hint_var, font=("SimHei", 11),
            text_color=COLORS["muted"], anchor="w", justify="left", wraplength=510,
        ).pack(fill="x")

        # 底部按钮先 pack 到「底部」：参数再多也始终可见，不会被顶出屏幕。
        action = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        action.pack(side="bottom", fill="x", padx=20, pady=(4, 14))
        ctk.CTkButton(
            action, text="执行", command=self._submit,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            font=("SimHei", 13, "bold"), height=38, width=130, corner_radius=6,
        ).pack(side="left")
        ctk.CTkButton(
            action, text="取消", command=self.destroy,
            fg_color=COLORS["gray"], hover_color=COLORS["gray_hover"],
            font=("SimHei", 12, "bold"), height=38, width=90, corner_radius=6,
        ).pack(side="right")

        # 参数区改「可滚动」外层：参数多（如高级刀 6 个）时整体滚动。内层选列/选值
        # 列表本身不滚（普通容器），所以全程只有这一条滚动条，不会两层嵌套打架。
        self.param_frame = ctk.CTkScrollableFrame(
            self, fg_color=COLORS["panel_soft"],
            border_color=COLORS["border"], border_width=BORDER_WIDTH, corner_radius=8,
        )
        self.param_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)
        self._render_params()

    def _on_pick_op(self, label):
        """顶部下拉切换具体操作：换 hint、重建参数区。"""
        self.step = next(s for s in self.steps if s["label"] == label)
        self._hint_var.set(self.step["hint"])
        self._render_params()

    def _render_params(self):
        """按当前选中操作重建参数控件（切换操作时先清空旧控件与取值器）。"""
        for w in self.param_frame.winfo_children():
            w.destroy()
        self._getters = {}
        self._value_var = None
        self._value_list = None
        if not self.step["params"]:
            ctk.CTkLabel(
                self.param_frame, text="（此操作无需参数，直接点「执行」）",
                font=("SimHei", 12), text_color=COLORS["muted"], anchor="w",
            ).pack(fill="x", padx=12, pady=16)
            return
        for p in self.step["params"]:
            self._build_param(self.param_frame, p)

    def _build_param(self, parent, p):
        kind = p["kind"]
        ctk.CTkLabel(
            parent, text=p["title"], font=("SimHei", 12, "bold"),
            text_color=COLORS["text"], anchor="w",
        ).pack(fill="x", padx=10, pady=(10, 2))

        if kind == "single_col":
            pre = [c for c in p.get("default_cols", []) if c in self.columns]
            lst = _ScrollList(parent, self.columns, multi=False, preselect=pre,
                              on_change=self._on_depends_change)
            lst.pack(fill="x", padx=10, pady=(0, 4))
            self._getters[p["name"]] = lst.get

        elif kind == "multi_col":
            pre = [c for c in p.get("default_cols", []) if c in self.columns]
            lst = _ScrollList(parent, self.columns, multi=True, preselect=pre)
            if p.get("select_all"):
                controls = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
                controls.pack(fill="x", padx=10, pady=(0, 4))
                ctk.CTkButton(
                    controls, text="一键全选", command=lst.select_all,
                    fg_color=COLORS["blue_soft"], hover_color="#dbeafe",
                    text_color=COLORS["blue"], border_color=COLORS["blue"],
                    border_width=1, font=("SimHei", 10, "bold"),
                    height=28, width=90, corner_radius=6,
                ).pack(side="left")
                ctk.CTkButton(
                    controls, text="取消全选", command=lst.clear_all,
                    fg_color="#ffffff", hover_color=COLORS["panel_soft"],
                    text_color=COLORS["muted"], border_color=COLORS["border"],
                    border_width=1, font=("SimHei", 10),
                    height=28, width=90, corner_radius=6,
                ).pack(side="left", padx=(8, 0))
            lst.pack(fill="x", padx=10, pady=(0, 4))
            self._getters[p["name"]] = lst.get

        elif kind == "choice":
            labels = [c[0] for c in p["choices"]]
            mapping = {c[0]: c[1] for c in p["choices"]}
            var = ctk.StringVar(value=labels[0])
            ctk.CTkOptionMenu(
                parent, variable=var, values=labels, font=("SimHei", 11), width=240,
            ).pack(anchor="w", padx=10, pady=(0, 4))
            self._getters[p["name"]] = lambda v=var, m=mapping: m[v.get()]

        elif kind in ("number", "text"):
            var = ctk.StringVar(value=p.get("default", ""))
            ctk.CTkEntry(parent, textvariable=var, font=("SimHei", 11), width=240).pack(
                anchor="w", padx=10, pady=(0, 4))
            self._getters[p["name"]] = lambda v=var: v.get()

        elif kind == "value":
            var = ctk.StringVar(value="")
            self._value_var = var
            ctk.CTkEntry(parent, textvariable=var, font=("SimHei", 11), width=240).pack(
                anchor="w", padx=10, pady=(0, 4))
            ctk.CTkLabel(
                parent, text="↓ 点候选填入（in_list 可逗号接多个）", font=("SimHei", 9),
                text_color=COLORS["muted"], anchor="w",
            ).pack(fill="x", padx=10)
            cand = _ScrollList(parent, self._candidates_for(self._current_depends_col()),
                               multi=False, on_change=self._pick_value)
            cand.pack(fill="x", padx=10, pady=(0, 4))
            self._value_list = cand
            self._getters[p["name"]] = lambda v=var: v.get()

    # ───── 「值」候选随依赖列联动 ─────

    def _depends_param(self):
        for p in self.step["params"]:
            if p.get("kind") == "value":
                return p
        return None

    def _current_depends_col(self):
        dep = self._depends_param()
        if not dep:
            return None
        getter = self._getters.get(dep["depends"])
        return getter() if getter else None

    def _on_depends_change(self, _col):
        if self._value_list is not None:
            self._value_list.set_options(self._candidates_for(self._current_depends_col()))

    def _candidates_for(self, col):
        if not col or col not in self.df.columns:
            return []
        vals = self.df[col].dropna().astype(str).unique().tolist()
        return vals[:VALUE_CANDIDATE_LIMIT]

    def _pick_value(self, v):
        self._value_var.set(v)

    # ───── 提交 ─────

    def _submit(self):
        raw = {name: getter() for name, getter in self._getters.items()}
        ok, msg, kwargs = self._finalize(raw)
        if not ok:
            messagebox.showwarning("参数不完整", msg, parent=self)
            return
        self.grab_release()
        self.on_submit(self.step["key"], kwargs)
        self.destroy()

    def _finalize(self, k):
        """按刀的类型做参数转换 + 必填校验，返回 (ok, 错误信息, kwargs)。"""
        key = self.step["key"]
        k = dict(k)
        if key == "drop_missing":
            if not k["columns"]:
                return False, "请至少选择一列。", None
        elif key == "coerce_numeric":
            k["columns"] = k["columns"] or None
        elif key == "normalize_text":
            k["columns"] = k["columns"] or None
            k["case"] = k["case"] or None
        elif key == "drop_by_text":
            if not k.get("column"):
                return False, "请选择作用的列。", None
            if not str(k.get("value", "")).strip():
                return False, "请填写要匹配的值。", None
            if k["op"] == "in_list":
                k["value"] = [x.strip() for x in str(k["value"]).split(",") if x.strip()]
        elif key == "drop_by_range":
            if not k.get("column"):
                return False, "请选择作用的列。", None
            try:
                k["threshold"] = float(k["threshold"])
            except (ValueError, TypeError):
                return False, "阈值必须是数字。", None
        elif key == "convert_date":
            if not k.get("column"):
                return False, "请选择日期列。", None
        elif key == "derive_column":
            if not str(k.get("new_col", "")).strip():
                return False, "请填写新列名。", None
            if not k.get("col_a") or not k.get("col_b"):
                return False, "请选择列 A 和列 B。", None
        elif key == "drop_cancellation_pairs":
            for c in ["invoice_col", "customer_col", "code_col", "price_col", "qty_col"]:
                if not k.get(c):
                    return False, "5 个列都要选齐（这是高级刀）。", None
        return True, "", k
