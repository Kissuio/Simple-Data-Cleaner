"""一次性脚本：把 Kaggle 下的 Online Retail II 处理成跟主项目列名一致的测试 CSV。

跑法：python prepare_test_data.py
输入：data/online_retail_II.xlsx（包含 2 个 sheet，列名 Invoice/Price/Customer ID）
输出：data/Online Retail II.csv（只取 Year 2009-2010 sheet，3 列重命名后）

用途：换一组真实电商数据测试系统通用性（验证清洗/RFM/可视化模块不只能跑 Online Retail 这一份数据）。
"""
import pandas as pd

SRC = "data/online_retail_II.xlsx"
DST = "data/Online Retail II.csv"
SHEET = "Year 2009-2010"  # 旧版没有的、纯新一年数据；另一 sheet 是旧版本身、跳过

# ────────────────────────────────────────────
# Step 1：读 xlsx 指定 sheet
# ────────────────────────────────────────────
print(f"[1/4] 读取 {SRC} 的 {SHEET} sheet ...")
df = pd.read_excel(SRC, sheet_name=SHEET)
print(f"      原始行数: {len(df):,}")
print(f"      原始列名: {df.columns.tolist()}")

# ────────────────────────────────────────────
# Step 2：重命名 3 列对齐主项目
# 字典 key 是 II 版的旧名，value 是我们项目用的名
# 其余 5 列（StockCode/Description/Quantity/InvoiceDate/Country）名字一致，不进字典
# ────────────────────────────────────────────
print("[2/4] 重命名 3 列 ...")
df = df.rename(columns={
    "Invoice": "InvoiceNo",
    "Price": "UnitPrice",
    "Customer ID": "CustomerID",
})

# ────────────────────────────────────────────
# Step 3：校验列名（防止 rename 字典 key 打错却不报错的坑）
# 用 set 对称差找出"缺失"和"多余"两类问题
# ────────────────────────────────────────────
print("[3/4] 校验列名 ...")
expected = {"InvoiceNo", "StockCode", "Description", "Quantity",
            "InvoiceDate", "UnitPrice", "CustomerID", "Country"}
actual = set(df.columns)
missing = expected - actual  # 该有却没有的列
extra = actual - expected    # 多出来的列
if missing or extra:
    raise ValueError(f"列名校验失败！缺失: {missing}，多余: {extra}")
print(f"      校验通过，新列名: {df.columns.tolist()}")

# ────────────────────────────────────────────
# Step 4：写出 CSV（index=False 避免多一列序号）
# ────────────────────────────────────────────
print(f"[4/4] 写入 {DST} ...")
df.to_csv(DST, index=False)
print(f"      完成！共 {len(df):,} 行")