def _use_product_labels(top, df):
    """有商品名称时显示名称，否则以匿名商品编码作为排行标签。"""
    if "Description" not in df.columns:
        top.index = top.index.map(str)
        return top

    top_rows = df[df["StockCode"].isin(top.index)]
    labels = {}
    for code, values in top_rows.groupby("StockCode")["Description"]:
        values = values.dropna().astype(str).str.strip()
        values = values[values != ""]
        labels[code] = values.mode().iloc[0] if len(values) else str(code)
    top.index = [labels.get(code, str(code)) for code in top.index]
    return top


def get_top_quantity(df, n=10):
    """按销量取 TOP n 商品。

    需要 StockCode、Quantity；有 Description 时显示商品名，否则显示匿名编码。
    """
    top = (
        df.groupby("StockCode")["Quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
    )
    return _use_product_labels(top, df)


def get_top_revenue(df, n=10):
    """按销售额取 TOP n 商品。

    需要 StockCode、TotalPrice；有 Description 时显示商品名，否则显示匿名编码。
    """
    top = (
        df.groupby("StockCode")["TotalPrice"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
    )
    return _use_product_labels(top, df)


def get_price_distribution(df):
    """返回所有成交记录的单价 Series，供单价分布直方图使用。"""
    return df["UnitPrice"]
