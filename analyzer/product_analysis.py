def get_top_quantity(df,n=10):
    """按销量取 TOP n 商品；
    参数 df 为清洗后的 DataFrame（需含 StockCode、Description、Quantity 列）；
    参数 n 为取前几名，默认 10；
    返回一个 Series：商品名 → 销量总和，按销量降序排列。
    """

    top=df.groupby("StockCode")["Quantity"].sum().sort_values(ascending=False).head(n)
    top_rows=df[df["StockCode"].isin(top.index)]
    name_map=top_rows.groupby("StockCode")["Description"].agg(lambda s:s.mode().iloc[0])
    top.index=top.index.map(name_map)
    return top
