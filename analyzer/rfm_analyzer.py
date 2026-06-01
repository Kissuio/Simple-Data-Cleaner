from data_handlers.base_data_handler import BaseDataHandler
import pandas as pd
class RFMAnalyzer(BaseDataHandler):
    """RFM 客户价值分析器，继承 BaseDataHandler

    接收清洗后的交易数据，按 RFM 模型计算每个客户的 Recency / Frequency /
    Monetary 三维指标，按均值打分（高/低），再组合成 8 类标准客户标签。
    每个方法可单独调用便于调试，也可通过 analyze_all() 按标准顺序一次执行。

    分析方法（按 analyze_all 标准顺序）:
        1. calc_rfm()       —— 计算 R/F/M 三个原始值
        2. score_rfm()      —— 按各维度均值打 高/低 分（1/0）
        3. label_customer() —— 按打分组合贴 8 类客户标签（Label 列）

    属性:
        df (pandas.DataFrame): 传入的清洗后数据（只读，不修改）
        rfm (pandas.DataFrame | None): 分析结果表；调用 calc_rfm() 后才有值
    """

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
        
    def score_rfm(self):
        """根据均值给 R/F/M 打分（1=高/好，0=低/差）

        R 越小越好：Recency 低于均值记 1
        F、M 越大越好：高于均值记 1

        返回值:
            pandas.DataFrame: 在 self.rfm 上新增 R_score/F_score/M_score 三列
        """

        if self.rfm is None:
            raise ValueError("请先调用 calc_rfm() 生成 RFM 表")
        
        r_mean = self.rfm["Recency"].mean()
        f_mean = self.rfm["Frequency"].mean()
        m_mean = self.rfm["Monetary"].mean()

        self.rfm["R_score"]=(self.rfm["Recency"]<r_mean).astype(int)
        self.rfm["F_score"] = (self.rfm["Frequency"] > f_mean).astype(int)
        self.rfm["M_score"] = (self.rfm["Monetary"] > m_mean).astype(int)

        return self.rfm
    
    def label_customer(self):
        """根据 R/F/M 三维打分组合，给每个客户贴 8 类标签

        把 R_score/F_score/M_score 拼成 "RFM" 三位 key（如 "111"），
        查 label_map 字典得到对应客户类型。

        返回值:
            pandas.DataFrame: 在 self.rfm 上新增 Label 列
        """
        if self.rfm is None or "R_score" not in self.rfm.columns:
            raise ValueError("请先调用 calc_rfm() 和 score_rfm()")

        label_map = {
            "111": "重要价值客户",
            "011": "重要保持客户",
            "101": "重要发展客户",
            "001": "重要挽留客户",
            "110": "一般价值客户",
            "010": "一般保持客户",
            "100": "一般发展客户",
            "000": "一般挽留客户",
        }

        key=(self.rfm["R_score"].astype(str)
            +self.rfm["F_score"].astype(str)
            +self.rfm["M_score"].astype(str))
        self.rfm["Label"]=key.map(label_map)
        return self.rfm

    def analyze_all(self):
        """按标准顺序执行完整 RFM 分析流程

        执行顺序:
            1. calc_rfm()       —— 计算 R/F/M 三个原始值
            2. score_rfm()      —— 按均值打 高/低 分(1/0)
            3. label_customer() —— 生成 8 类客户标签

        返回值:
            pandas.DataFrame: 完成全部分析的客户 RFM 表
        """
        self.calc_rfm()
        self.score_rfm()
        self.label_customer()
        self.log.append("=== RFM 分析全部完成 ===")
        return self.rfm

       

    