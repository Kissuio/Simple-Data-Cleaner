from data_handlers.base_data_handler import BaseDataHandler
import pandas as pd
import re 
class FileLoader(BaseDataHandler):
    """保留原始列名的 CSV/XLSX 电商数据加载器。

    负责从本地读取 .xlsx 或 .csv 数据。加载阶段不修改列名；字段标准化
    延后到分析前，由自动猜测和用户确认共同决定，避免自定义商家字段被
    静默改错。类中保留 `guess_mapping`、`apply_mapping` 和 `check_columns`
    供非 GUI 调用方使用。

    属性:
        file_path (str): 待加载文件的路径
        required_columns (list[str]): 必需字段列表（缺失抛错）
        optional_columns (list[str]): 可选字段列表（缺失只记日志）
        column_aliases (dict[str, list[str]]): 标准列名 → 别名列表

    主要方法:
        load_file()          —— 读取文件并保留原始列名
        check_columns()      —— 校验必需/可选字段是否齐全
        guess_mapping()      —— 根据标准名与别名猜测字段对应关系
        apply_mapping()      —— 显式应用调用方确认的字段映射
    """
    
    def __init__(self,file_path):
        """接收文件路径，初始化加载器并设定字段规则

        参数:
            file_path (str): 待加载的 .xlsx 或 .csv 文件路径

        初始化的属性:
            required_columns: 必需字段列表，缺失会在 check_columns 抛错
            optional_columns: 可选字段列表，缺失只记日志（功能降级）
            column_aliases:   标准列名 → 别名列表，仅供自动猜测映射
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
        # 标准列名 → 常见别名（中英混合）。
        # 别名表只用来「自动猜测」映射，给用户填默认值，不是强制——
        # 猜不中的字段，用户在 GUI 里手动用下拉指认即可。
        # 扩到中英文常见叫法，是为了支持不同商家自定义列名的表（如「会员卡号」→ CustomerID）。
        self.column_aliases = {
          "InvoiceNo":  ["Invoice", "订单号", "订单编号", "发票号", "单号", "OrderID", "Order ID", "Order No"],
          "StockCode":  ["Stock Code", "商品编码", "商品编号", "货号", "SKU", "SKU ID", "商品ID", "ProductID", "Product ID", "Item Code"],
          "Description":["Product", "商品名称", "商品名", "品名", "描述", "Product Name", "Item Name"],
          "Quantity":   ["Qty", "数量", "购买数量", "销量", "Amount", "Count"],
          "InvoiceDate":["Order Time", "Order Timestamp", "下单时间", "交易时间", "成交时间",
                         "购买时间", "Datetime", "Timestamp", "Order Date", "OrderDate",
                         "订单日期", "交易日期", "日期", "Date", "Update Time", "Created At"],
          "UnitPrice":  ["Price", "单价", "成交价", "售价", "Unit Price", "Final Unit Price", "Sale Price", "Actual Price"],
          "CustomerID": ["Customer ID", "User ID", "客户ID", "客户编号", "会员ID", "会员编号", "会员卡号", "用户ID", "用户编号", "买家ID", "CustomerNo"],
          "Country":    ["国家", "地区", "国家地区", "Region", "Nation"],
        }
        # 映射前的原始数据快照（load_file 后填充）：
        # apply_mapping 每次都以它为基准重建 df，使「反复调整映射」幂等、不会因列名被改过而错乱
        self.raw_df = None
        # 最终采用的字段映射 {标准字段: 用户选定的原始列名}，apply_mapping 后填充，供 GUI 回显
        self.mapping = {}

    def load_file(self):
        """读取 CSV/XLSX，保留原始列名并保存可重复映射的原始快照。

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
        # 读进来先不动列名，只保留原始快照。
        # 列名统一改到「映射」环节（guess_mapping 给建议 + 用户确认 + apply_mapping 执行），
        # 让每一次列名变更都可见、可控，而不是加载时按写死别名悄悄改名——
        # 这正是「支持不同商家自定义列名」的关键：列名由用户指认，而非程序假定。
        self.raw_df = self.df.copy()
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

    def guess_mapping(self):
        """为每个标准/可选字段，在实际列里猜一个最可能的列，给映射界面当默认值

        猜测三招（置信度从高到低；已被占用的实际列不再分给其他字段）:
            ① 完全同名 —— 实际列名忽略大小写/首尾空格后与标准名相同
            ② 别名匹配 —— 实际列名命中 column_aliases 里登记的别名
            ③ 模糊包含 —— 标准名与实际列名互相包含（兜底，可能不准）

        返回值:
            dict[str, str | None]: {标准字段: 猜中的实际列名 or None}
        """
        if not self.validate():
            raise ValueError("数据未加载或为空，请先调用 load_file()")

        norm = lambda s: re.sub(r"[\s_-]+", "", str(s).strip().lower())
        # 实际列：归一名 → 原始列名（同一归一名重复时取先出现的，少见可接受）
        actual_norm = {}
        for col in self.df.columns:
            actual_norm.setdefault(norm(col), col)

        targets = self.required_columns + self.optional_columns
        guess = {std: None for std in targets}
        used = set()

        # ①② 高置信：完全同名、别名匹配
        for std in targets:
            if norm(std) in actual_norm and actual_norm[norm(std)] not in used:
                guess[std] = actual_norm[norm(std)]
                used.add(guess[std])
                continue
            for alias in self.column_aliases.get(std, []):
                col = actual_norm.get(norm(alias))
                if col is not None and col not in used:
                    guess[std] = col
                    used.add(col)
                    break

        # ③ 兜底：模糊包含（只补还没猜到的字段）
        for std in targets:
            if guess[std]:
                continue
            for col in self.df.columns:
                if col in used:
                    continue
                if norm(std) in norm(col) or norm(col) in norm(std):
                    guess[std] = col
                    used.add(col)
                    break

        return guess

    def apply_mapping(self, mapping):
        """按用户确认的映射，把原始列重命名为标准列名

        参数:
            mapping (dict[str, str | None]): {标准字段: 选定的原始列名}；
                值为 None / 空串表示该字段不映射（跳过）

        规则:
            - 以 raw_df 为基准重建 df，保证反复调整映射时幂等、不串列；
            - 同一个原始列不能映射到两个不同标准字段（否则 rename 后列名冲突）。

        返回值:
            pandas.DataFrame: 应用映射后的 df（列名已统一为标准名）
        """
        if self.raw_df is None:
            raise ValueError("数据未加载，请先调用 load_file()")

        rename_map = {}
        chosen = {}  # 原始列 → 已分配给的标准字段，用于查重
        for std, actual_col in mapping.items():
            if not actual_col:
                continue
            if actual_col not in self.raw_df.columns:
                raise ValueError(f"列 '{actual_col}' 不在数据中，无法映射到 {std}")
            if actual_col in chosen:
                raise ValueError(
                    f"列 '{actual_col}' 被同时指定给 {chosen[actual_col]} 和 {std}，请检查映射"
                )
            chosen[actual_col] = std
            if actual_col != std:
                rename_map[actual_col] = std

        df = self.raw_df.copy()
        if rename_map:
            df = df.rename(columns=rename_map)
        self.df = df
        self.mapping = {k: v for k, v in mapping.items() if v}
        self.log.append(f"字段映射已应用:{rename_map if rename_map else '（列名无需改动）'}")
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
