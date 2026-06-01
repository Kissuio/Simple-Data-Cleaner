# 基于 RFM 模型的电商客户分群与运营策略分析系统

> 基于 RFM 模型，对真实电商交易数据进行清洗、客户分群与多维可视化分析的桌面应用。
> 上海大学《程序设计 A（Python）》期末项目。

## 功能简介

本系统以英国某电商 2009–2011 年的真实交易数据为对象，完成从数据清洗到客户分群、再到运营洞察的完整分析流程，并提供图形界面与 AI 辅助解读。

- **数据加载与清洗**：兼容 `.xlsx` / `.csv`，内置列名归一化（大小写不敏感 + 别名映射），可直接加载同一零售商的不同版本数据集而无需手工改列名；自动清洗缺失客户 ID、取消订单、非商品编码等异常记录。
- **RFM 客户分群**：按最近消费（R）、消费频次（F）、消费金额（M）将客户划分为 8 类（重要价值、重要发展、一般保持……），识别高价值与流失客户。
- **销售趋势分析**：月度销售趋势、周×小时订单热力图，刻画经营节奏。
- **商品分析**：销量 / 销售额 TOP10 榜单、商品单价分布。
- **可视化**：共 8 张图表（饼图 / 柱状图 / RFM 散点 / 趋势线 / TOP 榜 / 单价分布 / 热力图）。
- **图形界面**：基于 customtkinter 的现代化桌面 GUI，主页仪表盘 + 6 大功能模块，引导式操作流程。
- **AI 解读**：在「图表总览」页接入 OpenAI 兼容协议（支持 DeepSeek / Moonshot / 智谱等），对生成的图表与分析结果做自动化解读。

## 运行环境

- **Python**：3.14.3（建议 3.10 及以上）
- **操作系统**：开发与测试于 Windows 11；所依赖的库均为跨平台，理论上亦可在 macOS / Linux 运行
- 依赖库见下方「第三方库」一节，均通过 `requirements.txt` 一键安装

## 安装步骤

```bash
# 1. 创建并激活虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. 安装依赖
python -m pip install -r requirements.txt
```

## 运行方法

```bash
python main.py
```

启动后进入主页仪表盘，按引导式流程依次操作：

**加载数据 → 数据清洗 → RFM 分群 → 销售趋势 / 商品分析 → 图表总览**
（在「图表总览」页生成 8 张图后，可对图表与分析结果调用 AI 解读）

## 项目结构

```text
期末项目/
├── main.py                  # 程序入口，启动 GUI
├── requirements.txt         # 第三方依赖清单
├── README.md
├── data/                    # 数据集（UCI Online Retail）
├── data_handlers/           # 数据处理层（OOP 核心）
│   ├── base_data_handler.py #   BaseDataHandler 基类（封装 df/log/validate）
│   ├── file_loader.py       #   FileLoader：文件加载 + 列名归一化
│   └── data_cleaner.py      #   DataCleaner：多步数据清洗
├── analyzer/                # 分析层
│   ├── rfm_analyzer.py      #   RFMAnalyzer：RFM 打分与 8 类客户分群
│   ├── sales_trend.py       #   销售趋势分析（月度 / 周×小时）
│   └── product_analysis.py  #   商品分析（TOP 榜 / 单价分布）
├── visualization/
│   └── visualizer.py        # Visualizer：8 张图表绘制与导出
├── gui/                     # customtkinter 图形界面
│   ├── window.py            #   主窗口 App
│   ├── widgets.py           #   自定义组件与色板
│   ├── ai_dialog.py         #   AI 解读弹窗
│   └── pages/               #   各功能页面（主页 / 加载 / 清洗 / RFM / 销售 / 商品 / 总览）
└── output/                  # 图表输出目录（运行时自动生成）
```

## 数据说明

数据来自 [UCI Machine Learning Repository](https://archive.ics.uci.edu/) 公开数据集（CC BY 4.0 许可），记录英国一家非店面在线零售商（主营全场合礼品，客户多为批发商）的真实交易：

| 数据集 | 时间范围 | 规模 |
|---|---|---|
| Online Retail（UCI #352，主数据集） | 2010-12 ~ 2011-12 | 541,909 条 |
| Online Retail II（UCI #502，2009-2010 部分，用于跨数据集验证） | 2009-12 ~ 2010-12 | 525,461 条 |

两套数据来自同一零售商，合计覆盖其 2009–2011 全周期；Online Retail II 的 2010-2011 部分与主数据集重复，故仅取其 2009-2010 部分用于验证，未重复纳入。

两套数据列名存在差异（`InvoiceNo`/`Invoice`、`UnitPrice`/`Price`、`CustomerID`/`Customer ID`），系统在加载阶段自动归一化，因此无需手工改名即可分析。

## 第三方库

| 库 | 用途 |
|---|---|
| pandas | DataFrame 操作、清洗、RFM 计算 |
| numpy | 数值计算（log 轴 bins、log10）|
| openpyxl | 读取 `.xlsx` 文件（pandas 隐式依赖）|
| matplotlib | 8 张图表的绘图引擎 |
| seaborn | 周×小时热力图 |
| pillow | 图片显示（缩略图、大图预览）|
| customtkinter | 现代化 Tkinter UI（圆角、主题、统一字体）|
| openai | OpenAI 兼容协议，对接多家 AI 服务商 |

完整版本号见 [requirements.txt](requirements.txt)。

## 作者

- 姓名：（待填写）
- 学号：（待填写）
- 班级：（待填写）
- 专业：上海大学 信息管理专业
