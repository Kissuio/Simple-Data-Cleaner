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

def get_top_revenue(df,n=10):
    """按销售额取 TOP n 商品；
    参数 df 为清洗后的 DataFrame（需含 StockCode、Description、TotalPrice 列）；
    参数 n 为取前几名，默认 10；
    返回一个 Series：商品名 → 销售额总和，按销售额降序排列。
    """
     
    top=df.groupby("StockCode")["TotalPrice"].sum().sort_values(ascending=False).head(n)
    top_rows=df[df["StockCode"].isin(top.index)]
    name_map=top_rows.groupby("StockCode")["Description"].agg(lambda s:s.mode().iloc[0])
    top.index=top.index.map(name_map)
    return top

def get_price_distribution(df):
    """返回所有成交记录的单价 Series，供单价分布直方图用
    """
    # 单价直接取一列即可；仍单独成函数，是为了和其他分析函数统一接口
    # —— Visualizer 只管理画图、统一通过分析函数取数，不直接取原始 df
    return df["UnitPrice"]