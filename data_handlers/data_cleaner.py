import pandas as pd
from data_handlers.base_data_handler import BaseDataHandler

class DataCleaner(BaseDataHandler):
    def __init__(self,df):
        """
        接收一个已加载的 DataFrame，初始化清洗器
        """
        super().__init__()
        self.df=df.copy()  #!!避免指向同一块内存，导致原DATAFRAME被修改!!
    
    
    def drop_missing_customer_id(self):
        """删除 CustomerID 字段为 NaN 的行

        返回值:
           pandas.DataFrame: 清洗后的 df
        """    

        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")
        
        before=len(self.df)
        self.df=self.df.dropna(subset=["CustomerID"])#dropna 去除NAN的值
        after=len(self.df)
        self.report_change(before,after)
        return self.df
    

    def drop_cancellations(self):
        """删除取消订单(InvoiceNo 以 'C' 开头的行)

        返回值:
           pandas.DataFrame: 清洗后的 df
        """

        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")
        
        before=len(self.df)
        is_cancellation=self.df["InvoiceNo"].astype(str).str.startswith("C")
        self.df=self.df[~is_cancellation]
        after=len(self.df)
        self.report_change(before,after)
        return self.df
    

    def convert_date(self):
        """把 InvoiceDate 字段从字符串转为 datetime 类型

         返回值:
            pandas.DataFrame: 转换后的 df
        """
    
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")
        
        self.df["InvoiceDate"]=pd.to_datetime(self.df["InvoiceDate"])
        self.log.append("已将该文档时间全部转换为 datetime64 类型")
        return self.df
  

    def add_total_price(self):
        """将Quantity与UnitPrice相乘得到总价列TotalPrice

        返回值:
           pandas.DataFrame: 增加TotalPrice的  df  
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，无法清洗数据")
        TotalPrice=self.df["Quantity"]*self.df["UnitPrice"]
        self.df["TotalPrice"]=TotalPrice
        self.log.append("新增TotalPrice列(Quantity × UnitPrice)")
        return self.df


    def clean_all(self):
        """按标准顺序执行全部 4 个清洗步骤

        执行顺序:
            1. drop_missing_customer_id() —— 删除 CustomerID 缺失行
            2. drop_cancellations()       —— 删除取消订单
            3. convert_date()             —— 时间字段转 datetime
            4. add_total_price()          —— 新增 TotalPrice 列

        返回值:
            pandas.DataFrame: 完成全部清洗的 df
        """
        self.drop_missing_customer_id()
        self.drop_cancellations()
        self.convert_date()
        self.add_total_price()
        self.log.append("=== 全部清洗步骤完成 ===")
        return self.df
