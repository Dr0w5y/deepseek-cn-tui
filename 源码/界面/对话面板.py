"""
对话面板
=======
聊天消息展示面板，继承 RichLog，支持 Markdown 渲染和代码高亮。

用法：
    panel = 对话面板(id="对话面板")
    panel.显示用户消息("帮我写个函数")
    panel.显示AI消息("好的，这是代码...")
    panel.显示工具消息("【工具结果：列出目录】...")
"""

from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from textual.widgets import RichLog


class UI对话面板(RichLog):
    """
    对话消息展示面板。

    支持：
      - Markdown 渲染（标题、粗体、斜体、链接）
      - 代码块语法高亮
      - 用户消息 / AI 消息 / 工具消息 三种气泡样式
      - 自动滚动到底部
    """

    def __init__(self, **kwargs):
        super().__init__(
            markup=True,         # 支持 Rich markup
            auto_scroll=True,    # 自动滚动到底部
            wrap=True,           # 自动换行
            highlight=True,      # 语法高亮（Markdown 中的代码）
            min_width=40,        # 最小宽度（列），防止被挤压到很窄
            **kwargs,
        )
        # 流式输出缓冲区：避免每个微小 chunk 单独 write() 独立成行
        self._流式缓冲区: str = ""

    # ── 消息显示方法 ───────────────────────────────────

    def 显示用户消息(self, 内容: str):
        """
        显示用户消息（蓝色调气泡）。

        参数：
            内容: 用户消息文本
        """
        文本 = Text()
        文本.append("\n🐋 你\n", style="bold #7aa2f7")
        # 消息内容
        try:
            md = Markdown(内容, code_theme="dracula")
            文本.append(md)
        except Exception:
            文本.append(内容, style="#c0caf5")
        文本.append("\n")
        self.write(文本)

    def 显示AI消息(self, 内容: str):
        """
        显示 AI 消息（绿色调气泡，Markdown 渲染）。

        参数：
            内容: AI 回复文本（支持 Markdown）
        """
        文本 = Text()
        文本.append("\n🤖 智能鲸鱼\n", style="bold #9ece6a")
        try:
            md = Markdown(内容, code_theme="dracula")
            文本.append(md)
        except Exception:
            文本.append(内容, style="#a9b1d6")
        文本.append("\n")
        self.write(文本)

    def 显示流式文本(self, 内容: str):
        """
        追加 AI 流式输出的文本（累积到缓冲区，达到阈值才写入）。

        避免每个微小 chunk 单独 write() 导致 RichLog 独立成行，
        从而解决中文每两三个字就换行的问题。

        参数：
            内容: 流式输出的文本块
        """
        if not hasattr(self, '_流式缓冲区'):
            self._流式缓冲区 = ""
        self._流式缓冲区 += 内容
        # 遇到换行符 或 缓冲区积累超过 60 个字符时，一次性写入
        if '\n' in self._流式缓冲区 or len(self._流式缓冲区) >= 60:
            待写入 = self._流式缓冲区
            self._流式缓冲区 = ""
            self.write(待写入)

    def 刷新流式缓冲(self):
        """将流式缓冲区中剩余内容写入面板（对话完成时调用）。"""
        if hasattr(self, '_流式缓冲区') and self._流式缓冲区:
            self.write(self._流式缓冲区)
            self._流式缓冲区 = ""

    def 显示工具消息(self, 工具名: str, 参数: str = "", 结果: str = ""):
        """
        显示工具调用消息（橙色调）。

        参数：
            工具名: 工具名称
            参数:   工具参数
            结果:   工具返回结果
        """
        文本 = Text()
        文本.append(f"\n🔧 工具调用：{工具名}", style="bold #e0af68")
        if 参数:
            文本.append(f"\n   参数：{参数}", style="#e0af68")
        if 结果:
            # 截断过长的结果
            if len(结果) > 500:
                结果 = 结果[:500] + "\n... (已截断)"
            文本.append(f"\n{结果}", style="italic #a9b1d6")
        文本.append("\n")
        self.write(文本)

    def 显示系统消息(self, 内容: str):
        """
        显示系统消息（居中灰色）。

        参数：
            内容: 系统消息文本
        """
        文本 = Text(f"\n  {内容}  \n", style="italic #565f89")
        self.write(文本)

    def 显示错误(self, 内容: str):
        """
        显示错误消息（红色）。

        参数：
            内容: 错误文本
        """
        文本 = Text(f"\n❌ 错误：{内容}\n", style="bold #f7768e")
        self.write(文本)

    def 显示成功(self, 内容: str):
        """
        显示成功消息（绿色）。

        参数：
            内容: 成功文本
        """
        文本 = Text(f"\n✅ {内容}\n", style="bold #9ece6a")
        self.write(文本)

    def 显示分隔线(self):
        """显示视觉分隔线"""
        self.write(Text("─" * 40, style="#3b4261"))

    # ── 清屏 ───────────────────────────────────────────

    def 清屏(self):
        """清空对话面板"""
        self.clear()

    # ── 滚动 ───────────────────────────────────────────

    def 滚动到底部(self):
        """强制滚动到最底部"""
        self.scroll_end(animate=False)
