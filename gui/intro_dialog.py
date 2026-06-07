"""分析方法引导说明窗（进入分析页时弹出，讲清「这是什么分析、需要哪些数据」）。

与其它弹窗的区别：
- mapping_dialog 是「让用户选列」的操作窗；
- analyze_dialog 是「生成给 AI 的提示词」；
- 本窗只做**讲解**：一段只读说明文本 + 一个「知道了，开始」按钮，
  关闭后通过 on_close 回调把控制权交还调用方（如接着弹字段映射）。

通用设计：标题 + 正文文本由调用方传入，便于以后给销售/商品页复用。
"""

import customtkinter as ctk

from gui.widgets import BORDER_WIDTH, UI_COLORS as COLORS


class IntroDialog(ctk.CTkToplevel):
    """分析说明引导窗（模态）。

    参数:
        master:    父窗口
        title:     窗口与顶部标题文字
        body:      说明正文（多行字符串，只读展示）
        on_close:  关闭（点「知道了」或 X）后的回调，签名 on_close()，可选
                   ——常用于「讲完接着弹字段映射」。
    """

    def __init__(self, master, title, body, on_close=None):
        super().__init__(master)
        self.on_close_cb = on_close
        self.title(title)
        self.geometry("600x600")
        self.configure(fg_color=COLORS["page_bg"])

        self._build(title, body)

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.transient(master)
        self.after(100, self._raise_to_front)
        self.grab_set()

    def _raise_to_front(self):
        self.lift()
        self.focus_force()

    def _build(self, title, body):
        ctk.CTkLabel(
            self, text=title, font=("SimHei", 16, "bold"),
            text_color=COLORS["text"], anchor="w",
        ).pack(fill="x", padx=22, pady=(18, 8))

        # 底部按钮先钉底，保证正文再长也始终可见
        action = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        action.pack(side="bottom", fill="x", padx=22, pady=(4, 16))
        ctk.CTkButton(
            action, text="知道了，开始", command=self._close,
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            font=("SimHei", 13, "bold"), height=38, width=150, corner_radius=6,
        ).pack(side="right")

        box = ctk.CTkTextbox(
            self, font=("SimHei", 13), fg_color="#ffffff", text_color=COLORS["text"],
            border_color=COLORS["border"], border_width=BORDER_WIDTH, corner_radius=8,
            wrap="word",
        )
        box.pack(side="top", fill="both", expand=True, padx=22, pady=(0, 10))
        box.insert("1.0", body)
        box.configure(state="disabled")  # 只读

    def _close(self):
        self.grab_release()
        self.destroy()
        if self.on_close_cb is not None:
            self.on_close_cb()
