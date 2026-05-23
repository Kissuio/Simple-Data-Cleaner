def get_monthly_sales(df):
    """按月汇总销售总额；
    参数 df 为清洗后的 DataFrame（含 InvoiceDate、TotalPrice 列）；
    返回月份→销售额的 Series。
    """

    month=df["InvoiceDate"].dt.strftime("%Y-%m")
    monthly= df.groupby(month)["TotalPrice"].sum()
    return monthly


def get_weekday_hour_orders(df):
    """按"星期几 × 小时"统计独立订单数；
    参数 df 为清洗后的 DataFrame（含 InvoiceDate、InvoiceNo 列）；
    返回 7×24 的 DataFrame：行=星期几(0-6, 0=周一)、列=小时(0-23)、值=该时段独立订单数。
    """

    weekday = df["InvoiceDate"].dt.dayofweek
    hour = df["InvoiceDate"].dt.hour
    pivot = df.groupby([weekday, hour])["InvoiceNo"].nunique().unstack()
    # 强制补全 7×24：reindex 补缺失的整行/整列、fillna 兜底剩余零星 NaN
    pivot = pivot.reindex(index=range(7), columns=range(24), fill_value=0).fillna(0)
    return pivot