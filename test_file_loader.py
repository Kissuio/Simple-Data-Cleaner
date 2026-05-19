"""临时测试脚本：验证 FileLoader 能否正确加载并校验 Online Retail 数据。
跑通后可以直接删除这个文件。"""

from data_handlers.file_loader import FileLoader

# 注意：文件名是 "Online Retail.csv"，中间是空格，不是下划线
loader = FileLoader("data/Online Retail.csv")

# 第 1 步：加载文件（xlsx 读 54 万行需要几十秒，请耐心等）
print("[1/3] 正在加载文件...")
df = loader.load_file()
print(f"    DataFrame 形状: {df.shape}")
print(f"    列名: {df.columns.tolist()}")

# 第 2 步：校验字段
print("\n[2/3] 正在校验字段...")
ok = loader.check_columns()
print(f"    校验结果: {ok}")

# 第 3 步：查看完整操作日志
print("\n[3/3] 操作日志:")
for line in loader.log:
    print(f"    - {line}")
