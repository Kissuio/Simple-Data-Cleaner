"""AI 解读独立窗口（OverviewPage 的【AI 解读】按钮点击后弹出）。

设计：
- 通过 OpenAI 兼容协议接入任意 AI 服务（OpenAI/DeepSeek/Moonshot/智谱/自定义）
- 用户填 base_url + api_key + model，API Key 不存盘
- 图片来源：项目 8 张图（顺序逐张解读）或自定义上传一张
- Prompt 模板可编辑

依赖：openai SDK（pip install openai）
"""

import base64
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
import tkinter as tk


# 预设的 OpenAI 兼容服务商 base_url
PROVIDERS = {
    "OpenAI": "https://api.openai.com/v1",
    "DeepSeek": "https://api.deepseek.com/v1",
    "Moonshot": "https://api.moonshot.cn/v1",
    "智谱清言": "https://open.bigmodel.cn/api/paas/v4",
    "自定义": "",
}

DEFAULT_PROMPT = (
    "这是一张电商客户分析项目里的图表。\n"
    "请用中文给出：\n"
    "1. 3-5 条业务洞察（图上能看出的现象 / 规律 / 异常）\n"
    "2. 2-3 条运营建议（针对洞察提出可执行的动作）\n"
    "500 字以内，分点清晰。"
)

# 项目 8 张图清单（和 OverviewPage 保持一致）
CHARTS = [
    ("饼图", "label_pie.png"),
    ("柱图", "label_avg_spend.png"),
    ("RFM 散点", "rfm_scatter.png"),
    ("月度趋势", "monthly_trend.png"),
    ("TOP10 销量", "top_quantity.png"),
    ("TOP10 销售额", "top_revenue.png"),
    ("单价分布", "price_distribution.png"),
    ("周热力图", "weekday_hour_heatmap.png"),
]


