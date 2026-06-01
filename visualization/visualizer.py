from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
class Visualizer:
    """图表绘制器（纯画图类，不继承数据处理父类）

    接收已聚合好的数据，用 matplotlib / seaborn 画图、存为 PNG 并返回路径。
    本身不做业务聚合——大表的聚合放在 sales_trend.py / product_analysis.py，
    Visualizer 只负责"拿到结果数据 → 画 → 存图"。

    8 个画图方法（对应项目 8 张图表）:
        plot_label_pie()             —— 8 类客户占比饼图
        plot_label_avg_spend()       —— 各类客户人均消费柱图
        plot_rfm_scatter()           —— RFM 客户分布气泡图
        plot_monthly_trend()         —— 月度销售趋势折线图
        plot_top_quantity()          —— TOP10 销量横向柱图
        plot_top_revenue()           —— TOP10 销售额横向柱图
        plot_price_distribution()    —— 成交单价分布直方图（对数刻度）
        plot_weekday_hour_heatmap()  —— 星期 × 小时订单数热力图

    属性:
        output_dir (str): 图表 PNG 的保存目录，默认 "output"
    """

    def __init__(self, output_dir="output"):
        """
        可视化类的初始化，  
        output_dir 为图表 PNG 的保存目录，  
        并设置 matplotlib 中文字体。
        """

        # 用 Path 包装目录，并确保它存在（不存在就连父级一起创建，已存在不报错）
        # 否则换机器/清空仓库后首次 savefig 会因目录缺失抛 FileNotFoundError
        self.output_dir=Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

    def plot_label_pie(self,rfm):
        """画出8类客户的占比饼图,  
        参数rfm为带Label列的RFM表,  
        返回保存png路径
        """

        counts=rfm["Label"].value_counts()
        plt.figure(figsize=(8,8))
        plt.pie(counts,labels=counts.index,autopct="%1.1f%%")
        plt.title("客户8大分类占比")
        path=self.output_dir / "label_pie.png"
        plt.savefig(path)
        plt.close()
        return str(path)
    
    def plot_label_avg_spend(self,rfm):
        """画出8类客户的消费柱状图,    
        参数rfm为带Label列的RFM表,  
        返回保存png路径
        """

        avg=rfm.groupby("Label")["Monetary"].mean().sort_values(ascending=False)
        plt.figure(figsize=(10,8))
        plt.bar(avg.index,avg)
        plt.title("各类客户人均消费金额")
        plt.ylabel("人均消费金额")
        plt.xticks(rotation=30)
        plt.tight_layout()
        path=self.output_dir / "label_avg_spend.png"
        plt.savefig(path)
        plt.close()
        return str(path)
    
    def plot_rfm_scatter(self, rfm):
        """RFM 气泡图，   
        x=Recency、y=Frequency（对数刻度）,  
        点大小=Monetary 取对数,  
        颜色区分 8 类客户,   
        返回 PNG 路径。
        """

        plt.figure(figsize=(11,7))
        for label,group in rfm.groupby("Label"):
            size=np.log10(group["Monetary"]+1)*20
            plt.scatter(group["Recency"],group["Frequency"],s=size,label=label,alpha=0.5)
        plt.yscale("log")
        plt.xlabel("Recency（最近消费距今天数）")
        plt.ylabel("Frequency（消费频次，对数刻度）")
        plt.title("RFM 客户分布气泡图（点越大，消费金额越高）")
        plt.legend()
        path = self.output_dir / "rfm_scatter.png"
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)
    
    def plot_monthly_trend(self, monthly):
        """月销售额折线图,  
        x=月份, y=销售总额,  
        返回 PNG 路径
        """

        monthly=monthly.iloc[:-1]
        plt.figure(figsize=(10,6))
        plt.plot(monthly.index,monthly,marker="o")
        plt.title("月度销售趋势")
        plt.xlabel("月份")
        plt.ylabel("销售总额")
        plt.xticks(rotation=45)
        plt.tight_layout()
        path = self.output_dir / "monthly_trend.png"
        plt.savefig(path)
        plt.close()
        return str(path)

    def plot_top_quantity(self, top_quantity):
        """TOP10 销量横向柱状图,
        参数 top_quantity 为 get_top_quantity(df) 返回的 Series（商品名→销量，降序）,
        返回 PNG 路径
        """

        # 反转：原 Series 是降序，barh 默认从下往上画，反转后最大值落在顶端
        top_quantity = top_quantity.iloc[::-1]
        plt.figure(figsize=(10,7))
        bars = plt.barh(top_quantity.index, top_quantity)
        plt.bar_label(bars, padding=3)
        plt.title("TOP10 热销商品（按销量）")
        plt.xlabel("销量")
        path = self.output_dir / "top_quantity.png"
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)
    
    def plot_price_distribution(self, prices):
        """成交单价分布直方图（x 轴对数刻度），
        参数 prices 为 get_price_distribution(df) 返回的单价 Series,
        返回 PNG 路径
        """
        prices = prices[prices > 0]
        bins = np.logspace(np.log10(prices.min()), np.log10(prices.max()), 50)
        plt.figure(figsize=(10, 6))
        plt.hist(prices, bins=bins)
        plt.xscale("log")
        plt.title("成交单价分布（对数刻度）")
        plt.xlabel("单价（英镑，对数刻度）")
        plt.ylabel("成交笔数")
        path = self.output_dir / "price_distribution.png"
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_weekday_hour_heatmap(self, pivot):
        """订单数热力图（星期 × 小时），
        参数 pivot 为 get_weekday_hour_orders(df) 返回的 7×24 DataFrame,
        返回 PNG 路径
        """
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        plt.figure(figsize=(12, 5))
        sns.heatmap(pivot, cmap="YlOrRd", annot=True, fmt=".0f", yticklabels=weekday_names)
        plt.title("订单数热力图（星期 × 小时）")
        plt.xlabel("小时")
        plt.ylabel("星期")
        path = self.output_dir / "weekday_hour_heatmap.png"
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_top_revenue(self,top_revenue):
        """TOP10 销售额横向柱状图,
        参数 top_revenue 为 get_top_revenue(df) 返回的 Series（商品名→销售额，降序）,
        返回 PNG 路径
        """
        top_revenue=top_revenue.iloc[::-1]
        plt.figure(figsize=(10,7))
        bars=plt.barh(top_revenue.index,top_revenue)
        plt.bar_label(bars,padding=3)
        plt.title("TOP10 热销商品（按销售额）")
        plt.xlabel("销售额")
        path = self.output_dir / "top_revenue.png"
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)












