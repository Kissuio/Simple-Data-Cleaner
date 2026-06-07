"""字段映射逻辑（独立于 GUI 与 FileLoader）：把任意商家表的列，对应到分析所需的标准字段。

方案 B：标准化推迟到「进入分析前」才做——加载、清洗阶段都用原始列名自由操作，
进入 RFM/销售/商品分析时才把列对应到标准字段。本模块提供两个纯函数：
- guess_mapping(columns)        —— 按列名猜每个标准字段对应哪一列（同名/别名/模糊）
- apply_field_mapping(df, m)     —— 按映射生成标准列，并按需派生 TotalPrice

不依赖任何实例状态，便于在「清洗后的 df」上直接调用。
"""

import re

import pandas as pd


# 分析层依赖的标准字段（顺序即映射界面展示顺序）：(标准名, 中文名, 是否必需)
# 软门禁口径：映射时只硬性要求「任何分析都要」的字段（客户/订单号/日期）+ 金额可得；
# 其余字段（数量/单价/商品名/商品编码/国家）标可选——缺了不挡映射，
# 进入用到它的分析页时再精确提示（见 ANALYSIS_REQUIRED）。
# - TotalPrice 可不选：有「数量×单价」时自动派生；金额二者得其一即可（见对话框校验）。
# - Quantity/UnitPrice 可选：只有商品分析与派生 TotalPrice 才用到。
STANDARD_FIELDS = [
    ("CustomerID",  "客户 ID",    True),
    ("InvoiceNo",   "订单号",     True),
    ("InvoiceDate", "交易时间",   True),
    ("Quantity",    "数量",       False),
    ("UnitPrice",   "单价",       False),
    ("Description", "商品名称",   False),
    ("StockCode",   "商品编码",   False),
    ("Country",     "国家 / 地区", False),
    ("TotalPrice",  "销售额",     False),
]

# 标准字段 → 中文名（提示用），从 STANDARD_FIELDS 派生
FIELD_CN = {std: cn for std, cn, _ in STANDARD_FIELDS}

# 标准字段 → 用途标注（映射界面逐字段显示「这列给哪个分析用」，让用户一眼看清
# 做 RFM / 销售 / 商品 各需要映射哪些列，而非只看笼统的必需/可选）。
FIELD_USAGE = {
    "CustomerID":  "RFM 必需 · 分群依据",
    "InvoiceNo":   "RFM / 销售 必需 · 频次与订单数",
    "InvoiceDate": "RFM / 销售 必需 · 时间维度",
    "TotalPrice":  "RFM / 销售 / 商品 金额（缺则按 数量×单价 自动算）",
    "Quantity":    "商品分析销量 · 也用于合成金额",
    "UnitPrice":   "商品分析单价 · 也用于合成金额",
    "Description": "商品分析 · 商品名称",
    "StockCode":   "商品分析 · 商品编码",
    "Country":     "可选 · 仅地域筛选用",
}

# 各分析「真正用到」的标准列（软门禁按此逐页校验）。
# 注意：这里列 TotalPrice 即可——它在 apply_field_mapping 里会由「数量×单价」自动派生，
# 故只要映射了金额或数量+单价，get_active_df 输出就含 TotalPrice。
ANALYSIS_REQUIRED = {
    "rfm":     ["CustomerID", "InvoiceNo", "InvoiceDate", "TotalPrice"],
    "sales":   ["InvoiceNo", "InvoiceDate", "TotalPrice"],
    "product": ["TotalPrice", "Quantity", "UnitPrice", "StockCode"],
    "overview": ["CustomerID", "InvoiceNo", "InvoiceDate", "TotalPrice",
                 "Quantity", "UnitPrice", "StockCode"],
}


def missing_required_fields(columns, kind):
    """给定（映射后）列名与分析类型，返回该分析还缺哪些标准列。"""
    have = set(columns)
    return [c for c in ANALYSIS_REQUIRED.get(kind, []) if c not in have]

