"""临时测试 analyzer/product_analysis.py 的函数。跑通后可删。"""

import sys
sys.stdout.reconfigure(encoding='utf-8')   # 解决 PowerShell 中文乱码

from data_handlers.file_loader import FileLoader
from data_handlers.data_cleaner import DataCleaner
from analyzer.product_analysis import get_top_quantity, get_top_revenue, get_price_distribution


# ───── 加载 + 清洗 ─────
print("[1/4] 加载、清洗数据...")
loader = FileLoader("data/Online Retail.csv")
loader.load_file()

cleaner = DataCleaner(loader.df)
cleaner.clean_all()
print(f"    清洗后行数: {len(cleaner.df)}\n")


# ───── 测试 get_top_quantity ─────
print("[2/4] 计算 TOP10 销量商品...")
top_qty = get_top_quantity(cleaner.df)
print(f"    返回类型: {type(top_qty).__name__}")
print(f"    返回形状: {top_qty.shape}")
print(f"    索引(应为商品名):")
print(top_qty.to_string())


# ───── 测试 get_top_revenue ─────
print("\n[3/4] 计算 TOP10 销售额商品...")
top_rev = get_top_revenue(cleaner.df)
print(f"    返回类型: {type(top_rev).__name__}")
print(f"    返回形状: {top_rev.shape}")
print(f"    索引(应为商品名):")
print(top_rev.to_string())


# ───── 测试 get_price_distribution ─────
print("\n[4/4] 计算单价分布...")
prices = get_price_distribution(cleaner.df)
print(f"    返回类型: {type(prices).__name__}")
print(f"    返回长度: {len(prices)} 条单价")
print(f"    单价范围: 最小 {prices.min()}, 最大 {prices.max()}")
print(f"    单价均值: {prices.mean():.2f}, 中位数: {prices.median()}")
