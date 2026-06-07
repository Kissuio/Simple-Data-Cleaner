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


def get_month_orders(df):
    """按"年 × 月"统计独立订单数（看不同年份的月份分布对比）；
    参数 df 为清洗后的 DataFrame（含 InvoiceDate、InvoiceNo 列）；
    返回 DataFrame：行=年、列=月(1-12)、值=该年该月独立订单数。

    既能横向看每年的季节性，又能纵向对比「不同年份的同一个月」（如逐年同月增长）——
    这是月度趋势(连续折线)不直观的角度，跨年同月得跳着看。
    只需「年、月」即可，故对只精确到「年月」的数据（如用户购买记录）同样有效。
    """

    year = df["InvoiceDate"].dt.year
    month = df["InvoiceDate"].dt.month
    pivot = df.groupby([year, month])["InvoiceNo"].nunique().unstack()
    # 补全 12 个月的列（缺失补 0），年份行用数据实际存在的年
    pivot = pivot.reindex(columns=range(1, 13)).fillna(0)
    return pivot