from collections import deque
import operator

import numpy as np
import pandas as pd
from data_handlers.base_data_handler import BaseDataHandler


# 数值比较运算符（drop_by_range 用）：NaN 参与比较得 False，不会误删
_NUM_OPS = {
    "<=": operator.le, "<": operator.lt,
    ">=": operator.ge, ">": operator.gt,
    "==": operator.eq, "!=": operator.ne,
}
# 派生列的四则运算（derive_column 用）
_ARITH_OPS = {"*": operator.mul, "+": operator.add, "-": operator.sub, "/": operator.truediv}


_COMPACT_DATE_FORMATS = {
    4: "%Y",
    6: "%Y%m",
    8: "%Y%m%d",
    10: "%Y%m%d%H",
    12: "%Y%m%d%H%M",
    14: "%Y%m%d%H%M%S",
}


def _infer_dayfirst(values):
    """根据含斜杠或短横线的日期样例推断是否采用“日在前”。

    仅把第一段大于 12 视为“日在前”证据，把第二段大于 12 视为
    “月在前”证据。证据相同或完全没有证据时返回 False，保持项目原有
    月/日口径，避免把 ``12/1/2010`` 从 12 月 1 日改成 1 月 12 日。
    """
    parts = values.astype("string").str.extract(
        r"^\s*(\d{1,2})[/-](\d{1,2})[/-]\d{2,4}(?:\D|$)"
    )
    first = pd.to_numeric(parts[0], errors="coerce")
    second = pd.to_numeric(parts[1], errors="coerce")
    dayfirst_evidence = int((first > 12).sum())
    monthfirst_evidence = int((second > 12).sum())
    return dayfirst_evidence > monthfirst_evidence


def _parse_numeric_dates(values):
    """解析数值型日期，兼容紧凑日期、Excel 序号和 Unix 时间戳。

    参数:
        values: 可转为数值的 pandas Series

    返回:
        pandas.Series: 与输入索引一致的 datetime64 Series；无法识别者为 NaT
    """
    numeric = pd.to_numeric(values, errors="coerce")
    result = pd.Series(pd.NaT, index=numeric.index, dtype="datetime64[ns]")
    rounded = numeric.round()
    integer_like = numeric.notna() & np.isclose(
        numeric, rounded, rtol=0, atol=1e-9
    )
    integer_text = rounded.astype("Int64").astype("string")

    # 先识别 YYYY、YYYYMM、YYYYMMDD、YYYYMMDDHH[MM[SS]]。
    for width, fmt in _COMPACT_DATE_FORMATS.items():
        candidates = integer_like & integer_text.str.len().eq(width)
        years = pd.to_numeric(integer_text.str.slice(0, 4), errors="coerce")
        candidates &= years.between(1678, 2261)
        candidates &= result.isna()
        if not candidates.any():
            continue
        parsed = pd.to_datetime(
            integer_text[candidates], format=fmt, errors="coerce"
        )
        valid = parsed.notna()
        result.loc[parsed.index[valid]] = parsed[valid]

    # 再按数量级识别 Unix 秒、毫秒、微秒、纳秒时间戳。
    absolute = numeric.abs()
    unix_ranges = [
        ("s", 1e8, 1e11),
        ("ms", 1e11, 1e14),
        ("us", 1e14, 1e17),
        ("ns", 1e17, 1e20),
    ]
    for unit, lower, upper in unix_ranges:
        candidates = (
            numeric.notna()
            & result.isna()
            & absolute.ge(lower)
            & absolute.lt(upper)
        )
        if not candidates.any():
            continue
        parsed = pd.to_datetime(
            numeric[candidates], unit=unit, origin="unix", errors="coerce"
        )
        valid = parsed.notna()
        result.loc[parsed.index[valid]] = parsed[valid]

    # 剩余中等数值按 Excel 1900 日期系统处理，支持小数表示的时分秒。
    excel_candidates = (
        numeric.notna()
        & result.isna()
        & numeric.ge(0)
        & numeric.lt(2_958_466)
    )
    if excel_candidates.any():
        parsed = pd.to_datetime(
            numeric[excel_candidates],
            unit="D",
            origin="1899-12-30",
            errors="coerce",
        )
        valid = parsed.notna()
        result.loc[parsed.index[valid]] = parsed[valid]

    return result


