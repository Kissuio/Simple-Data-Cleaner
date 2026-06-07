"""图表洞察文案的动态生成（从聚合数据现算事实，替代写死的固定解读）。

为什么要这个模块：
- 原来各页的 INSIGHTS 是写死的（"11 月￡1,150,000 对应圣诞季""销量冠军 WORLD WAR 2
  GLIDERS"…），只对 Online Retail 成立，换数据集就全错；
- 这里每个函数接收对应图表的聚合数据，现算关键事实（峰值、占比、TOP 等）套中文模板，
  换任何数据都能给出针对性的"数据事实型"洞察。

边界：只给数据事实（"订单最高在 11 月"），不给业务背景解读（"因为圣诞季"）——
后者因商家而异、无法通用，交给「AI 解读」窗口按图说背景。
"""


def monthly_trend_insight(monthly):
    """月度销售趋势洞察。monthly: Series(index=年月字符串, value=销售额)。"""
    if monthly is None or len(monthly) == 0:
        return "• 暂无月度销售数据"
    peak, peak_v = monthly.idxmax(), monthly.max()
    low, low_v = monthly.idxmin(), monthly.min()
    if monthly.iloc[-1] > monthly.iloc[0]:
        trend = "上升"
    elif monthly.iloc[-1] < monthly.iloc[0]:
        trend = "下降"
    else:
        trend = "基本持平"
    return (
        f"• 覆盖 {monthly.index[0]} ~ {monthly.index[-1]}，共 {len(monthly)} 个月\n"
        f"• 销售额最高：{peak}（约 {peak_v:,.0f}）\n"
        f"• 销售额最低：{low}（约 {low_v:,.0f}）\n"
        f"• 首尾对比整体呈{trend}趋势"
    )


def weekday_hour_insight(pivot):
    """周热力图洞察。pivot: 7×24 DataFrame(行=星期0-6, 列=小时)。"""
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    if pivot is None or pivot.values.sum() == 0:
        return "• 暂无时段数据（数据可能不含小时信息）"
    flat = pivot.stack()
    (wd, hr), peak_v = flat.idxmax(), flat.max()
    active = int((pivot > 0).sum().sum())
    note = ""
    if active <= 1:
        note = "\n• 所有订单挤在同一时段——该数据不含精确到小时的时间，本图参考意义有限"
    return (
        f"• 订单最集中：{weekday_names[int(wd)]} {int(hr)} 点（{peak_v:.0f} 单）\n"
        f"• 共 {active} 个「星期×小时」时段有订单\n"
        f"• 用订单数而非销售额，避免大额订单干扰时段判断{note}"
    )


def month_insight(pivot):
    """各年各月分布洞察。pivot: 年×12 DataFrame。"""
    if pivot is None or pivot.values.sum() == 0:
        return "• 暂无月份分布数据"
    years = [int(y) for y in pivot.index]
    month_total = pivot.sum(axis=0)
    peak_m, peak_v = int(month_total.idxmax()), month_total.max()
    low_m, low_v = int(month_total.idxmin()), month_total.min()
    return (
        f"• 覆盖 {years[0]} ~ {years[-1]} 共 {len(years)} 年\n"
        f"• 旺季月份：{peak_m} 月（各年合计 {peak_v:.0f} 单）\n"
        f"• 淡季月份：{low_m} 月（{low_v:.0f} 单）\n"
        f"• 颜色按每年归一化，纵向可比不同年份同一月的相对高低"
    )


def top_quantity_insight(top):
    """TOP 销量榜洞察。top: Series(商品名→销量, 降序)。"""
    if top is None or len(top) == 0:
        return "• 暂无商品销量数据"
    return (
        f"• 销量冠军：{top.index[0]}（{top.iloc[0]:,.0f} 件）\n"
        f"• 榜单共 {len(top)} 款，合计 {top.sum():,.0f} 件\n"
        f"• 高销量商品适合做引流款、组合销售，并关注库存周转避免断货"
    )


def top_revenue_insight(top):
    """TOP 销售额榜洞察。top: Series(商品名→销售额, 降序)。"""
    if top is None or len(top) == 0:
        return "• 暂无商品销售额数据"
    return (
        f"• 销售额冠军：{top.index[0]}（约 {top.iloc[0]:,.0f}）\n"
        f"• 榜单共 {len(top)} 款，合计约 {top.sum():,.0f}\n"
        f"• 高销售额商品适合关联推荐、节日陈列和复购运营"
    )


def price_distribution_insight(prices):
    """单价分布洞察。prices: Series(成交单价)。"""
    if prices is None:
        return "• 暂无单价数据"
    prices = prices[prices > 0]
    if len(prices) == 0:
        return "• 暂无有效单价数据"
    med = prices.median()
    q1, q3 = prices.quantile(0.25), prices.quantile(0.75)
    return (
        f"• 单价中位数约 {med:,.2f}\n"
        f"• 中间 50% 的商品单价在 {q1:,.2f} ~ {q3:,.2f}\n"
        f"• 多数集中在低价带、少数高价长尾（分布右偏）"
    )
