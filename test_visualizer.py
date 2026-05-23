"""测试 Visualizer 已完成的两个图表方法：饼图 + 人均消费柱状图。
跑通后可以删除。"""

import sys
sys.stdout.reconfigure(encoding='utf-8')   # 解决 PowerShell 中文乱码

from data_handlers.file_loader import FileLoader
from data_handlers.data_cleaner import DataCleaner
from analyzer.rfm_analyzer import RFMAnalyzer
from analyzer.sales_trend import get_monthly_sales, get_weekday_hour_orders
from analyzer.product_analysis import get_top_quantity, get_top_revenue, get_price_distribution
from visualization.visualizer import Visualizer


# ───── 第 1 步：加载 + 清洗 + RFM 分析 ─────
print("[1/3] 加载、清洗、RFM 分析...")
loader = FileLoader("data/Online Retail.csv")
loader.load_file()

cleaner = DataCleaner(loader.df)
cleaner.clean_all()

analyzer = RFMAnalyzer(cleaner.df)
rfm = analyzer.analyze_all()
print(f"    RFM 表形状: {rfm.shape}")
print(f"    8 类分布:\n{rfm['Label'].value_counts().to_string()}\n")


# ───── 第 2 步：创建 Visualizer ─────
print("[2/3] 创建 Visualizer...")
viz = Visualizer()


# ───── 第 3 步：画两张图 ─────
print("[3/3] 生成图表...")
pie_path = viz.plot_label_pie(rfm)
print(f"    饼图已保存: {pie_path}")

bar_path = viz.plot_label_avg_spend(rfm)
print(f"    柱状图已保存: {bar_path}")

scatter_path = viz.plot_rfm_scatter(rfm)
print(f"    气泡图已保存: {scatter_path}")

monthly = get_monthly_sales(cleaner.df)
trend_path = viz.plot_monthly_trend(monthly)
print(f"    月度趋势图已保存: {trend_path}")

top_qty = get_top_quantity(cleaner.df)
top_qty_path = viz.plot_top_quantity(top_qty)
print(f"    TOP10 销量图已保存: {top_qty_path}")

top_rev = get_top_revenue(cleaner.df)
top_rev_path = viz.plot_top_revenue(top_rev)
print(f"    TOP10 销售额图已保存: {top_rev_path}")

prices = get_price_distribution(cleaner.df)
price_path = viz.plot_price_distribution(prices)
print(f"    单价分布图已保存: {price_path}")

pivot = get_weekday_hour_orders(cleaner.df)
heatmap_path = viz.plot_weekday_hour_heatmap(pivot)
print(f"    周热力图已保存: {heatmap_path}")

print("\n完成。打开 output/ 目录查看 PNG。")
