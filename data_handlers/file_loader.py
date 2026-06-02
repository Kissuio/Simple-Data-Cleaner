from data_handlers.base_data_handler import BaseDataHandler
import pandas as pd
import re 
class FileLoader(BaseDataHandler):
    """电商数据文件加载器，继承 BaseDataHandler

    负责从本地读取 .xlsx 或 .csv 数据，并在加载后自动对列名做归一化处理，
    以兼容不同版本数据集的列名差异（如 Online Retail 与 Online Retail II
    中 "InvoiceNo"/"Invoice"、"CustomerID"/"Customer ID"、
    "UnitPrice"/"Price" 等）。

    属性:
        file_path (str): 待加载文件的路径
        required_columns (list[str]): 必需字段列表（缺失抛错）
        optional_columns (list[str]): 可选字段列表（缺失只记日志）
        column_aliases (dict[str, list[str]]): 标准列名 → 别名列表

    主要方法:
        load_file()          —— 读取文件 + 列名归一化
        check_columns()      —— 校验必需/可选字段是否齐全
        _normalize_columns() —— 私有方法，基于别名字典统一列名
    """
    
    def __init__(self,file_path):
        """接收文件路径，初始化加载器并设定字段规则

        参数:
            file_path (str): 待加载的 .xlsx 或 .csv 文件路径

        初始化的属性:
            required_columns: 必需字段列表，缺失会在 check_columns 抛错
            optional_columns: 可选字段列表，缺失只记日志（功能降级）
            column_aliases:   标准列名 → 别名列表，供 _normalize_columns 归一化
        """
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
        self.column_aliases = {
          "InvoiceNo":  ["Invoice"],
          "UnitPrice":  ["Price"],
          "CustomerID": ["Customer ID"],
        }

    def load_file(self):
        """读取文件并归一化列名，存到 self.df 中，同时记录日志  
           详细列名归一化规则见 _normalize_columns 方法""" 
        #正则
        if not re.search(r"\.(csv|xlsx)$",self.file_path,re.IGNORECASE):
            raise ValueError("不支持的文件格式，请上传 .xlsx 或 .csv")

        # try/except 接住运行时错误：文件不存在时 pd.read_xxx 会抛 FileNotFoundError，
        # 这里接住后改抛一条清楚的中文提示，便于定位（GUI 的 except Exception 会把它显示在弹窗里）
        try:
            if self.file_path.lower().endswith(".xlsx"):
                self.df=pd.read_excel(self.file_path)
                msg=f"文件加载成功:{len(self.df)}行，格式为: '.xlsx' "
                self.log.append(msg)
            elif self.file_path.lower().endswith(".csv"):
                self.df=pd.read_csv(self.file_path)
                msg=f"文件加载成功:{len(self.df)}行，格式为: '.csv' "
                self.log.append(msg)
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在，请检查路径：{self.file_path}")
        self._normalize_columns()
        return self.df
    
    def _normalize_columns(self):
        """对于名称缺失部分或字符串中间含空格的列标题,  
        保证一定程度上的名称兼容，  
        避免大小写及首尾空格的影响
        """

        alias_to_std={}
        
        for k,v in self.column_aliases.items():
            for alias in v:
                alias_to_std[alias.strip().lower()]=k
        
        rename_map={}
        
        for actual_col in self.df.columns:
            key=actual_col.strip().lower()
            if key in alias_to_std:
                std_col=alias_to_std[key]
                if actual_col!=std_col:#避免自身的加入导致日志显示加入自身
                    rename_map[actual_col]=std_col

        if rename_map:
            self.df.rename(columns=rename_map,inplace=True)
            self.log.append(f"列名归一化:{rename_map}")
                
            

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
            attempted_aliases={}
            for col in missing_required:
                attempted_aliases[col]=self.column_aliases.get(col,[])
            msg = f"缺少必需字段(字段名→已尝试别名):{attempted_aliases}"
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