# 标准字段 → 常见别名（中英混合），仅用于「自动猜测」给默认值，不强制
COLUMN_ALIASES = {
    "InvoiceNo":  ["Invoice", "订单号", "订单编号", "发票号", "单号", "OrderID", "Order ID", "Order No"],
    "StockCode":  ["Stock Code", "商品编码", "商品编号", "货号", "SKU", "SKU ID", "商品ID", "ProductID", "Product ID", "Item Code"],
    "Description":["Product", "商品名称", "商品名", "品名", "描述", "Product Name", "Item Name"],
    "Quantity":   ["Qty", "数量", "购买数量", "购买数", "销量", "Count"],
    "InvoiceDate":["Order Time", "Order Timestamp", "下单时间", "交易时间", "成交时间",
                   "购买时间", "Datetime", "Timestamp", "Order Date", "OrderDate",
                   "订单日期", "交易日期", "日期", "Date", "Update Time", "Created At"],
    "UnitPrice":  ["Price", "单价", "成交价", "售价", "Unit Price", "Final Unit Price", "Sale Price", "Actual Price"],
    "CustomerID": ["Customer ID", "User ID", "客户ID", "客户编号", "会员ID", "会员编号", "会员卡号", "用户ID", "用户编号", "买家ID", "CustomerNo"],
    "Country":    ["国家", "地区", "国家地区", "Region", "Nation"],
    "TotalPrice": ["销售额", "销售金额", "总价", "总金额", "金额", "成交额", "Sales", "Amount", "Total", "Revenue"],
}


def guess_mapping(columns):
    """为每个标准字段，在给定列名里猜一个最可能的列（同名 > 别名 > 模糊包含）。

    已被占用的实际列不再分给其他字段，避免一列同时映射到多个标准字段。

    参数:
        columns: 可迭代的实际列名（如清洗后 df.columns）
    返回:
        dict[str, str | None]: {标准字段: 猜中的实际列名 or None}
    """
    # 常见导出系统会把同一个字段写成 Order ID、order_ID 或 order-id。
    norm = lambda s: re.sub(r"[\s_-]+", "", str(s).strip().lower())
    cols = list(columns)
    actual_norm = {}
    for col in cols:
        actual_norm.setdefault(norm(col), col)

    targets = [f[0] for f in STANDARD_FIELDS]
    guess = {std: None for std in targets}
    used = set()

    # 同名 / 别名（高置信）
    for std in targets:
        if norm(std) in actual_norm and actual_norm[norm(std)] not in used:
            guess[std] = actual_norm[norm(std)]
            used.add(guess[std])
            continue
        for alias in COLUMN_ALIASES.get(std, []):
            col = actual_norm.get(norm(alias))
            if col is not None and col not in used:
                guess[std] = col
                used.add(col)
                break

    # 模糊包含（兜底，只补还没猜到的）
    for std in targets:
        if guess[std]:
            continue
        for col in cols:
            if col in used:
                continue
            if norm(std) in norm(col) or norm(col) in norm(std):
                guess[std] = col
                used.add(col)
                break

    return guess


def apply_field_mapping(df, mapping):
    """按映射从原始列生成标准列，并按需派生 TotalPrice。

    参数:
        df:      清洗后的 DataFrame（原始列名）
        mapping: {标准字段: 实际列名}；值为空/None 表示该字段不映射

    返回:
        pandas.DataFrame: 应用映射后的新表，不修改传入的 df

    异常:
        ValueError: 原表含重复列名，或同一实际列被映射到多个标准字段

    规则:
        - 每个标准列都从原始 df 取值，用户映射会覆盖原表中已有的同名标准列；
        - 建立标准列后删除不再作为其他映射目标的源列，保持原有“重命名”效果；
        - 映射中不存在的实际列暂时跳过，由分析页的缺失字段检查负责提示；
        - 未映射 TotalPrice 且已有 Quantity + UnitPrice 时，重新派生销售额。
    """
    if not df.columns.is_unique:
        duplicates = list(dict.fromkeys(df.columns[df.columns.duplicated()].tolist()))
        names = "、".join(repr(name) for name in duplicates)
        raise ValueError(f"原始数据含重复列名：{names}，请先重命名后再做字段映射")

    selected = {
        std: col
        for std, col in mapping.items()
        if col and col in df.columns
    }

    source_targets = {}
    for std, col in selected.items():
        source_targets.setdefault(col, []).append(std)
    reused = {
        col: targets
        for col, targets in source_targets.items()
        if len(targets) > 1
    }
    if reused:
        details = "；".join(
            f"{col!r} → {', '.join(targets)}"
            for col, targets in reused.items()
        )
        raise ValueError(f"同一实际列不能映射到多个标准字段：{details}")

    out = df.copy()
    for std, col in selected.items():
        # 始终从原始 df 读取，确保覆盖同名目标列和字段互换时结果稳定。
        out[std] = df[col].copy()

    targets = set(selected)
    removable_sources = [
        col
        for std, col in selected.items()
        if col != std and col not in targets
    ]
    if removable_sources:
        out = out.drop(columns=removable_sources)

    if (
        not mapping.get("TotalPrice")
        and "Quantity" in out.columns
        and "UnitPrice" in out.columns
    ):
        out["TotalPrice"] = (
            pd.to_numeric(out["Quantity"], errors="coerce")
            * pd.to_numeric(out["UnitPrice"], errors="coerce")
        )
    return out
