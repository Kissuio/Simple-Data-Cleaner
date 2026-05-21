from data_handlers.base_data_handler import BaseDataHandler
import pandas as pd
class RFMAnalyzer(BaseDataHandler):
    def __init__(self,df):
        """初始化,  
        与BaseDataHandler有共同成分满足继承条件,  
        提供DataFrame进行只读操作,提供rfm方法端口
        """
        super().__init__()
        self.df=df     #只读属性
        self.rfm=None
    
    def calc_rfm(self):
        """计算每个客户的 R、F、M 三个原始值

        R Recency   —— 最近一次消费距截止日的天数(越小越活跃)  
        F Frequency —— 消费频次，不重复订单数  
        M Monetary  —— 消费总金额

        截止日取数据集最后一笔交易日期 + 1 天。

        返回值:
            pandas.DataFrame: 每行一个客户(CustomerID 为索引)，    
            含 Recency / Frequency / Monetary 三列
        """

        if not self.validate():
            raise ValueError("数据未加载或为空，无法分析")
        #以InvoiceDate中最后一次购买日期+1天作为截止日，使R的值>=1
        snapshot_date=self.df["InvoiceDate"].max()+pd.Timedelta(days=1)
        rfm=self.df.groupby("CustomerID").agg(
            last_purchase=("InvoiceDate","max"),
            Frequency=("InvoiceNo","nunique"),
            Monetary=("TotalPrice","sum"),         
         )
        rfm["Recency"]=(snapshot_date-rfm["last_purchase"]).dt.days
        self.rfm=rfm[["Recency","Frequency","Monetary"]]
        return self.rfm
        
       

    