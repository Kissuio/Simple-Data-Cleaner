"""「AI 分析本页」弹窗：截取当前程序窗口快照（存到 output/），并可再上传任意图片，
每张图各自配一段提示词，像图表总览的 AI 解读一样选模型逐张提交 Vision 模型分析。

与 ai_dialog.py 的关系：
- ai_dialog 解读【图表总览】里项目生成的 9 张图（共用一段提示词，逐张）；
- 本弹窗解读【当前页程序截图 + 用户自己上传的图】，每张图提示词独立、可分别编辑。

无 API Key 退路：每张图卡片上都有「复制提示词」，把该图对应的提示词复制走，
连同图片发给任意 AI；本页截图的提示词按当前页 + 当前数据生成，每页不同。

依赖：openai SDK（提交分析时）、pillow 的 ImageGrab（截图）与 Image（缩略图）。
"""

import base64
import time
from pathlib import Path
from tkinter import messagebox, filedialog

import customtkinter as ctk
from PIL import Image, ImageGrab

from gui.ai_dialog import PROVIDERS
from gui.error_messages import friendly_error_message, show_friendly_error
from gui.widgets import BORDER_WIDTH, UI_COLORS as COLORS


# 页面（左栏流程名）→ 截图文件名用的英文短名（避免中文文件名）
PAGE_SLUG = {
    "主页": "home", "加载数据": "load", "数据清洗": "clean", "RFM 分析": "rfm",
    "销售分析": "sales", "商品分析": "product", "图表总览": "overview",
}

# 每个页面对应的提示词模板：开场 + 让 AI 做什么（结合截图与数据事实）
PAGE_PROMPTS = {
    "加载数据": {
        "intro": "下图是「加载数据」页面的程序截图，我刚加载了一份电商交易数据。",
        "ask": "请结合截图与下面的数据概况：1) 判断是否适合做 RFM 分析、还缺哪些关键字段；"
               "2) 提示加载阶段要注意的问题（编码、字段含义等）。中文分点、简洁。",
    },
    "数据清洗": {
        "intro": "下图是「数据清洗」页面的程序截图，我正在清洗一份交易数据用于 RFM 分群。",
        "ask": "请结合截图与下面的清洗前后情况：1) 评估数据质量、还可能有哪些脏数据；"
               "2) 建议还该做哪些清洗步骤（缺失、异常值、重复、取消单等）。中文分点。",
    },
    "RFM 分析": {
        "intro": "下图是「RFM 分析」页面的程序截图，我用 RFM 模型对客户做了分群。",
        "ask": "请结合截图与下面的 RFM 指标：1) 解读客户结构（高价值/潜力/流失风险等）；"
               "2) 给 3-5 条针对不同客群的可执行运营建议。中文分点。",
    },
    "销售分析": {
        "intro": "下图是「销售分析」页面的程序截图，含月度趋势、时段分布等图表。",
        "ask": "请结合截图与下面的销售概况：1) 指出销售趋势、季节性或时段规律；"
               "2) 给出提升销售的建议。中文分点。",
    },
    "商品分析": {
        "intro": "下图是「商品分析」页面的程序截图，含销量榜、销售额榜、单价分布。",
        "ask": "请结合截图与下面的商品概况：1) 分析商品结构（爆款、长尾、价格带）；"
               "2) 给出选品、定价或组合销售的建议。中文分点。",
    },
    "图表总览": {
        "intro": "下图是「图表总览」页面的程序截图，汇总了客户分群、销售、商品等多张图表。",
        "ask": "请结合截图与下面的整体数据概况，给综合业务诊断 + 运营建议（客户、销售、商品）。中文分点。",
    },
}

_DEFAULT_PROMPT = {
    "intro": "下图是我的电商客户 RFM 数据分析项目的程序截图。",
    "ask": "请结合截图与下面的数据概况，给出业务洞察和运营建议。中文分点。",
}

# 用户自行上传图片时的默认提示词（每张可单独改）
UPLOAD_PROMPT = (
    "这是一张电商客户分析相关的图表/截图。请用中文给出：\n"
    "1) 3-5 条业务洞察（图上的现象 / 规律 / 异常）；\n"
    "2) 2-3 条可执行运营建议。500 字以内，分点清晰。"
)


def _fmt_int(x):
    try:
        return f"{int(x):,}"
    except Exception:
        return str(x)


