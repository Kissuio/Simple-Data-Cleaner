"""新手带练(Guided Tour)—— 用一份真实数据，带着新手在真实页面上亲手走完整流程。

设计原则(综合用户反馈)：
- **亲手操作 > 代点**：清洗工具由学生**自己在真实页面上点真实按钮、在弹窗里选列选参数**，
  教练浮窗只负责「精确指路 + 事后检验这一步是否真做到了」，做到了才放行；没做到给提示。
  (这取代了上一版「点教练上的『执行这一步』由教练代劳」的做法。)
- **只讲这份表用到的工具**：不把工具箱里 9 个工具一次性灌给学生，只在用到某个工具那一步讲它。
- **字段映射放在进入 RFM 时才弹**(方案 B 本意：清洗只面对原始列，进分析才固定字段)，
  且这一步最容易让人误会，讲得最细。
- **清洗完成后告诉学生还有更多工具**，应对别的表格形态，体现这套工具是通用的。

带练用的数据：`data/jd/JD_order_data.csv`(京东真实订单，约 55 万行)。选它是因为它**天然用到的清洗
工具种类最多**(删重复、按数值删行删掉单价≤0 的赠品、列转日期、因为没有金额列还要派生新列)，
而且它和报告里用的英国 Online Retail 完全不同——正好说明本系统不是只为某一份数据写死的。
"""

import re
import tkinter.font as tkfont

import customtkinter as ctk
import pandas as pd

from gui.widgets import BORDER_WIDTH, UI_COLORS as COLORS, apply_hanging_indent, chart_group_complete
from gui.window import PROJECT_ROOT

TOUR_DATA_PATH = PROJECT_ROOT / "data" / "jd" / "JD_order_data.csv"


