"""一次性脚本：从 Online Retail II 的多 sheet xlsx 里挑出 'Year 2009-2010' 写成 CSV，方便主项目作为测试数据集加载。

跑法：python prepare_test_data.py
输入：data/online_retail_II.xlsx（包含 2 个 sheet）
输出：data/Online Retail II.csv（只取 Year 2009-2010 sheet）

用途：换一组真实电商数据测试系统通用性。

注：原版还做了 Invoice→InvoiceNo / Price→UnitPrice / Customer ID→CustomerID 的列名重命名，
该功能已被 FileLoader.column_aliases 接管（加载时自动归一化），本脚本不再需要 rename。
"""
import pandas as pd

SRC = "data/online_retail_II.xlsx"
DST = "data/Online Retail II.csv"
SHEET = "Year 2009-2010"  # 只取这一个 sheet；另一 sheet 是 Year 2010-2011，与旧版 Online Retail 重复

# ────────────────────────────────────────────
# Step 1：读 xlsx 指定 sheet
# ────────────────────────────────────────────
print(f"[1/2] 读取 {SRC} 的 {SHEET} sheet ...")
df = pd.read_excel(SRC, sheet_name=SHEET)
print(f"      原始行数: {len(df):,}")
print(f"      原始列名: {df.columns.tolist()}")

# ────────────────────────────────────────────
# Step 2：写出 CSV（index=False 避免多一列序号）
# ────────────────────────────────────────────
print(f"[2/2] 写入 {DST} ...")
df.to_csv(DST, index=False)
print(f"      完成！共 {len(df):,} 行")