def _collect_facts(app, target):
    """收集「当前页 + 当前数据」的事实，按页补充专属指标（取不到的安静跳过）。

    这是「每页提示词不同、根据数据说话」的关键：通用事实之外，
    销售页带月度峰值、商品页带 TOP 商品、RFM 页带分群分布。
    """
    lines = []
    loader = getattr(app, "loader", None)
    if loader is not None and getattr(loader, "df", None) is not None:
        df = loader.df
        lines.append(f"- 原始数据：{_fmt_int(len(df))} 行、{len(df.columns)} 列")
    cleaner = getattr(app, "cleaner", None)
    if cleaner is not None and getattr(cleaner, "df", None) is not None:
        lines.append(f"- 清洗后：{_fmt_int(len(cleaner.df))} 行")

    rfm = getattr(app, "rfm_df", None)
    has_rfm = rfm is not None and "Label" in getattr(rfm, "columns", [])

    active = None
    try:
        if hasattr(app, "is_mapped") and app.is_mapped():
            active = app.get_active_df()
    except Exception:
        active = None

    if target in ("RFM 分析", "图表总览") and has_rfm:
        n = rfm["CustomerID"].nunique() if "CustomerID" in rfm.columns else len(rfm)
        lines.append(f"- RFM 客户数：{_fmt_int(n)}")
        for col, name in (("Recency", "平均 Recency(天)"),
                          ("Frequency", "平均 Frequency"),
                          ("Monetary", "平均 Monetary")):
            if col in rfm.columns:
                lines.append(f"  · {name}：{rfm[col].mean():,.1f}")
        top = rfm["Label"].value_counts().head(4)
        lines.append("- 主要客户分群：" + "；".join(f"{k} {_fmt_int(v)}人" for k, v in top.items()))

    if target in ("销售分析", "图表总览") and active is not None:
        try:
            from analyzer.sales_trend import get_monthly_sales
            m = get_monthly_sales(active)
            if len(m):
                lines.append(
                    f"- 月度销售：覆盖 {m.index[0]}~{m.index[-1]}，"
                    f"最高 {m.idxmax()}（约 {m.max():,.0f}）、最低 {m.idxmin()}（约 {m.min():,.0f}）"
                )
        except Exception:
            pass

    if target in ("商品分析", "图表总览") and active is not None:
        try:
            from analyzer.product_analysis import get_top_quantity, get_top_revenue
            tq = get_top_quantity(active, n=3)
            tr = get_top_revenue(active, n=3)
            if len(tq):
                lines.append("- 销量 TOP3：" + "；".join(f"{k}（{v:,.0f} 件）" for k, v in tq.items()))
            if len(tr):
                lines.append("- 销售额 TOP3：" + "；".join(f"{k}（约 {v:,.0f}）" for k, v in tr.items()))
        except Exception:
            pass

    return lines


def build_prompt(app, target):
    """拼出针对「当前页 + 当前数据」的提示词：开场 + 当前数据事实 + 请 AI 做什么。"""
    tmpl = PAGE_PROMPTS.get(target, _DEFAULT_PROMPT)
    facts = _collect_facts(app, target)
    facts_block = "\n".join(facts) if facts else "（暂无数据，请先加载文件、必要时完成清洗与分析）"
    return f"{tmpl['intro']}\n\n当前数据情况：\n{facts_block}\n\n{tmpl['ask']}"


