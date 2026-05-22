def get_monthly_sales(df):
    """按月汇总销售总额；  
    参数 df 为清洗后的 DataFrame（含 InvoiceDate、TotalPrice 列）；  
    返回月份→销售额的 Series。
    """

    month=df["InvoiceDate"].dt.strftime("%Y-%m")
    monthly= df.groupby(month)["TotalPrice"].sum()
    return monthly