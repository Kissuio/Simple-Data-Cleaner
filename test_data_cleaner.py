"""测试 DataCleaner 的 4 个清洗方法是否正确执行。
跑通后可以删除。"""

import sys
sys.stdout.reconfigure(encoding='utf-8')   # 解决 PowerShell 中文乱码

from data_handlers.file_loader import FileLoader
from data_handlers.data_cleaner import DataCleaner


# ───── 第 1 步：加载原始数据 ─────
print("[1/4] 加载原始数据...")
loader = FileLoader("data/Online Retail.csv")
loader.load_file()
loader.check_columns()
print(f"    原始数据形状: {loader.df.shape}\n")


# ───── 第 2 步：实例化 DataCleaner ─────
print("[2/4] 创建 DataCleaner（应自动 .copy() 一份独立 df）...")
cleaner = DataCleaner(loader.df)
print(f"    cleaner.df 形状: {cleaner.df.shape}")
print(f"    cleaner.df 和 loader.df 是同一个对象吗？{cleaner.df is loader.df}")
print(f"    （应该是 False，因为 .copy() 创建了独立副本）\n")


# ───── 第 3 步：执行全套清洗 ─────
print("[3/4] 执行 clean_all() —— 4 个清洗方法依次调用...")
cleaner.clean_all()
print(f"    清洗后形状: {cleaner.df.shape}\n")


# ───── 第 4 步：检查清洗效果 ─────
print("[4/4] 验证清洗结果:")

# 4.1 检查 InvoiceDate 是否成功转 datetime
print(f"\n    InvoiceDate 类型: {cleaner.df['InvoiceDate'].dtype}")
print(f"    第一行时间: {cleaner.df['InvoiceDate'].iloc[0]}")

# 4.2 检查 TotalPrice 列是否成功新增
print(f"\n    TotalPrice 列前 3 行示例:")
sample = cleaner.df[['Quantity', 'UnitPrice', 'TotalPrice']].head(3)
print(sample.to_string())

# 4.3 检查取消订单是否清除（应该没有以 C 开头的 InvoiceNo）
remaining_c = cleaner.df['InvoiceNo'].astype(str).str.startswith('C').sum()
print(f"\n    剩余以 'C' 开头的 InvoiceNo: {remaining_c} 个（应为 0）")

# 4.4 检查 CustomerID 是否还有 NaN
remaining_nan = cleaner.df['CustomerID'].isna().sum()
print(f"    剩余 CustomerID 为 NaN 的行: {remaining_nan} 个（应为 0）")

# 4.5 完整日志
print(f"\n--- 完整操作日志（{len(cleaner.log)} 条）---")
for i, line in enumerate(cleaner.log, 1):
    print(f"    {i}. {line}")