class AIDialog(tk.Toplevel):
    """AI 解读独立窗口。"""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("AI 解读")
        self.geometry("900x800")

        # 自传图的路径（自定义模式下）
        self.custom_image_path = None

        self._build_ui()

    def _build_ui(self):
        # ───── AI 配置区 ─────
        config_frame = ttk.LabelFrame(self, text="AI 配置", padding=10)
        config_frame.pack(fill="x", padx=10, pady=(10, 5))

        # AI 供应商
        row = ttk.Frame(config_frame); row.pack(fill="x", pady=2)
        ttk.Label(row, text="AI 供应商:", width=12).pack(side="left")
        self.provider_var = tk.StringVar(value="OpenAI")
        combo = ttk.Combobox(
            row, textvariable=self.provider_var,
            values=list(PROVIDERS.keys()), state="readonly", width=15,
        )
        combo.pack(side="left", padx=5)
        combo.bind("<<ComboboxSelected>>", self._on_provider_change)

        # Base URL
        row = ttk.Frame(config_frame); row.pack(fill="x", pady=2)
        ttk.Label(row, text="Base URL:", width=12).pack(side="left")
        self.base_url_var = tk.StringVar(value=PROVIDERS["OpenAI"])
        ttk.Entry(row, textvariable=self.base_url_var).pack(
            side="left", padx=5, fill="x", expand=True
        )

        # API Key（show="*" 显示成密文）
        row = ttk.Frame(config_frame); row.pack(fill="x", pady=2)
        ttk.Label(row, text="API Key:", width=12).pack(side="left")
        self.api_key_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.api_key_var, show="*").pack(
            side="left", padx=5, fill="x", expand=True
        )

        # Model
        row = ttk.Frame(config_frame); row.pack(fill="x", pady=2)
        ttk.Label(row, text="Model:", width=12).pack(side="left")
        self.model_var = tk.StringVar(value="gpt-4o-mini")
        ttk.Entry(row, textvariable=self.model_var, width=30).pack(side="left", padx=5)
        ttk.Label(
            row, text="（需 vision 模型，如 gpt-4o / moonshot-v1-8k-vision-preview）",
            foreground="gray",
        ).pack(side="left", padx=5)

        # ───── 图片来源 ─────
        source_frame = ttk.LabelFrame(self, text="图片来源", padding=10)
        source_frame.pack(fill="x", padx=10, pady=5)
        self.source_var = tk.StringVar(value="all8")
        ttk.Radiobutton(
            source_frame, text="一键分析项目 8 张图（顺序逐张解读）",
            variable=self.source_var, value="all8",
        ).pack(anchor="w", pady=2)
        custom_row = ttk.Frame(source_frame); custom_row.pack(fill="x", pady=2)
        ttk.Radiobutton(
            custom_row, text="上传自定义图：",
            variable=self.source_var, value="custom",
        ).pack(side="left")
        ttk.Button(custom_row, text="选择图片...", command=self._on_pick_image).pack(
            side="left", padx=5
        )
        self.custom_label_var = tk.StringVar(value="（未选择）")
        ttk.Label(custom_row, textvariable=self.custom_label_var, foreground="gray").pack(
            side="left", padx=5
        )

        # ───── Prompt 模板 ─────
        prompt_frame = ttk.LabelFrame(self, text="Prompt 模板（可编辑）", padding=10)
        prompt_frame.pack(fill="x", padx=10, pady=5)
        self.prompt_text = tk.Text(prompt_frame, height=5, font=("SimHei", 10), wrap="word")
        self.prompt_text.pack(fill="x")
        self.prompt_text.insert("1.0", DEFAULT_PROMPT)

        # ───── 操作按钮 ─────
        action_frame = ttk.Frame(self); action_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(
            action_frame, text="开始解读", command=self._on_start,
            style="Action.TButton",
        ).pack(side="left")
        ttk.Button(
            action_frame, text="导出 AI 建议", command=self._on_export_result,
            style="Action.TButton",
        ).pack(side="right")
        self.progress_var = tk.StringVar(value="")
        ttk.Label(action_frame, textvariable=self.progress_var, foreground="gray").pack(
            side="left", padx=10
        )

        # ───── AI 返回区 ─────
        result_frame = ttk.LabelFrame(self, text="AI 返回", padding=10)
        result_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self.result_text = tk.Text(result_frame, font=("SimHei", 11), wrap="word")
        scrollbar = ttk.Scrollbar(
            result_frame, orient="vertical", command=self.result_text.yview
        )
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ───── 回调 ─────

    def _on_provider_change(self, event=None):
        """选了供应商，自动填默认 base_url。"""
        provider = self.provider_var.get()
        self.base_url_var.set(PROVIDERS.get(provider, ""))

    def _on_pick_image(self):
        """选自定义图片。"""
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[
                ("PNG 图片", "*.png"),
                ("JPG 图片", "*.jpg *.jpeg"),
                ("所有图片", "*.png *.jpg *.jpeg"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        self.custom_image_path = path
        self.custom_label_var.set(Path(path).name)
        # 自动切到"自定义"模式
        self.source_var.set("custom")

    def _on_start(self):
        """点击开始解读：校验 → 调 API → 显示结果。"""
        api_key = self.api_key_var.get().strip()
        base_url = self.base_url_var.get().strip()
        model = self.model_var.get().strip()
        prompt = self.prompt_text.get("1.0", "end").strip()

        # 输入校验
        if not api_key:
            messagebox.showwarning("缺少 API Key", "请填入 AI 服务商的 API Key。")
            return
        if not base_url:
            messagebox.showwarning("缺少 Base URL", "请填入 AI 服务的 Base URL。")
            return
        if not model:
            messagebox.showwarning("缺少 Model", "请填入要使用的模型名。")
            return
        if not prompt:
            messagebox.showwarning("缺少 Prompt", "请填入 Prompt 模板。")
            return

        # 确定图片列表
        if self.source_var.get() == "all8":
            images = [
                (name, f"output/{fname}")
                for name, fname in CHARTS
                if Path(f"output/{fname}").exists()
            ]
            if not images:
                messagebox.showwarning(
                    "8 张图未生成",
                    "请先在【图表总览】点【一键生成所有 8 张图】。",
                )
                return
        else:
            if not self.custom_image_path:
                messagebox.showwarning(
                    "未选择图片", "请先点【选择图片...】选定要解读的图。"
                )
                return
            images = [(Path(self.custom_image_path).name, self.custom_image_path)]

        # 清空返回区
        self.result_text.delete("1.0", "end")

        # 初始化 OpenAI client
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            messagebox.showerror("初始化失败", f"无法创建 OpenAI client：\n{e}")
            return

        # 逐张调 API（同步，用 update_idletasks 让用户看到进度）
        for i, (name, path) in enumerate(images, 1):
            self.progress_var.set(f"正在处理 {i}/{len(images)}: {name}...")
            self.update_idletasks()

            try:
                # 编码图片为 base64
                with open(path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode("utf-8")
                data_url = f"data:image/png;base64,{img_b64}"

                # 调 API（OpenAI 兼容协议，content 是 list 时支持 vision）
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"图名：{name}\n\n{prompt}"},
                                {"type": "image_url", "image_url": {"url": data_url}},
                            ],
                        }
                    ],
                )
                content = response.choices[0].message.content
            except Exception as e:
                content = f"[调用失败] {type(e).__name__}: {e}"

            # 追加到结果区，并滚到底部
            self.result_text.insert(
                "end", f"\n{'=' * 60}\n【{name}】\n{'=' * 60}\n\n{content}\n"
            )
            self.result_text.see("end")
            self.update_idletasks()

        self.progress_var.set(f"完成（共 {len(images)} 张图）")

    def _on_export_result(self):
        """导出 AI 返回内容到 .md / .txt 文件。"""
        content = self.result_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("无内容", "AI 还没返回任何内容，无法导出。")
            return
        path = filedialog.asksaveasfilename(
            title="导出 AI 建议",
            defaultextension=".md",
            filetypes=[
                ("Markdown 文件", "*.md"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*"),
            ],
            initialfile="AI 解读结果.md",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return
        messagebox.showinfo("已导出", f"已保存到：\n{path}")
