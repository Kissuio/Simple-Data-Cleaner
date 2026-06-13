"""把底层异常转换成用户能直接照着处理的中文提示。"""

import re
from tkinter import messagebox


def _contains_chinese(text):
    """判断文本中是否包含中文字符。"""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _short_reason(raw):
    """保留简短中文业务错误，过滤冗长的底层技术信息。"""
    raw = " ".join(str(raw).split())
    if raw and len(raw) <= 180 and _contains_chinese(raw):
        return raw
    return ""


def friendly_error_message(error, action="当前操作"):
    """将异常翻译为“发生了什么 + 怎么处理”的通俗中文。

    Args:
        error: 捕获到的异常对象。
        action: 用户刚才执行的动作，如“读取数据文件”。

    Returns:
        可直接显示在错误对话框中的中文提示。
    """
    raw = str(error).strip()
    kind = type(error).__name__
    text = f"{kind} {raw}".lower()
    reason = ""
    suggestions = []

    if isinstance(error, FileNotFoundError) or "no such file" in text:
        reason = "没有找到需要的文件，文件可能被移动、改名或删除了。"
        suggestions = ["重新选择文件。", "确认文件路径和文件名没有变化。"]
    elif isinstance(error, PermissionError) or "permission denied" in text:
        reason = "程序没有权限读取或保存这个文件，文件也可能正被其他软件占用。"
        suggestions = ["关闭正在打开该文件的 Excel、图片查看器等软件。", "换一个有写入权限的位置后重试。"]
    elif isinstance(error, MemoryError) or "out of memory" in text:
        reason = "数据或图片太大，当前可用内存不足。"
        suggestions = ["先关闭其他占用内存较多的软件。", "减少数据量或分批处理后重试。"]
    elif isinstance(error, UnicodeDecodeError) or "codec can't decode" in text:
        reason = "文件的文字编码无法识别，常见于 CSV 不是 UTF-8 编码。"
        suggestions = ["用 Excel 重新另存为 UTF-8 CSV。", "也可以改用 XLSX 格式再导入。"]
    elif isinstance(error, KeyError) or "not in index" in text:
        missing = raw.strip("'\"[] ")
        reason = f"分析需要的字段没有找到{f'：{missing}' if missing else '。'}"
        suggestions = ["打开顶部“字段映射”，确认所需字段都已对应到正确的原始列。", "检查清洗后是否改名或删除了相关列。"]
    elif any(token in text for token in (
        ".dt accessor", "datetimelike", "datetime", "dateutil", "unknown datetime",
    )):
        reason = "日期列还没有被正确识别，或其中混有无法解析的日期值。"
        suggestions = ["在“类型转换工具”中执行“列转日期”。", "检查日期列里是否混入说明文字、空白或异常数字。"]
    elif any(token in text for token in (
        "could not convert", "invalid literal", "non-numeric", "must be real number",
        "unsupported operand", "cannot convert",
    )):
        reason = "需要计算的列中混有文字、货币符号或其他非数字内容。"
        suggestions = ["在“类型转换工具”中对数量、单价等列执行“列转数值”。", "查看异常列中是否有单位、逗号或说明文字。"]
    elif any(token in text for token in (
        "emptydataerror", "no columns to parse", "zero-size array", "empty axes",
        "need at least one array", "no numeric data", "dataframe is empty",
    )):
        reason = "当前没有可用于这一步的数据，文件可能为空，或筛选、清洗后已没有记录。"
        suggestions = ["检查顶部年份和国家筛选是否过窄，并尝试重置筛选。", "回到数据清洗页查看当前行数，必要时撤销或重置。"]
    elif any(token in text for token in (
        "worksheet", "excel file format", "badzipfile", "not a zip file",
    )):
        reason = "Excel 文件结构无法读取，文件可能损坏、扩展名不正确或工作表异常。"
        suggestions = ["用 Excel 打开并重新另存为 XLSX。", "确认文件本身不是改了后缀名的其他格式。"]
    elif any(token in text for token in ("401", "authentication", "api key", "unauthorized")):
        reason = "AI 服务没有通过身份验证，API Key 或服务地址可能不正确。"
        suggestions = ["重新检查 API Key、Base URL 和供应商是否对应。", "确认该 Key 仍有效且有权使用所填模型。"]
    elif any(token in text for token in ("429", "rate limit", "quota", "insufficient_quota")):
        reason = "AI 服务请求过多，或账号额度已经不足。"
        suggestions = ["稍等一会再试。", "登录服务商后台检查余额、额度和调用限制。"]
    elif any(token in text for token in ("timeout", "timed out", "connection", "network")):
        reason = "网络连接或服务地址没有响应。"
        suggestions = ["检查网络和 Base URL 是否正确。", "稍后重试，或换用可用的 AI 服务。"]
    elif any(token in text for token in ("image", "png", "jpeg", "cannot identify")):
        reason = "图片文件不存在、未生成完整，或格式无法识别。"
        suggestions = ["返回图表页面重新生成该图。", "确认当前数据对应的输出图片文件夹没有被移动或占用。"]
    else:
        reason = _short_reason(raw) or "遇到了未识别的数据格式或当前状态不满足这一步的要求。"
        suggestions = ["检查当前数据是否还有记录，以及所需列是否存在。", "尝试撤销最近一次清洗、重置筛选后再操作。"]

    steps = "\n".join(f"{index}. {item}" for index, item in enumerate(suggestions, 1))
    return f"{action}没有完成。\n\n发生了什么：\n{reason}\n\n你可以这样处理：\n{steps}"


def show_friendly_error(title, error, action="当前操作", parent=None):
    """使用统一格式显示通俗中文错误指引。"""
    messagebox.showerror(
        title,
        friendly_error_message(error, action=action),
        parent=parent,
    )