class AnalyzeDialog(ctk.CTkToplevel):
    """「AI 分析本页」窗口：本页截图 + 可上传多图，每图独立提示词，选模型逐张解读。"""

    def __init__(self, master, app, target):
        super().__init__(master)
        self.app = app
        self.target = target
        self.withdraw()  # 先隐藏自己，避免本窗口出现在截图里

        self.title(f"AI 分析本页 · {target}")
        self.geometry("920x860")
        self.configure(fg_color=COLORS["page_bg"])

        self.cards = []            # 每张图：{path, name, kind, prompt, thumb, frame, _img}
        self.snapshot_card = None

        self._build_ui()

        # 截当前页快照并作为第一张图加入
        snap = self._capture()
        if snap is not None:
            self.snapshot_card = self._add_card(
                snap, kind="snapshot", name="① 本页截图",
                default_prompt=build_prompt(app, target),
            )

        self.deiconify()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.transient(master)
        self.after(100, self._raise_to_front)

    def _raise_to_front(self):
        self.lift()
        self.focus_force()

    # ───── 截图 ─────

    def _snapshot_dir(self):
        d = Path(self.app.output_picture_dir()) / "snapshots"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _grab_program(self):
        """本窗口须先 withdraw；让主窗口到前台、等屏幕真正重绘后再抓全屏。"""
        self.app.lift()
        self.app.update_idletasks()
        self.app.update()
        # 关键：等本弹窗真正从屏幕消失、桌面重绘完成，否则会把弹窗自己拍进去
        time.sleep(0.4)
        self.app.update()
        return ImageGrab.grab()

    def _capture(self):
        """截整个程序窗口（已最大化≈全屏），存到 output/.../snapshots/。"""
        try:
            img = self._grab_program()
            ts = time.strftime("%Y%m%d_%H%M%S")
            slug = PAGE_SLUG.get(self.target, "page")
            path = self._snapshot_dir() / f"{slug}_{ts}.png"
            img.save(path)
            return path
        except Exception as e:
            show_friendly_error("截图失败", e, "截取程序快照", parent=self)
            return None

    def _on_recapture(self):
        """重新截图：先隐藏本窗口并等其消失，截完再显示，只更新截图卡片的图与路径。"""
        if self.snapshot_card is None:
            return
        self.withdraw()
        self.update()
        time.sleep(0.05)
        path = self._capture()
        self.deiconify()
        self._raise_to_front()
        if path is not None:
            self.snapshot_card["path"] = path
            self._load_thumb(self.snapshot_card)

    # ───── 图片卡片 ─────

    def _load_thumb(self, card):
        try:
            img = Image.open(card["path"])
            w, h = img.size
            tw = 170
            th = max(1, int(h * tw / w))
            card["_img"] = ctk.CTkImage(light_image=img, size=(tw, th))
            card["thumb"].configure(image=card["_img"], text="")
        except Exception:
            card["thumb"].configure(text="（预览不可用）", image=None)

    def _add_card(self, path, kind, name, default_prompt):
        frame = ctk.CTkFrame(
            self.image_list, fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"], border_width=BORDER_WIDTH, corner_radius=8,
        )
        frame.pack(fill="x", padx=8, pady=6)

        thumb = ctk.CTkLabel(frame, text="（加载中）", width=170, text_color=COLORS["muted"])
        thumb.pack(side="left", padx=10, pady=10)

        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)
        ctk.CTkLabel(
            right, text=f"{name}　·　{Path(path).name}", font=("SimHei", 11, "bold"),
            text_color=COLORS["text"], anchor="w",
        ).pack(fill="x")

        pbox = ctk.CTkTextbox(
            right, height=84, font=("SimHei", 10), fg_color="#ffffff", text_color=COLORS["text"],
            border_color=COLORS["border"], border_width=BORDER_WIDTH, corner_radius=6, wrap="word",
        )
        pbox.pack(fill="x", pady=(4, 4))
        self._bind_textbox_wheel_guard(pbox)
        pbox.insert("1.0", default_prompt)

        card = {"path": path, "name": name, "kind": kind, "prompt": pbox,
                "thumb": thumb, "frame": frame, "_img": None}

        btnrow = ctk.CTkFrame(right, fg_color="transparent")
        btnrow.pack(fill="x")
        ctk.CTkButton(
            btnrow, text="复制提示词", width=92, height=26, corner_radius=6,
            fg_color=COLORS["gray"], hover_color=COLORS["gray_hover"], font=("SimHei", 10),
            command=lambda c=card: self._copy_card(c),
        ).pack(side="left")
        if kind == "snapshot":
            ctk.CTkButton(
                btnrow, text="重新截图", width=92, height=26, corner_radius=6,
                fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"], font=("SimHei", 10),
                command=self._on_recapture,
            ).pack(side="left", padx=6)
        else:
            ctk.CTkButton(
                btnrow, text="移除", width=70, height=26, corner_radius=6,
                fg_color=COLORS["gray"], hover_color=COLORS["gray_hover"], font=("SimHei", 10),
                command=lambda c=card: self._remove_card(c),
            ).pack(side="left", padx=6)

        self.cards.append(card)
        self._load_thumb(card)
        return card

    def _remove_card(self, card):
        try:
            card["frame"].destroy()
        except Exception:
            pass
        if card in self.cards:
            self.cards.remove(card)

    def _copy_card(self, card):
        text = card["prompt"].get("1.0", "end").strip()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.progress_var.set(f"✓ 已复制「{card['name']}」的提示词")

    def _on_upload(self):
        paths = filedialog.askopenfilenames(
            title="选择图片（可多选）",
            filetypes=[("图片", "*.png *.jpg *.jpeg"), ("所有文件", "*.*")],
        )
        for p in paths:
            n = len([c for c in self.cards if c["kind"] == "upload"]) + 1
            self._add_card(p, kind="upload", name=f"上传图 {n}", default_prompt=UPLOAD_PROMPT)

    # ───── UI ─────

    def _make_section_frame(self, parent, title):
        outer = ctk.CTkFrame(
            parent, fg_color=COLORS["panel_bg"],
            border_color=COLORS["border"], border_width=BORDER_WIDTH, corner_radius=8,
        )
        ctk.CTkLabel(
            outer, text=title, font=("SimHei", 11, "bold"),
            text_color=COLORS["muted"], anchor="w",
        ).pack(fill="x", padx=15, pady=(8, 0))
        return outer

    def _bind_textbox_wheel_guard(self, textbox):
        """让文本框只滚动自己，避免同时触发外层截图弹窗滚动条。"""
        text_widget = getattr(textbox, "_textbox", textbox)

        def _scroll_text(event):
            delta = getattr(event, "delta", 0)
            if delta:
                units = -int(delta / 120)
                if units == 0:
                    units = -1 if delta > 0 else 1
            else:
                units = -1 if getattr(event, "num", None) == 4 else 1
            text_widget.yview_scroll(units, "units")
            return "break"

        scrollbar = getattr(textbox, "_scrollbar", None)
        for target in (textbox, text_widget, scrollbar):
            if target is None:
                continue
            target.bind("<MouseWheel>", _scroll_text)
            target.bind("<Button-4>", _scroll_text)
            target.bind("<Button-5>", _scroll_text)

    def _build_ui(self):
        root = ctk.CTkScrollableFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True)

        # ── AI 配置 ──
        config = self._make_section_frame(root, "AI 配置")
        config.pack(fill="x", padx=15, pady=(15, 8))

        row = ctk.CTkFrame(config, fg_color="transparent"); row.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(row, text="AI 供应商:", width=80, anchor="w", font=("SimHei", 11)).pack(side="left")
        self.provider_var = ctk.StringVar(value="OpenAI")
        ctk.CTkOptionMenu(
            row, variable=self.provider_var, values=list(PROVIDERS.keys()),
            command=self._on_provider_change, font=("SimHei", 11), width=160,
        ).pack(side="left", padx=5)

        row = ctk.CTkFrame(config, fg_color="transparent"); row.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(row, text="Base URL:", width=80, anchor="w", font=("SimHei", 11)).pack(side="left")
        self.base_url_var = ctk.StringVar(value=PROVIDERS["OpenAI"])
        ctk.CTkEntry(row, textvariable=self.base_url_var, font=("SimHei", 11)).pack(side="left", padx=5, fill="x", expand=True)

        row = ctk.CTkFrame(config, fg_color="transparent"); row.pack(fill="x", padx=15, pady=4)
        ctk.CTkLabel(row, text="API Key:", width=80, anchor="w", font=("SimHei", 11)).pack(side="left")
        self.api_key_var = ctk.StringVar()
        ctk.CTkEntry(row, textvariable=self.api_key_var, font=("SimHei", 11), show="*").pack(side="left", padx=5, fill="x", expand=True)

        row = ctk.CTkFrame(config, fg_color="transparent"); row.pack(fill="x", padx=15, pady=(4, 10))
        ctk.CTkLabel(row, text="Model:", width=80, anchor="w", font=("SimHei", 11)).pack(side="left")
        self.model_var = ctk.StringVar(value="gpt-4o-mini")
        ctk.CTkEntry(row, textvariable=self.model_var, font=("SimHei", 11), width=280).pack(side="left", padx=5)
        ctk.CTkLabel(row, text="（需 vision 模型，如 gpt-4o / moonshot-v1-8k-vision-preview）",
                     text_color=COLORS["muted"], font=("SimHei", 10)).pack(side="left", padx=5)

        # ── 待分析图像（每张图独立提示词）──
        imgs = self._make_section_frame(root, "待分析图像（每张图的提示词可单独编辑）")
        imgs.pack(fill="both", expand=True, padx=15, pady=8)
        bar = ctk.CTkFrame(imgs, fg_color="transparent"); bar.pack(fill="x", padx=15, pady=(6, 2))
        ctk.CTkButton(
            bar, text="＋ 上传图片", command=self._on_upload,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            font=("SimHei", 11), height=30, width=120, corner_radius=6,
        ).pack(side="left")
        ctk.CTkLabel(bar, text="（本页截图已自动加入；可继续上传更多图，逐张解读）",
                     text_color=COLORS["muted"], font=("SimHei", 10)).pack(side="left", padx=10)
        self.image_list = ctk.CTkFrame(imgs, fg_color="transparent")
        self.image_list.pack(fill="both", expand=True, padx=6, pady=(2, 10))

        # ── 操作 ──
        action = ctk.CTkFrame(root, fg_color="transparent"); action.pack(fill="x", padx=15, pady=8)
        ctk.CTkButton(
            action, text="开始解读（逐张）", command=self._on_start,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            font=("SimHei", 12, "bold"), height=36, width=150, corner_radius=6,
        ).pack(side="left")
        self.progress_var = ctk.StringVar(value="")
        ctk.CTkLabel(action, textvariable=self.progress_var, text_color=COLORS["muted"], font=("SimHei", 11)).pack(side="left", padx=12)
        ctk.CTkButton(
            action, text="导出 AI 建议", command=self._on_export_result,
            fg_color=COLORS["green"], hover_color=COLORS["green_hover"],
            font=("SimHei", 12, "bold"), height=36, width=140, corner_radius=6,
        ).pack(side="right")

        # ── AI 返回 ──
        result_frame = self._make_section_frame(root, "AI 返回")
        result_frame.pack(fill="both", expand=True, padx=15, pady=(8, 15))
        self.result_text = ctk.CTkTextbox(
            result_frame, height=200, font=("SimHei", 11), fg_color="#ffffff", text_color=COLORS["text"],
            border_color=COLORS["border"], border_width=BORDER_WIDTH, corner_radius=6, wrap="word",
        )
        self.result_text.pack(fill="both", expand=True, padx=15, pady=(8, 12))
        self._bind_textbox_wheel_guard(self.result_text)

    # ───── 回调 ─────

    def _on_provider_change(self, choice=None):
        self.base_url_var.set(PROVIDERS.get(self.provider_var.get(), ""))

    def _on_start(self):
        """逐张提交：每张图用它自己的提示词 + 图片 → Vision 模型解读。"""
        if not self.cards:
            messagebox.showwarning("没有图片", "请先截图或上传至少一张图片。", parent=self)
            return
        api_key = self.api_key_var.get().strip()
        base_url = self.base_url_var.get().strip()
        model = self.model_var.get().strip()
        if not api_key:
            messagebox.showwarning("缺少 API Key", "请填入 API Key（没有可用每张图的「复制提示词」）。", parent=self)
            return
        if not base_url or not model:
            messagebox.showwarning("缺少配置", "请填入 Base URL 与 Model。", parent=self)
            return

        self.result_text.delete("1.0", "end")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            show_friendly_error("初始化失败", e, "连接 AI 服务", parent=self)
            return

        total = len(self.cards)
        for i, card in enumerate(list(self.cards), 1):
            name = card["name"]
            prompt = card["prompt"].get("1.0", "end").strip()
            self.progress_var.set(f"正在解读 {i}/{total}：{name} ...")
            self.update_idletasks()
            try:
                with open(card["path"], "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode("utf-8")
                data_url = f"data:image/png;base64,{img_b64}"
                response = client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }],
                )
                content = response.choices[0].message.content
            except Exception as e:
                content = friendly_error_message(e, action=f"解读「{name}」")
            self.result_text.insert("end", f"\n{'=' * 56}\n【{name}】\n{'=' * 56}\n\n{content}\n")
            self.result_text.see("end")
            self.update_idletasks()

        self.progress_var.set(f"完成（共 {total} 张）")

    def _on_export_result(self):
        content = self.result_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("无内容", "AI 还没返回任何内容，无法导出。", parent=self)
            return
        path = filedialog.asksaveasfilename(
            title="导出 AI 建议", defaultextension=".md",
            filetypes=[("Markdown 文件", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"AI 分析_{self.target}.md",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            show_friendly_error("保存失败", e, "保存 AI 分析结果", parent=self)
            return
        messagebox.showinfo("已导出", f"已保存到：\n{path}", parent=self)
