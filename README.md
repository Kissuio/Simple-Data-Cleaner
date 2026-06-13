# 面向电商交易数据的通用清洗与可视化分析系统

> 一个**通用**的电商交易数据清洗与可视化桌面应用：对具备必要字段的交易表完成数据清洗、列名对应关系确认、RFM 客户分群与多维图表展示，并提供 AI 辅助解读。
> 上海大学《程序设计 A（Python）》期末项目。

## 功能简介

系统把“从原始交易表到运营洞察”的完整流程做成图形化工具。它**不把某一张表的列名或清洗步骤焊死在代码里**：加载时保留原始列名，用通用清洗工具箱处理，进入分析前再由用户把自己表中的列对应到标准字段。具备客户、订单、时间和金额等必要语义字段，并能完成列名对应关系确认的交易表，可以复用同一套分析模块。项目使用多套来源、规模与列名结构不同的电商交易数据进行开发和验证。

- **数据加载**：兼容 `.xlsx` / `.csv`，加载时保留原始列名，自动尝试多种编码（utf-8 / gbk / latin-1），适配不同来源的文件。
- **数据清洗（通用工具箱）**：一组可自由组合的参数化清洗原语——去重、删空值、按文本 / 数值条件删行、文本规整、类型转换、派生新列等；在数据业务含义与字段条件满足时，还可选用取消记录配对工具。支持**撤销与重置**，不规定固定执行顺序。
- **列名对应关系确认（通用化关键）**：进入分析前，由用户把自己表中的列对应到标准分析字段（系统按列名提供初始匹配建议）；缺销售额时可由“数量 × 单价”自动派生。
- **RFM 客户分群**：按最近消费（R）、消费频次（F）、消费金额（M）将客户划分为 8 类（重要价值、重要发展、一般保持……），识别高价值与流失客户。
- **销售与商品分析**：月度销售趋势、周×小时与各年各月订单热力图、销量 / 销售额 TOP10 榜单、商品单价分布。
- **可视化**：共 9 张图表，可逐张预览、导出 PNG（按数据集分文件夹存放）。
- **全局筛选**：分析页顶部可按年月、国家筛选，动态重算 RFM 与图表。
- **图形界面**：基于 customtkinter 的现代化桌面 GUI，主页仪表盘集中展示状态、模块入口与下一步建议。
- **AI 解读**：在「图表总览」页接入 OpenAI 兼容协议（支持 DeepSeek / Moonshot / 智谱等），对图表与分析结果生成文字解读。

## 运行环境

- **Python**：3.14.3（建议 3.10 及以上）
- **操作系统**：开发与测试于 Windows 11；所依赖的库均为跨平台，理论上亦可在 macOS / Linux 运行。
- 依赖库见「第三方库」一节，通过 `requirements.txt` 一键安装。

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

启动后进入主页仪表盘，可按当前数据状态选择需要使用的模块：

**加载数据 → 数据清洗 → 分析字段确认 → RFM 分群 → 销售 / 商品分析 → 图表总览**

清洗阶段用原始列名自由处理；首次进入任一分析页时会弹出**列名对应关系确认**对话框，确认列对应关系后即可生成结果；在「图表总览」页生成 9 张图后，可对图表与分析结果调用 AI 解读。

## AI 解读与 API Key 配置

AI 解读通过 OpenAI 兼容协议调用，可在界面中选择 OpenAI、DeepSeek、Moonshot、智谱或自定义兼容服务。

1. 先在「图表总览」生成图片，或在“AI 分析本页”中截取当前页面。
2. 在 AI 弹窗中选择供应商，填写对应的 `Base URL`、模型名和 API Key。
3. API Key 只保存在当前弹窗的内存变量中，不写入代码、配置文件或磁盘。
4. 未填写 API Key 时，程序会弹出中文提示并停止本次远程调用，不影响加载、清洗、RFM 和图表功能。
5. 没有可用 API Key 时，可使用“复制提示词”把图片与提示词交给其他支持图片分析的工具；教师快速查阅功能本身也不依赖真实 API。

本项目没有内置任何真实密钥，提交材料中也不应包含 `.env`、密钥截图或真实 API Key。

## 项目结构