def build_tour_steps():
    """返回带练步骤。字段：

    key / page / title / body 必有；page=None 表示停留当前页面。
    assist / assist_text  可选：教练浮窗上的一个辅助按钮(如「载入示例数据」「打开映射窗」)，
                          这类是"非工具"的环节(选示例文件、打开映射窗)，由按钮代劳。
    verify / verify_hint  可选：点「下一步」时先检验这一步是否真做到了(看数据结果)，
                          没做到就显示 verify_hint、不放行。清洗/分析这些「要亲手做」的步骤靠它。
    """
    return [
        {
            "key": "welcome",
            "page": "主页",
            "title": "欢迎进入新手带练",
            "body": (
                "欢迎您使用新手带练。本流程将使用一份**真实的京东订单数据**(约 55 万行)，"
                "引导您在真实页面上**亲手**完成完整的分析流程：加载 → 数据清洗 → 字段映射 → "
                "RFM 客户分群 → 销售 / 商品分析 → 图表总览。\n\n"
                "与「教师快速查阅」(一键自动运行、仅查看结果)不同，本流程的**每一步都需要您亲自操作**；"
                "我们会通过右下角的引导浮窗为您讲解每一步的操作要点，并在您完成后协助您核对结果。\n\n"
                "另外值得说明：这份京东数据与技术报告中所用的英国电商数据集(Online Retail)"
                "在列名与格式上完全不同——能用同一套工具同样完成清洗与分析，"
                "正说明本系统**并非只适用于某一种固定格式的数据表**，而是能够适配不同来源的交易数据。\n\n"
                "准备就绪后，请点击「下一步」开始。"
            ),
        },
        {
            "key": "load",
            "page": "加载数据",
            "title": "第 1 步 · 加载数据",
            "body": (
                "分析的第一步，是将交易表读入系统。正常使用时，您会在本页点击「选择文件」，"
                "选择自己的 CSV / Excel 文件；在带练中，为省去查找文件的步骤，请点击下方按钮，"
                "我们将直接为您载入这份京东示例数据。\n\n"
                "载入完成后，页面会显示原始行数与前几行预览，建议您先大致浏览它的结构"
                "(order_ID 订单号、user_ID 客户、order_time 下单时间、quantity 数量、"
                "final_unit_price 实付单价、sku_ID 商品编码)。\n\n"
                "确认载入完成后，请点击「下一步」。"
            ),
            "assist": "load_sample",
            "assist_text": "① 载入京东示例数据(约 55 万行)",
            "verify": "loaded",
            "verify_hint": "尚未检测到已载入的数据，请先点击上方的「载入京东示例数据」按钮。",
        },
        {
            "key": "dup",
            "page": "数据清洗",
            "title": "第 2 步 · 删除完全重复的整行",
            "body": (
                "进入数据清洗页后，我们建议您先处理「完全重复的整行」——同一条记录被重复导出，"
                "会使统计结果虚高。\n\n"
                "请您按以下步骤操作：\n"
                "  1)点击页面上的「删除行工具 …」按钮；\n"
                "  2)在弹窗顶部的下拉框中选择「删重复行」；\n"
                "  3)点击弹窗中的「执行」。\n\n"
                "完成后，您可查看左上角「当前记录 / 删除记录」的变化，再点击「下一步」，"
                "我们将为您核对重复行是否已清除。"
            ),
            "verify": "dedup",
            "verify_hint": "数据中似乎仍存在完全重复的行，请通过「删除行工具 … → 删重复行 → 执行」处理后再继续。",
        },
        {
            "key": "range",
            "page": "数据清洗",
            "title": "第 3 步 · 删除单价 ≤ 0 的赠品行",
            "body": (
                "这份数据中约有两成记录的 final_unit_price(实付单价)为 0 或负数——它们大多是"
                "赠品 / 满赠，并非正常销售，会使客单价、销售额产生偏差，建议予以剔除。\n\n"
                "请您按以下步骤操作：\n"
                "  1)点击「删除行工具 …」按钮；\n"
                "  2)在顶部下拉框中选择「按数值条件删行」；\n"
                "  3)作用的列选择 final_unit_price；\n"
                "  4)比较方式选择「<=」(小于等于)；\n"
                "  5)阈值填写 0；\n"
                "  6)点击「执行」。\n\n"
                "完成后，您会看到行数明显下降，再点击「下一步」即可。"
            ),
            "verify": "price_positive",
            "verify_hint": "数据中仍存在 final_unit_price ≤ 0 的行，请通过「删除行工具 → 按数值条件删行」，对 final_unit_price 删除「<= 0」的记录。",
        },
        {
            "key": "date",
            "page": "数据清洗",
            "title": "第 4 步 · 将下单时间转换为日期类型",
            "body": (
                "order_time(下单时间)目前仍为文本格式。若要按时间维度进行分析"
                "(RFM 中的 R 值、月度趋势、星期 × 小时热力图)，需先将其转换为真正的「日期类型」。\n\n"
                "请您按以下步骤操作：\n"
                "  1)点击「转换列类型工具 …」按钮；\n"
                "  2)在顶部下拉框中选择「列转日期」；\n"
                "  3)日期列选择 order_time；\n"
                "  4)点击「执行」。\n\n"
                "完成后请点击「下一步」，我们将为您核对 order_time 是否已转换为日期类型。"
            ),
            "verify": "date_converted",
            "verify_hint": "order_time 尚未转换为日期类型，请通过「转换列类型工具 → 列转日期」，对 order_time 执行一次转换。",
        },
        {
            "key": "derive",
            "page": "数据清洗",
            "title": "第 5 步 · 准备分析所需的销售额列",
            "body": (
                "到这一步，针对这份数据的清洗与整理已基本完成。\n\n"
                "如果您**只需要一份清洗后的干净数据、不打算继续后续分析**，可以直接点击页面右上角的"
                "「导出当前数据」按钮，将结果另存为新的 CSV / Excel 文件(不会修改原始数据文件)，"
                "到此即可结束。\n\n"
                "如果您希望继续进行客户分群与可视化分析，则还需要一列「销售额」。而这份京东数据表中"
                "**没有现成的销售额列**，仅有数量与单价——因此我们用「派生新列」工具，"
                "按「金额 = 数量 × 实付单价」将它计算出来。\n\n"
                "请您按以下步骤操作：\n"
                "  1)点击「整理 / 派生工具 …」按钮；\n"
                "  2)在顶部下拉框中选择「派生新列」；\n"
                "  3)新列名保持默认 TotalPrice(销售额)；\n"
                "  4)列 A 选择 quantity；\n"
                "  5)运算方式选择「×」；\n"
                "  6)列 B 选择 final_unit_price；\n"
                "  7)点击「执行」。\n\n"
                "完成后，预览表最右侧会新增一列 TotalPrice，再点击「下一步」继续。"
            ),
            "verify": "derived",
            "verify_hint": "尚未检测到派生出的金额列，请通过「整理 / 派生工具 → 派生新列」，将新列名设为 TotalPrice，计算 quantity × final_unit_price。",
        },
        {
            "key": "clean_done",
            "page": "数据清洗",
            "title": "清洗完成 · 工具箱中还有更多工具",
            "body": (
                "数据清洗已完成。本次您依次用到了：删重复行、按数值条件删行、列转日期、派生新列。\n\n"
                "除这几项外，我们还提供了更多清洗工具(例如删空值、列转数值、文本规整、删除取消单等)，"
                "以应对其他数据表中可能出现的不同情况；这份京东表只是没有用到它们而已。\n\n"
                "这也说明这套工具是**通用**的，能适配不同来源的数据表。请点击「下一步」，进入字段映射。"
            ),
        },
        {
            "key": "mapping",
            "page": None,
            "title": "第 6 步 · 字段映射(最容易混淆，请您仔细阅读)",
            "body": (
                "数据清洗完成后即可进入分析环节，但在此之前需要先解决一个问题：系统内部统一使用"
                "一套**标准字段**(客户 ID、订单号、交易时间、销售额等)来组织分析。这套统一标准"
                "与字段映射相配合，使系统能够适配列名各异的各类商家数据表。而您这张表的列名是"
                " user_ID、order_ID、order_time 等，因此需要先告诉系统：它们分别对应哪个标准字段。\n\n"
                "「字段映射」正是用于解决这一问题：它相当于建立一张**对照表**，将系统所需的每个"
                "标准字段，逐一指向您表中对应的列。例如您指明「本表的 user_ID 列即系统所需的"
                "『客户 ID』」，系统随后便依此对照取数与计算。\n\n"
                "以这份京东数据为例，对照关系如下(左为标准字段，右为您表里对应的列)：\n"
                "  · 客户 ID ← user_ID(谁购买，RFM 据此分群)\n"
                "  · 订单号 ← order_ID(哪一单，用于计算频次)\n"
                "  · 交易时间 ← order_time(何时下单)\n"
                "  · 销售额 ← TotalPrice(刚派生出的金额)\n"
                "  · 商品编码 ← sku_ID(买了什么，供商品分析)\n\n"
                "在映射窗里操作时，请您注意：\n\n"
                "  · 每一行右侧都附有**样例值**，对照样例逐列核对，最不容易选错。\n\n"
                "  · 一张交易表中往往有多个形似「编号」的列(客户编号、订单号、商品编号等)，"
                "它们最容易混淆。映射时请看清每个编号实际代表的对象，再对应到相应字段——"
                "例如本表的 **user_ID(客户)、order_ID(订单)、sku_ID(商品)** "
                "三者含义完全不同，切勿混用。\n\n"
                "  · 若某列系统猜错了，点击该行的下拉框手动改选即可。\n\n"
                "这份京东表列名较规范，系统大多已自动匹配好，您**对照样例核对一遍、确认**即可。\n\n"
                "请点击下方按钮前往 RFM 页并打开映射窗，确认完成后返回，点击「下一步」。"
            ),
            "assist": "goto_mapping",
            "assist_text": "前往 RFM 并打开字段映射窗",
            "verify": "mapped",
            "verify_hint": "尚未完成字段映射，请点击上方按钮，在弹出的映射窗中核对各列后点击确认。",
        },
        {
            "key": "rfm",
            "page": "RFM 分析",
            "title": "第 7 步 · RFM 客户分群",
            "body": (
                "RFM 是一种衡量客户价值的方法，它从三个维度刻画客户：\n\n"
                "  · 最近一次消费时间(Recency)：距今越近，通常说明客户越活跃、再次购买的可能性越高；\n\n"
                "  · 消费频次(Frequency)：购买次数越多，说明客户的黏性与忠诚度越强；\n\n"
                "  · 消费金额(Monetary)：累计消费越高，说明该客户为商家创造的价值越大。\n\n"
                "系统会综合这三项指标，将客户划分为「重要价值客户」「重要保持客户」等 8 类，"
                "便于针对不同客群采取不同的运营策略。\n\n"
                "请您点击本页的「一键全分析」按钮，系统将计算每位客户的 R / F / M 指标，"
                "并为其标注所属的客户群。\n\n"
                "待页面显示客户数量与 8 类分布后，请点击「下一步」。"
            ),
            "verify": "rfm_done",
            "verify_hint": "尚未检测到 RFM 分析结果，请点击本页的「一键全分析」按钮生成客户分群。",
        },
        {
            "key": "sales",
            "page": "销售分析",
            "title": "第 8 步 · 销售分析",
            "body": (
                "完成清洗与字段映射后，便可从时间维度观察销售规律。\n\n"
                "请您依次点击本页的「月度趋势」与「周热力图」两个按钮"
                "(如有兴趣，也可点击「年月分布」查看)。\n\n"
                "需要说明的是：这份京东数据仅覆盖 2018 年 3 月这一个月，因此「月度趋势」图"
                "只有一个数据点，属于正常现象；本步真正值得关注的是**「周热力图」(星期 × 小时)**"
                "——由于前面已将 order_time 转换为带具体时刻的日期，这里才能看出一周之内"
                "哪一天、哪个时段的下单最为集中。\n\n"
                "两张图均生成后，请点击「下一步」。"
            ),
            "verify": "sales_done",
            "verify_hint": "销售图尚未全部生成，请点击本页的「月度趋势」与「周热力图」两个按钮。",
        },
        {
            "key": "product",
            "page": "商品分析",
            "title": "第 9 步 · 商品分析",
            "body": (
                "接下来从商品角度观察：销量、销售额与价格分布。\n\n"
                "请您依次点击本页的「TOP10 销量」「TOP10 销售额」「单价分布」三个按钮。"
                "(这份京东表只有商品编码 sku_ID、没有商品名称，因此榜单中显示的是商品编码，"
                "属于正常现象。)\n\n"
                "页面中所显示的为固定尺寸的预览图，部分细节可能无法完整呈现；如需查看完整大图，"
                "可在下一步「图表总览」中使用「导出此图」按钮保存后查看。\n\n"
                "三张图均生成后，请点击「下一步」。"
            ),
            "verify": "product_done",
            "verify_hint": "商品图尚未全部生成，请点击本页的「TOP10 销量」「TOP10 销售额」「单价分布」三个按钮。",
        },
        {
            "key": "overview",
            "page": "图表总览",
            "title": "第 10 步 · 图表总览",
            "body": (
                "最后，在图表总览中将 9 张图统一汇总查看。\n\n"
                "请您点击本页的「生成全部图表」按钮，系统会一次性生成全部 9 张图，"
                "并在右侧目录中列出。生成后，您可以：\n\n"
                "  · 在右侧目录中逐张点击查看；\n\n"
                "  · 页面内为缩放后的预览；每张图实际已生成为完整 PNG，如需在程序外查看大图"
                "或放入报告，可点击「导出此图」，将其另存到您指定的位置；\n\n"
                "  · 点击「AI 解读」，由模型针对当前图生成一段文字说明，便于撰写报告。\n\n"
                "9 张图全部生成后，请点击「下一步」。"
            ),
            "verify": "overview_done",
            "verify_hint": "图表尚未全部生成，请点击本页的「生成全部图表」按钮。",
        },
        {
            "key": "done",
            "page": "主页",
            "title": "带练完成 🎉",
            "body": (
                "您已经**亲手**完整地走完了整个流程：加载 → 清洗(删重复 / 删单价 ≤ 0 / 转日期 / "
                "派生金额) → 字段映射 → RFM → 销售 → 商品 → 图表总览。\n\n"
                "接下来，您可以从主页的「加载数据」换上**您自己的**交易表，按相同的思路再操作一遍："
                "清洗工具可根据数据的实际问题自由组合、并无固定顺序；进入 RFM 时，系统会弹出字段映射窗，"
                "供您逐列确认；这份京东表未用到的那些工具(删空值 / 列转数值 / 文本规整 / 删取消单配对)，"
                "在遇到相应问题的数据表时便能派上用场。\n\n"
                "如有需要，您可随时再次点击主页的「新手带练」重新体验。点击「完成」即可关闭本引导。"
            ),
        },
    ]


