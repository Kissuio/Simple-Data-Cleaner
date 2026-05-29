"""所有子页面的公共基类（customtkinter 版本）。

为什么需要这个基类：
- 重构后所有子页面顶部都有「← 返回主页 + 标题 + 下一步 →」三件套
- 大部分子页面进入时要检查前置条件（loader / cleaner / rfm 是否就绪）
- 上面这些事抽到基类里只写一次

子类用法：
    class CleanerPage(BasePage):
        def __init__(self, master, app):
            super().__init__(
                master, app,
                title="数据清洗",
                requires="loader",
                next_page="RFM 分析",
            )
            self._build_body()

        def _build_body(self):
            ctk.CTkLabel(self.body, text="...").pack()

注意：HomePage（主页）不继承本类——主页本身就是"家"，不需要返回钮。
"""

import customtkinter as ctk


# 前置条件键 → 横幅提示文字 的映射
REQUIRE_HINTS = {
    "loader": "⚠ 尚未加载数据 —— 请回到主页选择「加载数据」",
    "cleaner": "⚠ 尚未完成清洗 —— 请回到主页选择「数据清洗」并执行【一键全清洗】",
    "rfm": "⚠ 尚未生成 RFM 结果 —— 请回到主页选择「RFM 分群」并执行【一键全分析】",
    "rfm+cleaner": "⚠ 数据未准备齐 —— 需要先完成「数据清洗」与「RFM 分群」",
}


class BasePage(ctk.CTkFrame):
    """子页面公共基类（继承自 customtkinter.CTkFrame）。

    构造参数：
        master:    父容器（window.py 的 container）
        app:       App 主窗口实例
        title:     页面标题（顶部条中央显示）
        requires:  前置条件键，可选 "loader" / "cleaner" / "rfm" / "rfm+cleaner" / None
        next_page: 流程上下一个模块的 key，传了就在右上角加「下一步 →」按钮
    """

    def __init__(self, master, app, title, requires=None, next_page=None):
        # fg_color=transparent 让 BasePage 跟随窗口默认色
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.app = app
        self.title_text = title
        self.requires = requires
        self.next_page = next_page
        self._build_header()

    def _build_header(self):
        """搭顶部条 + 提示横幅 + body 容器。"""
        theme = self.app.THEME

        # ───── 顶部条（白底）─────
        header = ctk.CTkFrame(
            self,
            fg_color=theme["header_bg"],
            corner_radius=0,
            height=60,
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)  # 阻止子 widget 改变 frame 高度

        # 「← 返回主页」按钮（左侧，深灰）
        back_btn = ctk.CTkButton(
            header,
            text="← 返回主页",
            command=lambda: self.app.show_page("主页"),
            fg_color=theme["back_fg"],
            hover_color=theme["back_hover"],
            text_color=theme["back_text"],
            font=("SimHei", 11, "bold"),
            width=110,
            height=32,
            corner_radius=6,
        )
        back_btn.pack(side="left", padx=15, pady=14)

        # 页面标题（左对齐，紧贴返回钮）
        title_label = ctk.CTkLabel(
            header,
            text=self.title_text,
            font=("SimHei", 16, "bold"),
            text_color=theme["title_fg"],
        )
        title_label.pack(side="left", padx=15)

        # 「下一步 →」按钮（右侧，亮蓝）——仅当 next_page 不为 None
        if self.next_page is not None:
            next_btn = ctk.CTkButton(
                header,
                text=f"下一步：{self.next_page} →",
                command=lambda: self.app.show_page(self.next_page),
                fg_color=theme["next_fg"],
                hover_color=theme["next_hover"],
                text_color=theme["next_text"],
                font=("SimHei", 11, "bold"),
                height=32,
                corner_radius=6,
            )
            next_btn.pack(side="right", padx=15, pady=14)

        # ───── 前置条件提示横幅（默认不显示）─────
        # 用 CTkLabel + fg_color 实现黄色横幅，进页面 + 不满足时由 on_show pack
        self.hint_label = ctk.CTkLabel(
            self,
            text="",
            font=("SimHei", 12, "bold"),
            fg_color=theme["hint_bg"],
            text_color=theme["hint_fg"],
            anchor="w",
            corner_radius=0,
            height=36,
        )
        # 不在这里 pack——等 on_show 决定

        # ───── 子类内容容器 ─────
        self.body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.body.pack(fill="both", expand=True)

    def on_show(self):
        """每次切换到本页面时由 App.show_page 调用。"""
        if self.requires is None:
            return

        if not self._check_requires():
            self.hint_label.configure(
                text="  " + REQUIRE_HINTS.get(self.requires, "⚠ 前置条件未满足")
            )
            self.hint_label.pack(fill="x", before=self.body)
        else:
            self.hint_label.pack_forget()

    def _check_requires(self):
        """根据 self.requires 检查 app 上对应数据是否已就绪。"""
        if self.requires == "loader":
            return (
                self.app.loader is not None
                and self.app.loader.df is not None
            )
        if self.requires == "cleaner":
            return (
                self.app.cleaner is not None
                and self.app.cleaner.df is not None
                and "TotalPrice" in self.app.cleaner.df.columns
            )
        if self.requires == "rfm":
            return (
                self.app.rfm_df is not None
                and "Label" in self.app.rfm_df.columns
            )
        if self.requires == "rfm+cleaner":
            cleaner_ok = (
                self.app.cleaner is not None
                and self.app.cleaner.df is not None
                and "TotalPrice" in self.app.cleaner.df.columns
            )
            rfm_ok = (
                self.app.rfm_df is not None
                and "Label" in self.app.rfm_df.columns
            )
            return cleaner_ok and rfm_ok
        return False