def _parse_date_series(values, dayfirst=None):
    """把一列异构日期值转换为统一 datetime Series。

    数字及纯数字字符串交给 `_parse_numeric_dates`；其余字符串使用 pandas
    的 mixed 格式逐元素解析。`dayfirst` 为 None 时根据列内样例推断，
    无明确证据时按月在前处理。
    """
    if pd.api.types.is_numeric_dtype(values):
        return _parse_numeric_dates(values)

    text = values.astype("string").str.strip()
    result = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    present = text.notna() & text.ne("")
    numeric_like = present & text.str.fullmatch(
        r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
    )

    if numeric_like.any():
        result.loc[numeric_like] = _parse_numeric_dates(
            text[numeric_like]
        )

    textual = present & ~numeric_like
    year_first = textual & text.str.match(r"^\d{4}[-/.]")
    if year_first.any():
        result.loc[year_first] = pd.to_datetime(
            text[year_first],
            format="mixed",
            errors="coerce",
            dayfirst=False,
        )

    ambiguous_order = textual & ~year_first
    if ambiguous_order.any():
        use_dayfirst = (
            _infer_dayfirst(text[ambiguous_order])
            if dayfirst is None
            else bool(dayfirst)
        )
        parsed = pd.to_datetime(
            text[ambiguous_order],
            format="mixed",
            errors="coerce",
            dayfirst=use_dayfirst,
        )
        result.loc[ambiguous_order] = parsed

    return result


