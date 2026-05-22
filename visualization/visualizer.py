import matplotlib.pyplot as plt
import numpy as np
class Visualizer:
    def __init__(self, output_dir="output"):
        """
        可视化类的初始化，  
        output_dir 为图表 PNG 的保存目录，  
        并设置 matplotlib 中文字体。
        """

        self.output_dir=output_dir
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
        path=f"{self.output_dir}/label_pie.png"
        plt.savefig(path)
        plt.close()
        return path
    
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
        path=f"{self.output_dir}/label_avg_spend.png"
        plt.savefig(path)
        plt.close()
        return path
    
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
        path = f"{self.output_dir}/rfm_scatter.png"
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return path







