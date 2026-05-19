from data_handlers.base_data_handler import BaseDataHandler
import pandas as pd
class FileLoader(BaseDataHandler):
    def __init__(self,file_path):
        super().__init__()
        self.file_path=file_path
        self.required_columns=[
          'InvoiceNo',
          'StockCode',
          'Description',
          'Quantity',
          'InvoiceDate',
          'UnitPrice',
          'CustomerID']
        self.optional_columns=['Country']


    def load_file(self):
        """读取文件，把数据存到 self.df 中，同时记录日志""" 

        if self.file_path.endswith(".xlsx"):
            self.df=pd.read_excel(self.file_path)
            msg=f"文件加载成功:{len(self.df)}行，格式为: '.xlsx' "
            self.log.append(msg)
        elif self.file_path.endswith(".csv"):
            self.df=pd.read_csv(self.file_path)
            msg=f"文件加载成功:{len(self.df)}行，格式为: '.csv' "
            self.log.append(msg)
        else:
            raise ValueError("不支持的文件格式，请上传 .xlsx 或 .csv")
        return self.df


    def check_columns(self):
        """检查 self.df 是否包含所需字段

        必需字段缺失：抛出 ValueError，分析无法进行
        
        可选字段缺失：只写日志，不报错（功能降级）

        返回值:
            bool: 全部必需字段存在时返回 True
        """
        # 必须先 load_file 才能检查列名，正好用上父类的 validate
        if not self.validate():
            raise ValueError("数据未加载或为空，请先调用 load_file()")

        # 当前 DataFrame 实际有哪些列
        actual_columns = self.df.columns.tolist()

        # 找出"在 required 里但不在 actual 里"的字段——即缺失的必需字段
        missing_required = [col for col in self.required_columns if col not in actual_columns]

        # 必需字段缺了直接中断，调用方必须处理
        if missing_required:
            msg = f"缺少必需字段:{missing_required}"
            self.log.append(msg)
            raise ValueError(msg)

        # 同样的方式找缺失的可选字段
        missing_optional = [col for col in self.optional_columns if col not in actual_columns]

        # 可选字段缺了只记日志，不报错
        if missing_optional:
            self.log.append(f"缺少可选字段:{missing_optional}，地域维度分析将不可用")
        else: 
            self.log.append(
                f"字段检查通过:必需字段{len(self.required_columns)}个、可选字段{len(self.optional_columns)}个全部存在"
            )

        return True
