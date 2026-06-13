from data_handlers.base_data_handler import BaseDataHandler
import pandas as pd
import re
class FileLoader(BaseDataHandler):
    """保留原始列名的 CSV/XLSX 电商数据加载器。

    只负责从本地读取 .xlsx 或 .csv 数据，并保留原始列名。字段标准化
    （自动匹配 + 用户确认 + 应用映射）已统一移到 data_handlers/field_mapping.py
    的纯函数与分析入口的软门禁，FileLoader 不再承担映射或字段校验，避免
    同一套逻辑两处维护、也避免自定义商家字段被静默改错。

    属性:
        file_path (str): 待加载文件的路径
        df (pandas.DataFrame): 读入的原始数据（继承自 BaseDataHandler）
        log (list[str]): 操作日志（继承自 BaseDataHandler）

    主要方法:
        load_file()          —— 读取文件并保留原始列名
    """

    def __init__(self,file_path):
        """接收文件路径，初始化加载器。

        参数:
            file_path (str): 待加载的 .xlsx 或 .csv 文件路径
        """
        super().__init__()
        self.file_path=file_path

    def load_file(self):
        """读取 CSV/XLSX，保留原始列名。

        返回:
            pandas.DataFrame: 文件中的原始数据

        异常:
            ValueError: 文件扩展名不是 .csv 或 .xlsx
            FileNotFoundError: 文件路径不存在
        """
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
                self.df=self._read_csv_any_encoding(self.file_path)
                msg=f"文件加载成功:{len(self.df)}行，格式为: '.csv' "
                self.log.append(msg)
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在，请检查路径：{self.file_path}")
        # 读进来不动列名：列名由后续「字段映射」环节（field_mapping.guess_mapping 给建议 +
        # 用户在映射对话框确认 + apply_field_mapping 执行）统一处理，让每一次列名变更
        # 都可见、可控，而不是加载时按写死别名悄悄改名——这正是「支持不同商家自定义列名」的关键。
        return self.df

    def _read_csv_any_encoding(self, path):
        """按常见编码依次尝试读取 CSV，兼容不同商家导出的非 utf-8 文件

        真实商家文件常不是 utf-8：中文 Excel 多为 gbk，西文系统多为 latin-1。
        尝试顺序：
            utf-8-sig —— 标准 utf-8（顺带去掉可能的 BOM）
            gbk       —— 中文 Windows / Excel 导出
            latin-1   —— 西文兜底（单字节编码，几乎不会解码失败）

        返回值:
            pandas.DataFrame: 成功读取的数据
        """
        encodings = ["utf-8-sig", "gbk", "latin-1"]
        last_error = None
        for enc in encodings:
            try:
                df = pd.read_csv(path, encoding=enc)
                if enc != "utf-8-sig":
                    self.log.append(f"utf-8 读取失败，已自动以 {enc} 编码读取")
                return df
            except (UnicodeDecodeError, UnicodeError) as e:
                last_error = e
                continue
        # 理论上 latin-1 不会走到这；兜底抛出最后一次错误
        raise last_error