```text
期末项目/
├── main.py                  # 程序入口，启动 GUI
├── requirements.txt         # 第三方依赖清单
├── README.md
├── AI_conversation_records_Claude_Code.md  # Claude Code 关键对话导出记录
├── data/                    # 多套数据集（online_retail / superstore / jd / others）
├── data_handlers/           # 数据处理层（OOP 核心）
│   ├── base_data_handler.py #   BaseDataHandler 基类（封装 df/log/validate）
│   ├── file_loader.py       #   FileLoader：读取 .csv/.xlsx，保留原始列名（多编码兼容）
│   ├── data_cleaner.py      #   DataCleaner：通用清洗工具箱（参数化原语 + 撤销/重置）
│   └── field_mapping.py     #   列名对应关系纯函数：初始匹配建议 + 标准字段生成 + 缺字段校验
├── analyzer/                # 分析层
│   ├── rfm_analyzer.py      #   RFMAnalyzer：RFM 打分与 8 类客户分群
│   ├── sales_trend.py       #   销售趋势分析（月度 / 周×小时 / 年×月）
│   ├── product_analysis.py  #   商品分析（TOP 榜 / 单价分布）
│   └── insights.py          #   图表洞察文案动态生成
├── visualization/
│   └── visualizer.py        # Visualizer：9 张图表绘制与导出
├── gui/                     # customtkinter 图形界面
│   ├── window.py            #   主窗口 App（数据中枢 + 列名对应关系调度 + 全局筛选）
│   ├── widgets.py           #   自定义组件与色板
│   ├── filter_bar.py        #   顶部全局筛选栏
│   ├── mapping_dialog.py    #   列名对应关系确认对话框
│   ├── clean_dialog.py      #   清洗参数对话框
│   ├── ai_dialog.py         #   AI 解读弹窗
│   ├── output_paths.py      #   按数据集名生成图片输出目录
│   └── pages/               #   各功能页面（主页 / 加载 / 清洗 / RFM / 销售 / 商品 / 总览）
├── report/                  # 技术报告与配图（结构图 / UML 类图 / 报告文档）
└── output/                  # 图表输出总目录，内部按 数据名_output_picture 分文件夹
```

## 系统设计

系统按职责分为四层，数据以 pandas DataFrame 单向流转：

- **数据处理层** `data_handlers/`：文件加载、清洗与列名对应关系确认，产出干净且列名标准化的交易数据；OOP 核心 `BaseDataHandler` 封装公共 `df / log / validate`，`FileLoader / DataCleaner / RFMAnalyzer` 继承复用。
- **分析层** `analyzer/`：RFM 分群、销售趋势、商品分析（无状态函数模块）。
- **可视化层** `visualization/`：将聚合结果绘制为 9 张图表并导出。
- **界面层** `gui/`：customtkinter 图形界面，主窗口 `App` 充当数据中枢，`get_active_df()` 在清洗后数据上应用已确认的列名对应关系与全局筛选统一对外供数。

完整的**系统结构图**与 **UML 类图**见 `report/architecture.png`、`report/class_diagram.png`（亦收录于技术报告「系统设计」章节）。

## 数据说明

数据来源包含 [UCI Machine Learning Repository](https://archive.ics.uci.edu/) 公开数据（CC BY 4.0 许可），也包含其他不同结构的电商交易样例，用于检验系统对列名差异和表格结构差异的适应能力：

| 数据集 | 时间范围 | 规模 |
|---|---|---|
| Online Retail（UCI #352） | 2010-12 ~ 2011-12 | 541,909 条 |
| Online Retail II（UCI #502，2009-2010 部分，用于跨数据集验证） | 2009-12 ~ 2010-12 | 525,461 条 |

两套数据来自同一零售商；其列名存在差异（`InvoiceNo`/`Invoice`、`UnitPrice`/`Price`、`CustomerID`/`Customer ID`），正好用于验证系统的通用性——进入分析前通过列名对应关系确认统一到标准字段，无需手工改名即可分析。

> 数据文件体积较大，未纳入版本库；各数据文件夹的 `来源说明.md` 保留出处链接，可据此复现。

## 第三方库

| 库 | 用途 |
|---|---|
| pandas | DataFrame 操作、清洗、RFM 计算 |
| numpy | 数值计算（对数轴 bins、log10）|
| openpyxl | 读取 `.xlsx` 文件（pandas 隐式依赖）|
| matplotlib | 图表绘制引擎 |
| seaborn | 热力图 |
| pillow | 图片显示（缩略图、大图预览）|
| customtkinter | 现代化 Tkinter UI（圆角、主题、统一字体）|
| openai | OpenAI 兼容协议，对接多家 AI 服务商 |

完整版本号见 [requirements.txt](requirements.txt)。

## 作者

- 姓名：鲁霄曈
- 学号：25122027
- 班级：信管 2 班
- 专业：上海大学 信息管理与信息系统

```text
本项目在开发中使用 AI 辅助工具（代码框架与调试、文档排版），详见技术报告「AI 使用日志」。
```