class DataCleaner(BaseDataHandler):
    """通用清洗工具箱（累积式），继承 BaseDataHandler

    设计原则：不写死任何表结构。每把「刀」是一个**通用参数化原语**——
    作用在「哪一列、什么条件」由调用方（GUI 上由用户）指定，因此换任何
    商家的表都不必改代码，选自己表里的列即可（OpenRefine 式）。

    通用清洗原语:
        drop_duplicates()                  —— 删完全重复行（整行）
        drop_missing(columns)              —— 删指定列为空的行
        drop_by_text(column, op, value)    —— 按文本条件删行
                                              op: equals/contains/startswith/in_list
        drop_by_range(column, op, thr)     —— 按数值条件删行（op: <= < >= > == !=）
        coerce_numeric(columns)            —— 脏字符串列 → 数值（剥千分位/货币符号）
        normalize_text(columns, case)      —— 文本列去空格、可选统一大小写
        convert_date(column, dayfirst)     —— 指定列 → datetime
        derive_column(new, a, op, b)       —— 新列 = 列a (×+-÷) 列b

    高级刀（强表结构假设、与通用工具箱隔离）:
        drop_cancellation_pairs(...)       —— 删取消单及其配对原始正单
                                              （依赖多个固定列，缺列即跳过）

    状态管理（累积式工具箱核心）:
        undo() / reset() / row_count / can_undo

    没有写死的「一键全套」流程或固定配置——所有清洗都是按需调用的通用原语，
    用户在 GUI 上自由组合（不绑任何表结构、不假定顺序）。

    注意:
        初始化时已对传入的 df 做 .copy()，所有清洗在副本上进行；
        另存一份 _original 供 reset 跳回，不污染原始 DataFrame。
    """

    def __init__(self, df):
        """接收一个已加载的 DataFrame，初始化清洗工具箱。

        所有清洗动作都是按需调用的通用原语（作用在哪列、用什么参数由调用方传入），
        没有写死的配置项或固定流程。
        """
        super().__init__()
        self.df = df.copy()  # !! 避免与原 DataFrame 指向同一块内存 !!
        # 累积式状态：每动一刀前把当前表压入撤销栈，撤销=弹栈；另存原始供 reset。
        # 撤销栈限长，大表多步时自动丢最老快照，避免整表拷贝堆积吃爆内存。
        self._original = self.df.copy()
        self._history = deque(maxlen=15)

    # ==================== 状态管理 ====================

    def _snapshot(self):
        """在每一步删改「之前」调用：把当前 df 拷一份压入撤销栈。"""
        self._history.append(self.df.copy())

    def undo(self):
        """撤销上一步：弹出最近的快照，恢复成那一步之前的数据。"""
        if not self._history:
            self.log.append("撤销：没有可撤销的操作")
            return self.df
        self.df = self._history.pop()
        self.log.append(f"已撤销上一步，当前 {len(self.df)} 行")
        return self.df

    def reset(self):
        """重置：丢弃全部清洗，回到最初加载进来的原始数据。"""
        self.df = self._original.copy()
        self._history.clear()
        self.log.append(f"已重置到原始数据，共 {len(self.df)} 行")
        return self.df

    @property
    def row_count(self):
        """当前数据行数（GUI 实时显示「当前 N 行」用）。"""
        return 0 if self.df is None else len(self.df)

    @property
    def can_undo(self):
        """撤销栈是否非空（GUI 据此决定「撤销」是否生效）。"""
        return len(self._history) > 0

    def _is_text_col(self, col):
        """判断某列是否文本列（兼容 object 与 pandas 的 string/str dtype）。

        不同 pandas 版本字符串列的 dtype 可能是 object 或 string/str，
        统一用 is_string_dtype 判断，并排除数值列（object 里存数字的边缘情况）。
        """
        s = self.df[col]
        return pd.api.types.is_string_dtype(s) and not pd.api.types.is_numeric_dtype(s)

    # ==================== 通用清洗原语 ====================

    def drop_duplicates(self):
        """删除完全重复的行（所有列取值都相同），只保留每组第一条。

        导出或多表合并常残留完全重复记录，会虚增订单数、销量与金额。

        返回值:
            pandas.DataFrame: 去重后的 df
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")

        self._snapshot()
        before = len(self.df)
        self.df = self.df.drop_duplicates(keep="first")
        after = len(self.df)
        self.report_change(before, after)
        return self.df

    def drop_missing(self, columns):
        """删除「指定列」为空(NaN)的行（通用，不写死任何列名）

        参数:
            columns: 列名列表；任一指定列为空就删该行。不存在的列记日志并跳过。

        返回值:
            pandas.DataFrame: 清洗后的 df
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")

        cols = [c for c in columns if c in self.df.columns]
        for m in [c for c in columns if c not in self.df.columns]:
            self.log.append(f"删空值：列 '{m}' 不存在，跳过")
        if not cols:
            self.log.append("删空值：无有效列，整步跳过")
            return self.df

        self._snapshot()
        before = len(self.df)
        self.df = self.df.dropna(subset=cols)
        after = len(self.df)
        self.log.append(f"删空值：按列 {cols} 删 {before - after} 行")
        self.report_change(before, after)
        return self.df

    def drop_by_text(self, column, op, value):
        """按「文本条件」删行（通用，覆盖删取消单/删非商品/STATUS=已取消 等）

        参数:
            column: 作用的列名
            op: 条件类型
                "equals"     —— 等于 value
                "contains"   —— 包含子串 value
                "startswith" —— 以 value 开头（如取消单发票号以 'C' 开头）
                "in_list"    —— 取值在 value(列表) 中（如 StockCode 属于黑名单）
            value: 比较值；op="in_list" 时传列表，其余传单值

        列不存在或 op 未知 → 记日志并跳过（便于换数据集）。

        返回值:
            pandas.DataFrame: 清洗后的 df
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")
        if column not in self.df.columns:
            self.log.append(f"按文本删行：列 '{column}' 不存在，跳过")
            return self.df

        s = self.df[column].astype(str)
        if op == "equals":
            mask = s == str(value)
        elif op == "contains":
            mask = s.str.contains(str(value), regex=False, na=False)
        elif op == "startswith":
            mask = s.str.startswith(str(value))
        elif op == "in_list":
            seq = value if isinstance(value, (list, tuple, set)) else [value]
            vals = [str(v).strip() for v in seq if str(v).strip()]
            mask = s.isin(vals)
        else:
            self.log.append(f"按文本删行：未知条件 '{op}'，跳过")
            return self.df

        self._snapshot()
        before = len(self.df)
        self.df = self.df[~mask]
        after = len(self.df)
        self.log.append(f"按文本删行：{column} {op} {value!r} → 删 {before - after} 行")
        self.report_change(before, after)
        return self.df

    def drop_by_range(self, column, op, threshold):
        """按「数值条件」删行（通用，覆盖删 数量≤0 / 单价≤0 等）

        参数:
            column: 作用的列名
            op: 比较符，取 <= / < / >= / > / == / !=
            threshold: 阈值

        用 to_numeric(coerce) 兜底：转不出的值记 NaN，NaN 参与比较得 False，
        不会被误删。列不存在或 op 未知 → 记日志并跳过。

        返回值:
            pandas.DataFrame: 清洗后的 df
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")
        if column not in self.df.columns:
            self.log.append(f"按数值删行：列 '{column}' 不存在，跳过")
            return self.df
        if op not in _NUM_OPS:
            self.log.append(f"按数值删行：未知比较 '{op}'，跳过")
            return self.df

        self._snapshot()
        before = len(self.df)
        nums = pd.to_numeric(self.df[column], errors="coerce")
        mask = _NUM_OPS[op](nums, threshold).fillna(False)
        self.df = self.df[~mask]
        after = len(self.df)
        self.log.append(f"按数值删行：{column} {op} {threshold} → 删 {before - after} 行")
        self.report_change(before, after)
        return self.df

    def coerce_numeric(self, columns=None):
        """把数值列里的脏字符串强制转成数值（千分位/货币符号/空格 → 纯数字）

        通用化场景：别家表的金额、数量可能存成 "1,200"、"￥10.5"、" 5 " 这类
        带符号的字符串，直接参与乘法或比较会报错或得 NaN。先剥掉所有非
        「数字/小数点/负号」的字符，再 to_numeric(errors="coerce")。

        columns 默认 ["Quantity", "UnitPrice"]；只动「存在且当前不是数值类型」
        的列。无目标列则整步跳过、不拍快照。

        返回值:
            pandas.DataFrame: 转换后的 df
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")

        cols = columns if columns is not None else ["Quantity", "UnitPrice"]
        targets = [
            c for c in cols
            if c in self.df.columns and not pd.api.types.is_numeric_dtype(self.df[c])
        ]
        if not targets:
            self.log.append("数值类型强制：目标列已是数值或不存在，跳过")
            return self.df

        self._snapshot()
        for col in targets:
            cleaned = self.df[col].astype(str).str.replace(r"[^\d.\-]", "", regex=True)
            self.df[col] = pd.to_numeric(cleaned, errors="coerce")
        self.log.append(f"数值类型强制：已转换列 {targets}")
        return self.df

    def normalize_text(self, columns=None, case=None):
        """规整文本列：去首尾空格、压缩内部连续空格；可选统一大小写

        换商家表时同一含义常有多种写法（"uk" / "UK" / " United Kingdom "），
        会让筛选、分组、TOP 榜把本属一类的拆开。

        columns 默认处理所有文本列；case="upper"/"lower"/None 控制是否统一大小写
        （默认 None 不改，避免改坏专有名词）。用 is_string_dtype 判断文本列，
        不写死 object（不同 pandas 版本字符串列 dtype 可能是 string/str）。

        返回值:
            pandas.DataFrame: 规整后的 df
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")

        if columns is not None:
            cols = [c for c in columns if c in self.df.columns]
        else:
            cols = [c for c in self.df.columns if self._is_text_col(c)]
        if not cols:
            self.log.append("字符串规整：无文本列可处理，跳过")
            return self.df

        self._snapshot()
        done = []
        for col in cols:
            if not self._is_text_col(col):
                continue  # 用户若指定了非文本列，跳过（.str 会报错）
            s = self.df[col].str.strip().str.replace(r"\s+", " ", regex=True)
            if case == "upper":
                s = s.str.upper()
            elif case == "lower":
                s = s.str.lower()
            self.df[col] = s
            done.append(col)
        self.log.append(f"字符串规整：列 {done}，大小写={case or '不变'}")
        return self.df

    def convert_date(self, column="InvoiceDate", dayfirst=None):
        """把指定列转为 datetime，兼容常见电商导出日期格式。

        支持：
        - 紧凑数字日期：YYYY、YYYYMM、YYYYMMDD、YYYYMMDDHHMMSS 等；
        - Excel 1900 日期序号及带小数的时间；
        - Unix 秒、毫秒、微秒、纳秒时间戳；
        - ISO、斜杠、短横线及同列混合字符串格式。

        参数:
            column: 要转换的列名
            dayfirst: True 表示日/月，False 表示月/日；None 时根据同列中
                大于 12 的日期段自动推断，无证据时默认月在前

        返回:
            pandas.DataFrame: 日期列已转换的新当前状态；无法解析的值为 NaT

        副作用:
            转换前保存撤销快照，并在 log 中记录成功率、失败数及失败样例
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")
        if column not in self.df.columns:
            self.log.append(f"日期转换：列 '{column}' 不存在，跳过")
            return self.df

        col = self.df[column]
        if pd.api.types.is_datetime64_any_dtype(col):
            self.log.append(f"{column} 已是 datetime 类型，无需转换")
            return self.df

        self._snapshot()
        parsed = _parse_date_series(col, dayfirst=dayfirst)
        self.df[column] = parsed

        original_text = col.astype("string").str.strip()
        supplied = original_text.notna() & original_text.ne("")
        supplied_count = int(supplied.sum())
        success_count = int(parsed[supplied].notna().sum())
        failed = supplied & parsed.isna()
        failed_count = int(failed.sum())
        success_rate = success_count / supplied_count if supplied_count else 1.0
        self.log.append(
            f"日期转换：{column} 成功 {success_count}/{supplied_count}"
            f"（{success_rate:.1%}），失败 {failed_count}"
        )
        if failed_count:
            samples = list(dict.fromkeys(original_text[failed].tolist()))[:5]
            self.log.append(
                f"日期转换警告：{column} 无法解析的样例 {samples}"
            )
        return self.df

    def derive_column(self, new_col, col_a, op, col_b):
        """派生新列：new_col = col_a (×/+/−/÷) col_b（通用，取代写死的 TotalPrice）

        参数:
            new_col: 新列名（如 "TotalPrice"）
            col_a, col_b: 两个源列名
            op: 运算符，取 * / + / - / /

        源列先 to_numeric(coerce) 再运算。源列不存在或 op 未知 → 记日志并跳过。

        返回值:
            pandas.DataFrame: 增加新列的 df
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")
        miss = [c for c in (col_a, col_b) if c not in self.df.columns]
        if miss:
            self.log.append(f"派生列：源列 {miss} 不存在，跳过")
            return self.df
        if op not in _ARITH_OPS:
            self.log.append(f"派生列：未知运算 '{op}'，跳过")
            return self.df

        self._snapshot()
        a = pd.to_numeric(self.df[col_a], errors="coerce")
        b = pd.to_numeric(self.df[col_b], errors="coerce")
        self.df[new_col] = _ARITH_OPS[op](a, b)
        self.log.append(f"派生列：{new_col} = {col_a} {op} {col_b}")
        return self.df

    # ==================== 高级刀（强表结构假设，与通用工具箱隔离） ====================

    def drop_cancellation_pairs(self, invoice_col="InvoiceNo", customer_col="CustomerID",
                                code_col="StockCode", price_col="UnitPrice",
                                qty_col="Quantity", prefix="C"):
        """删取消订单，以及它们残留的「原始正单」（高级，需多个固定列齐全）

        取消订单 = invoice_col 以 prefix 开头的行。每条取消单对应一条原始正单
        （同客户、同商品编码、同单价，数量正负相反）。本方法用「指纹配对」找出
        并删除这些原始正单，避免虚增销量与金额。

        这是最依赖具体表结构的一刀（要 5 个固定列），故与通用工具箱隔离：
        prefix 为空 → 跳过；任一所需列缺失 → 记日志并跳过（不报错）。

        参数:
            invoice_col/customer_col/code_col/price_col/qty_col: 各角色对应的列名
            prefix: 取消单前缀（默认 "C"）

        返回值:
            pandas.DataFrame: 清洗后的 df
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")

        prefix = (prefix or "").strip()
        if not prefix:
            self.log.append("删取消单配对：未设置取消单前缀，跳过")
            return self.df

        need = [invoice_col, customer_col, code_col, price_col, qty_col]
        miss = [c for c in need if c not in self.df.columns]
        if miss:
            self.log.append(f"删取消单配对：缺列 {miss}，跳过（高级刀需字段齐全）")
            return self.df

        self._snapshot()
        before = len(self.df)
        is_cancel = self.df[invoice_col].astype(str).str.startswith(prefix)
        cancellations = self.df[is_cancel]
        cancel_keys = set(zip(cancellations[customer_col], cancellations[code_col],
                              cancellations[price_col], -cancellations[qty_col]))
        row_keys = zip(self.df[customer_col], self.df[code_col],
                       self.df[price_col], self.df[qty_col])
        is_orig = pd.Series([k in cancel_keys for k in row_keys], index=self.df.index)
        self.df = self.df[~is_cancel & ~is_orig]
        after = len(self.df)
        self.report_change(before, after)
        return self.df
