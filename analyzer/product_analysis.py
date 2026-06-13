def get_product_key(df):
    """返回商品分析使用的分组键（商品编码或名称，有一个即可）。

    优先用商品编码 StockCode（更精确，同名不同款不会被合并）；表里没有编码时，
    退用商品名称 Description 作分组键，让无 SKU 的商家表也能做商品分析。
    """
    if "StockCode" in df.columns:
        return "StockCode"
    if "Description" in df.columns:
        return "Description"
    raise KeyError("商品分析需要 StockCode（商品编码）或 Description（商品名称）至少一个字段。")


def get_product_count(df):
    """返回不同商品数量，商品编码或商品名称有一个即可。"""
    return int(df[get_product_key(df)].nunique())


def _use_product_labels(top, df, key):
    """把分组键的取值换成可读标签。

    - 按编码分组且有商品名：用每个编码出现最多的商品名当标签；
    - 按商品名分组（无编码），或无商品名：标签即分组键本身。
    """
    if key == "StockCode" and "Description" in df.columns:
        top_rows = df[df["StockCode"].isin(top.index)]
        labels = {}
        for code, values in top_rows.groupby("StockCode")["Description"]:
            values = values.dropna().astype(str).str.strip()
            values = values[values != ""]
            labels[code] = values.mode().iloc[0] if len(values) else str(code)
        top.index = [labels.get(code, str(code)) for code in top.index]
    else:
        top.index = top.index.map(str)
    return top


def get_top_quantity(df, n=10):
    """按销量取 TOP n 商品。

    分组键为商品编码或商品名称（二者有一即可）；有商品名时榜单显示商品名。
    """
    key = get_product_key(df)
    top = (
        df.groupby(key)["Quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
    )
    return _use_product_labels(top, df, key)


def get_top_revenue(df, n=10):
    """按销售额取 TOP n 商品。

    分组键为商品编码或商品名称（二者有一即可）；有商品名时榜单显示商品名。
    """
    key = get_product_key(df)
    top = (
        df.groupby(key)["TotalPrice"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
    )
    return _use_product_labels(top, df, key)


def get_price_distribution(df):
    """返回所有成交记录的单价 Series，供单价分布直方图使用。"""
    return df["UnitPrice"]