class GuidedTour(ctk.CTkToplevel):
    """右下角常驻的「教练浮窗」：指路 + 检验，学生在真实页面亲手操作。非模态，不阻断主窗口。"""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.steps = build_tour_steps()
        self.index = 0
        self._raw_cols = set()  # 载入时记录原始列名，供「派生新列」检验用
        self._bold_font = None  # 正文 **加粗** 用的派生粗体字体，首次渲染时按实际字号建一次
        self._status_token = 0  # 每次更新状态自增，用于让过期的失败闪烁自行停止

        self.title("新手带练")
        self.geometry("600x620")
        self.configure(fg_color=COLORS["page_bg"])
        self.protocol("WM_DELETE_WINDOW", self._quit)
        self.transient(app)
        self.attributes("-topmost", True)

        self.progress_var = ctk.StringVar(value="")
        self.title_var = ctk.StringVar(value="")
        self.status_var = ctk.StringVar(value="")

        self._build()
        self._place_bottom_right()
        self._render()

    # ───────────────────────── 界面 ─────────────────────────
    def _build(self):
        ctk.CTkLabel(
            self, textvariable=self.progress_var, font=("SimHei", 11, "bold"),
            text_color=COLORS["green"], anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 2))

        ctk.CTkLabel(
            self, textvariable=self.title_var, font=("SimHei", 15, "bold"),
            text_color=COLORS["text"], anchor="w", justify="left", wraplength=550,
        ).pack(fill="x", padx=20, pady=(0, 8))

        # 底部按钮先钉底
        bottom = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        bottom.pack(side="bottom", fill="x", padx=20, pady=(6, 14))

        self.quit_btn = ctk.CTkButton(
            bottom, text="退出带练", command=self._quit,
            fg_color="transparent", hover_color=COLORS["page_bg"],
            text_color=COLORS["muted"], border_color=COLORS["border"], border_width=1,
            font=("SimHei", 12), height=34, width=92, corner_radius=6,
        )
        self.quit_btn.pack(side="left")

        self.next_btn = ctk.CTkButton(
            bottom, text="下一步 →", command=self._next,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            font=("SimHei", 13, "bold"), height=34, width=120, corner_radius=6,
        )
        self.next_btn.pack(side="right")

        self.prev_btn = ctk.CTkButton(
            bottom, text="← 上一步", command=self._prev,
            fg_color=COLORS["gray"], hover_color=COLORS["gray_hover"],
            font=("SimHei", 12), height=34, width=92, corner_radius=6,
        )
        self.prev_btn.pack(side="right", padx=(0, 8))

        # 辅助按钮(载入示例 / 打开映射窗)单独一行，按需显隐
        self.assist_btn = ctk.CTkButton(
            self, text="", command=self._assist,
            fg_color=COLORS["green"], hover_color=COLORS["green_hover"],
            font=("SimHei", 13, "bold"), height=40, corner_radius=6,
        )

        # 状态 / 检验反馈行
        self.status_label = ctk.CTkLabel(
            self, textvariable=self.status_var, font=("SimHei", 11),
            text_color=COLORS["green"], anchor="w", justify="left", wraplength=550,
            fg_color="transparent", corner_radius=6,
        )
        self.status_label.pack(side="bottom", fill="x", padx=20, pady=(0, 6), ipady=4)

        self.body_box = ctk.CTkTextbox(
            self, font=("SimHei", 13), fg_color="#ffffff", text_color=COLORS["text"],
            border_color=COLORS["border"], border_width=BORDER_WIDTH, corner_radius=8,
            wrap="word",
        )
        self.body_box.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 8))

    def _place_bottom_right(self):
        self.update_idletasks()
        try:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            w, h = 600, 620
            self.geometry(f"{w}x{h}+{max(20, sw - w - 48)}+{max(20, sh - h - 96)}")
        except Exception:
            pass

    # ───────────────────────── 渲染当前步骤 ─────────────────────────
    def _render(self):
        step = self.steps[self.index]

        page = step.get("page")
        if page is not None:
            try:
                self.app.show_page(page)
            except Exception:
                pass
        self.lift()

        self.progress_var.set(f"新手带练 · 第 {self.index + 1} / {len(self.steps)} 步")
        self.title_var.set(step["title"])
        self._set_body(step["body"])
        self._set_status(self._data_status_line(), ok=True)

        # 辅助按钮
        if step.get("assist"):
            self.assist_btn.configure(text=step.get("assist_text", "执行"))
            self.assist_btn.pack(side="bottom", fill="x", padx=20, pady=(0, 4))
        else:
            self.assist_btn.pack_forget()

        self.prev_btn.configure(state="normal" if self.index > 0 else "disabled")
        if self.index == len(self.steps) - 1:
            self.next_btn.configure(text="完成", command=self._quit)
        else:
            self.next_btn.configure(text="下一步 →", command=self._next)

    def _set_body(self, text):
        """把正文写入只读文本框；`**……**` 渲染成真正的粗体。

        CTkTextbox 是纯文本框、不解析 markdown，直接写 `**粗体**` 只会原样显示星号。
        这里按 `**……**` 切段：普通段照常插入，加粗段用 tkinter 文本 tag 套粗体字体。
        """
        box = self.body_box
        box.configure(state="normal")
        box.delete("1.0", "end")
        # CTkTextbox.tag_config 禁止 font 选项(怕与缩放冲突)，改用底层 tkinter Text，
        # 并从文本框「当前实际字体」派生一个同号粗体——这样能自动跟随 set_widget_scaling
        # 的缩放，粗体和正文大小一致。粗体字体只建一次、缓存复用。
        under = box._textbox
        if getattr(self, "_bold_font", None) is None:
            base = tkfont.Font(font=under.cget("font"))
            self._bold_font = tkfont.Font(
                family=base.cget("family"), size=base.cget("size"), weight="bold"
            )
            under.tag_config("bold", font=self._bold_font)
        pos = 0
        for m in re.finditer(r"\*\*(.+?)\*\*", text):
            if m.start() > pos:
                box.insert("end", text[pos:m.start()])
            box.insert("end", m.group(1), "bold")
            pos = m.end()
        if pos < len(text):
            box.insert("end", text[pos:])
        apply_hanging_indent(box)
        box.configure(state="disabled")

    def _set_status(self, text, ok=True):
        self.status_var.set(text)
        self._status_token += 1
        if ok:
            self.status_label.configure(text_color=COLORS["green"], fg_color="transparent")
            return
        # 失败：红底横幅 + 响铃 + 短暂闪烁，避免新手只看到一行不起眼的红字而漏掉
        self.status_label.configure(text_color=COLORS["red"], fg_color=COLORS["red_soft"])
        try:
            self.bell()
        except Exception:
            pass
        self._flash_status(self._status_token, 0)

    def _flash_status(self, token, step):
        """红底横幅闪烁几下抓注意力；token 过期(已切到新状态)则停止，避免残留。"""
        if token != self._status_token:
            return
        frames = [COLORS["red"], COLORS["red_soft"], COLORS["red"], COLORS["red_soft"]]
        if step >= len(frames):
            self.status_label.configure(fg_color=COLORS["red_soft"], text_color=COLORS["red"])
            return
        color = frames[step]
        strong = color != COLORS["red_soft"]
        self.status_label.configure(
            fg_color=color,
            text_color="#ffffff" if strong else COLORS["red"],
        )
        self.after(130, lambda: self._flash_status(token, step + 1))

    def _data_status_line(self):
        app = self.app
        loader_df = app.loader.df if getattr(app, "loader", None) is not None else None
        cleaner_df = app.cleaner.df if getattr(app, "cleaner", None) is not None else None
        rfm_df = getattr(app, "rfm_df", None)
        if loader_df is None:
            return "当前：尚未加载数据。"
        parts = [f"原始 {len(loader_df):,} 行"]
        if cleaner_df is not None:
            parts.append(f"当前 {len(cleaner_df):,} 行")
        if rfm_df is not None:
            parts.append(f"RFM {len(rfm_df):,} 个客户")
        return "当前：" + " ｜ ".join(parts)

    # ───────────────────────── 导航 + 检验 ─────────────────────────
    def _next(self):
        step = self.steps[self.index]
        verify = step.get("verify")
        if verify is not None:
            checker = getattr(self, f"_verify_{verify}", None)
            ok = False
            try:
                ok = bool(checker()) if checker else True
            except Exception:
                ok = False
            if not ok:
                self._set_status("⚠ " + step.get("verify_hint", "这一步似乎还没完成，请按说明操作后再点「下一步」。"), ok=False)
                return
        if self.index < len(self.steps) - 1:
            self.index += 1
            self._render()

    def _prev(self):
        if self.index > 0:
            self.index -= 1
            self._render()

    def _quit(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    # ───────────────────────── 辅助按钮动作 ─────────────────────────
    def _assist(self):
        step = self.steps[self.index]
        token = step.get("assist")
        handler = getattr(self, f"_assist_{token}", None) if token else None
        if handler is None:
            return
        try:
            message = handler()
        except Exception as e:
            from gui.error_messages import show_friendly_error
            show_friendly_error("带练操作失败", e, f"执行「{step['title']}」的辅助操作", parent=self)
            return
        self._set_status(message or self._data_status_line(), ok=True)
        self.lift()

    def _assist_load_sample(self):
        from data_handlers.data_cleaner import DataCleaner
        from data_handlers.file_loader import FileLoader
        from gui.window import make_chart_progress

        path = TOUR_DATA_PATH
        if not path.exists():
            raise FileNotFoundError(
                f"未找到带练示例数据：{path}\n请确认 data/jd/JD_order_data.csv 是否存在。"
            )
        loader = FileLoader(str(path))
        loader.load_file()
        self.app.loader = loader
        self.app.cleaner = DataCleaner(loader.df)
        self.app.rfm_analyzer = None
        self.app.rfm_df = None
        self.app.visualizer = None
        self.app.chart_progress = make_chart_progress()
        self.app.reset_data_filter()
        self.app.field_mapping = None
        self.app.mapping_intro_seen = True
        self.app.cleaning_intro_seen = True
        self._raw_cols = set(loader.df.columns)
        # 刷新加载页显示
        page = self.app.pages.get("加载数据")
        if page is not None and hasattr(page, "on_show"):
            try:
                page.on_show()
            except Exception:
                pass
        return f"已载入京东示例数据：{len(loader.df):,} 行 × {len(loader.df.columns)} 列。"

    def _assist_goto_mapping(self):
        # 前往 RFM 页：show_page 进入分析页且未映射时已会自动弹出字段映射窗，
        # 这里不能再调一次 open_field_mapping，否则会弹两次（已映射则无需再弹）。
        self.app.show_page("RFM 分析")
        self.lift()
        return "已打开字段映射窗，请对照样例值核对各列后点击确认。"

    # ───────────────────────── 各步骤检验(看真实数据结果)─────────────────────────
    def _cleaner_df(self):
        cl = getattr(self.app, "cleaner", None)
        return cl.df if cl is not None and getattr(cl, "df", None) is not None else None

    def _verify_loaded(self):
        loader = getattr(self.app, "loader", None)
        return loader is not None and getattr(loader, "df", None) is not None

    def _verify_dedup(self):
        df = self._cleaner_df()
        return df is not None and not df.duplicated().any()

    def _verify_price_positive(self):
        df = self._cleaner_df()
        if df is None or "final_unit_price" not in df.columns:
            return False
        return int((pd.to_numeric(df["final_unit_price"], errors="coerce") <= 0).sum()) == 0

    def _verify_date_converted(self):
        df = self._cleaner_df()
        if df is None or "order_time" not in df.columns:
            return False
        return pd.api.types.is_datetime64_any_dtype(df["order_time"])

    def _verify_derived(self):
        df = self._cleaner_df()
        if df is None:
            return False
        # 派生成功的标志：出现了新列(默认名 TotalPrice)，或列数比原始多
        return ("TotalPrice" in df.columns) or (len(df.columns) > len(self._raw_cols))

    def _verify_mapped(self):
        return bool(getattr(self.app, "is_mapped", lambda: False)())

    def _verify_rfm_done(self):
        return getattr(self.app, "rfm_df", None) is not None

    def _verify_sales_done(self):
        return chart_group_complete(self.app, "sales")

    def _verify_product_done(self):
        return chart_group_complete(self.app, "product")

    def _verify_overview_done(self):
        return chart_group_complete(self.app, "overview")
