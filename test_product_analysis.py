"""临时测试 analyzer/product_analysis.py 的函数。跑通后可删。"""

import sys
sys.stdout.reconfigure(encoding='utf-8')   # 解决 PowerShell 中文乱码

from data_handlers.file_loader import FileLoader
from data_handlers.data_cleaner import DataCleaner
from analyzer.product_analysis import get_top_quantity


# ───── 加载 + 清洗 ─────
print("[1/2] 加载、清洗数据...")
loader = FileLoader("data/Online Retail.csv")
loader.load_file()

cleaner = DataCleaner(loader.df)
cleaner.clean_all()
print(f"    清洗后行数: {len(cleaner.df)}\n")


# ───── 测试 get_top_quantity ─────
print("[2/2] 计算 TOP10 销量商品...")
top_qty = get_top_quantity(cleaner.df)
print(f"    返回类型: {type(top_qty).__name__}")
print(f"    返回形状: {top_qty.shape}")
print(f"    索引(应为商品名):")
print(top_qty.to_string())
