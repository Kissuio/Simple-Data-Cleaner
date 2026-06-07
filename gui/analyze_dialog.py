"""「分析本页」弹窗：按当前所在页面生成一段「现成提示词」，含该页关键数据事实，
一键复制后丢给 ChatGPT / DeepSeek 等任意 AI 即可——不依赖 API key、不联网。

与 ai_dialog.py 的区别：那个是真接 API 解读图片；这里只产出「提示词文本」，
降低使用门槛（用户不一定有 API key）。
"""

from tkinter import messagebox

import customtkinter as ctk

from gui.widgets import BORDER_WIDTH, UI_COLORS as COLORS


# 每个页面（target = 左栏流程名）对应的提示词模板：开场 + 让 AI 做什么
PAGE_PROMPTS = {
    "加载数据": {
        "intro": "我在做一个电商客户 RFM 数据分析项目，刚加载了一份交易数据，准备做字段映射和清洗。",
        "ask": "请根据下面的数据概况：1) 判断这份数据是否适合做 RFM 分析、还缺哪些关键字段；"
               "2) 提示加载阶段要注意的问题（编码、字段含义等）。中文分点、简洁。",
    },
    "数据清洗": {
        "intro": "我在清洗一份电商交易数据，准备用于 RFM 客户分群。",
        "ask": "请根据下面的清洗前后情况：1) 评估数据质量、还可能有哪些脏数据；"
               "2) 建议还该做哪些清洗步骤（缺失、异常值、重复、取消单等）。中文分点。",
    },
    "RFM 分析": {
        "intro": "我用 RFM 模型（Recency 最近消费、Frequency 频次、Monetary 金额）对电商客户做了分群。",
        "ask": "请根据下面的 RFM 指标：1) 解读客户结构（高价值/潜力/流失风险等）；"
               "2) 给 3-5 条针对不同客群的可执行运营建议。中文分点。",
    },
    "销售分析": {
        "intro": "我在分析一份电商交易数据的销售情况（月度趋势、时段分布等）。",
        "ask": "请根据下面的销售概况：1) 指出销售趋势、季节性或时段规律；"
               "2) 给出提升销售的建议。中文分点。",
    },
    "商品分析": {
        "intro": "我在分析一份电商交易数据的商品表现（销量榜、销售额榜、单价分布）。",
        "ask": "请：1) 分析商品结构（爆款、长尾、价格带）；"
               "2) 给出选品、定价或组合销售的建议。中文分点。",
    },
    "图表总览": {
        "intro": "我做了一个电商 RFM 客户分析项目，涵盖客户分群、销售趋势、商品表现等多张图表。",
        "ask": "请根据下面的整体数据概况，给一份综合业务诊断 + 运营建议（客户、销售、商品三方面）。中文分点。",
    },
}

_DEFAULT = {
    "intro": "我在做一个电商客户 RFM 数据分析项目。",
    "ask": "请根据下面的数据概况给出业务洞察和运营建议。中文分点。",
}


def _collect_facts(app):
    """收集当前能拿到的数据事实（取不到的安静跳过，不报错）。"""
    lines = []
    loader = getattr(app, "loader", None)
    if loader is not None and getattr(loader, "df", None) is not None:
        df = loader.df
        lines.append(f"- 原始数据：{len(df):,} 行、{len(df.columns)} 列")

    cleaner = getattr(app, "cleaner", None)
    if cleaner is not None and getattr(cleaner, "df", None) is not None:
        lines.append(f"- 清洗后：{len(cleaner.df):,} 行")

    rfm = getattr(app, "rfm_df", None)
    if rfm is not None and "Label" in getattr(rfm, "columns", []):
        n = rfm["CustomerID"].nunique() if "CustomerID" in rfm.columns else len(rfm)
        lines.append(f"- RFM 客户数：{n:,}")
        labels = ["Recency", "Frequency", "Monetary"]
        names = {"Recency": "平均 Recency(天)", "Frequency": "平均 Frequency", "Monetary": "平均 Monetary"}
        for col in labels:
            if col in rfm.columns:
                lines.append(f"  · {names[col]}：{rfm[col].mean():,.1f}")
        if "Label" in rfm.columns:
            top = rfm["Label"].value_counts().head(3)
            parts = "；".join(f"{k} {v}人" for k, v in top.items())
            lines.append(f"- 主要客户分群：{parts}")
    return lines


def build_prompt(app, target):
    """拼出针对某页面的提示词：开场 + 当前数据事实 + 请 AI 做什么。"""
    tmpl = PAGE_PROMPTS.get(target, _DEFAULT)
    facts = _collect_facts(app)
    facts_block = "\n".join(facts) if facts else "（暂无数据，请先在「加载数据」加载文件、必要时完成清洗与分析）"
    return f"{tmpl['intro']}\n\n当前数据情况：\n{facts_block}\n\n{tmpl['ask']}"


class AnalyzeDialog(ctk.CTkToplevel):
    """显示当前页提示词的小窗：可编辑、一键复制。"""

    def __init__(self, master, app, target):
        super().__init__(master)
        self.title(f"分析本页 · {target}")
        self.geometry("560x520")
        self.configure(fg_color=COLORS["page_bg"])

        self._status = ctk.StringVar(value="")
        self._build(build_prompt(app, target))

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.transient(master)
        self.after(100, self._raise_to_front)

    def _raise_to_front(self):
        self.lift()
        self.focus_force()

    def _build(self, prompt):
        ctk.CTkLabel(
            self, text="把下面这段复制给 ChatGPT / DeepSeek 等 AI（可先改）：",
            font=("SimHei", 12, "bold"), text_color=COLORS["text"], anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 6))

        # 底部按钮先钉底，保证文本再长也始终可见
        action = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        action.pack(side="bottom", fill="x", padx=20, pady=(4, 14))
        ctk.CTkButton(
            action, text="复制", command=self._copy,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            font=("SimHei", 13, "bold"), height=38, width=120, corner_radius=6,
        ).pack(side="left")
        ctk.CTkLabel(
            action, textvariable=self._status, font=("SimHei", 11),
            text_color=COLORS["green"],
        ).pack(side="left", padx=12)
        ctk.CTkButton(
            action, text="关闭", command=self.destroy,
            fg_color=COLORS["gray"], hover_color=COLORS["gray_hover"],
            font=("SimHei", 12, "bold"), height=38, width=90, corner_radius=6,
        ).pack(side="right")

        self.box = ctk.CTkTextbox(
            self, font=("SimHei", 12), fg_color="#ffffff", text_color=COLORS["text"],
            border_color=COLORS["border"], border_width=BORDER_WIDTH, corner_radius=8,
            wrap="word",
        )
        self.box.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 10))
        self.box.insert("1.0", prompt)

    def _copy(self):
        text = self.box.get("1.0", "end").strip()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self._status.set("✓ 已复制到剪贴板")
