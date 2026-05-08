"""
输入框
=====
多行输入组件，支持 Ctrl+Enter 发送、Esc 清空。

用法：
    input_box = 输入框(id="输入区域")
    input_box.设置标题("当前会话：爬虫编写")
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import TextArea, Static


class UI输入框(Vertical):
    """
    多行消息输入组件。

    快捷键：
      - Ctrl+Enter: 发送消息（需在父级处理）
      - Esc:        清空输入框
      - Shift+Enter: 插入换行（默认行为）

    组合结构：
      ┌── 会话标题栏 ──────────────────┐
      │  📂 当前会话：XXX               │
      ├── 输入区 ──────────────────────┤
      │  💬 输入你的问题...              │
      │  (多行文本)                     │
      └────────────────────────────────┘
    """

    BINDINGS = [
        Binding("escape", "清空输入", "清空输入", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._会话标题 = "新对话"

    def compose(self) -> ComposeResult:
        """构建子组件"""
        yield Static(f"📂 当前会话：{self._会话标题}", classes="input-hint")
        yield TextArea(
            "",
            id="message-input",
            language=None,
            show_line_numbers=False,
            tab_behavior="indent",
            soft_wrap=True,
            max_checkpoints=10,
        )

    # ── 属性 ───────────────────────────────────────────

    @property
    def 文本内容(self) -> str:
        """获取当前输入框文本"""
        try:
            textarea = self.query_one("#message-input", TextArea)
            return textarea.text.strip()
        except Exception:
            return ""

    @property
    def 是否为空(self) -> bool:
        """输入框是否为空"""
        return self.文本内容 == ""

    # ── 操作 ───────────────────────────────────────────

    def 获取并清空(self) -> str:
        """
        获取当前文本并清空输入框。

        返回：
            输入文本内容
        """
        文本 = self.文本内容
        try:
            textarea = self.query_one("#message-input", TextArea)
            textarea.clear()
        except Exception:
            pass
        return 文本

    def action_清空输入(self):
        """清空输入框（Esc 快捷键）"""
        try:
            textarea = self.query_one("#message-input", TextArea)
            textarea.clear()
        except Exception:
            pass

    def 设置标题(self, 标题: str):
        """
        设置会话标题显示。

        参数：
            标题: 会话标题文本
        """
        self._会话标题 = 标题
        try:
            static = self.query_one("Static")
            static.update(f"📂 当前会话：{标题}")
        except Exception:
            pass

    def 聚焦(self):
        """聚焦到输入框"""
        try:
            textarea = self.query_one("#message-input", TextArea)
            textarea.focus()
        except Exception:
            pass