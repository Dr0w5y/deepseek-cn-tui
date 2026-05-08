"""
智能鲸鱼主应用
============
Textual 终端 UI 主程序。

布局：
  ┌── 顶部状态栏 ─────────────────────────────┐
  │  🐋 智能鲸鱼 | 当前会话：XXX | Token：1234  │
  ├──── 左侧面板 ──┬── 对话区 ─────────────────┤
  │  文件树        │  消息列表                  │
  │               │                           │
  │               │                           │
  ├────────────────┴───────────────────────────┤
  │  输入区域                                  │
  │  📂 当前会话：XXX                          │
  │  💬 输入问题... Ctrl+回车发送               │
  ├────────────────────────────────────────────┤
  │  Ctrl+Q 退出 | Ctrl+N 新会话 | F1 帮助      │
  └────────────────────────────────────────────┘

快捷键：
  Ctrl+Q: 退出
  Ctrl+B: 切换文件面板
  Ctrl+N: 新建会话
  Ctrl+L: 清屏
  Ctrl+S: 保存当前会话
  F1:     显示帮助
"""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from 源码.核心.代理 import 智能鲸鱼代理
from 源码.界面.对话面板 import UI对话面板 as 对话面板
from 源码.界面.输入框 import UI输入框 as 输入框
from 源码.界面.文件面板 import UI文件面板 as 文件面板


class UI智能鲸鱼应用(App):
    """
    智能鲸鱼终端应用主界面。

    CSS 文件: 源码/界面/样式表.css
    """

    # ── 元信息 ─────────────────────────────────────────
    CSS_PATH = "样式表.css"
    TITLE = "🐋 智能鲸鱼 — 终端中文编程搭子"
    SUB_TITLE = "DeepSeek V4 Pro"

    BINDINGS = [
        Binding("ctrl+q", "退出", "退出", show=True),
        Binding("ctrl+b", "切换文件面板", "文件面板"),
        Binding("ctrl+n", "新建会话", "新会话"),
        Binding("ctrl+l", "清屏", "清屏"),
        Binding("ctrl+s", "保存会话", "保存"),
        Binding("f1", "显示帮助", "帮助"),
        Binding("ctrl+enter", "发送消息", "发送", show=False, priority=True),
        Binding("ctrl+j", "发送消息", "发送", show=False, priority=True),
    ]

    # ── 生命周期 ─────────────────────────────────────

    def __init__(self, 工作目录: str = ".", **kwargs):
        super().__init__(**kwargs)
        self.工作目录 = Path(工作目录).resolve()
        self.文件面板可见 = True
        self.代理: Optional[智能鲸鱼代理] = None

    def on_mount(self) -> None:
        """应用启动后初始化"""
        # 初始化代理
        self.代理 = 智能鲸鱼代理()
        self.代理.启动新会话()

        # 更新状态栏
        self._更新状态栏()

        # 设置文件面板根目录和回调
        面板 = self.query_one("#file-panel", 文件面板)
        面板.path = self.工作目录
        面板.文件被点击_callback = self._文件被点击

        # 更新输入框标题
        输入 = self.query_one("#input-area", 输入框)
        输入.设置标题("新对话")

        # 显示欢迎消息
        对话 = self.query_one("#chat-panel", 对话面板)
        对话.显示系统消息("🐋 欢迎使用智能鲸鱼！输入你的问题开始对话。")
        对话.显示系统消息("Ctrl+Enter 发送 | Ctrl+B 文件面板 | F1 帮助")

    # ── 界面构建 ──────────────────────────────────────

    def compose(self) -> ComposeResult:
        """构建界面布局"""
        # 顶部状态栏
        yield Static("", id="status-bar")

        # 主内容区（水平布局）
        with Horizontal():
            # 左侧文件面板
            yield 文件面板(self.工作目录, id="file-panel")

            # 右侧对话+输入区（垂直布局）
            with Vertical(id="chat-area"):
                yield 对话面板(id="chat-panel")
                yield 输入框(id="input-area")

        # 底部快捷键提示
        yield Static(
            " Ctrl+Q 退出 | Ctrl+N 新会话 | Ctrl+B 文件面板 | Ctrl+L 清屏 | Ctrl+S 保存 | F1 帮助 ",
            id="shortcut-bar",
        )

    # ── 快捷键处理 ────────────────────────────────────

    def action_退出(self):
        """退出应用"""
        if self.代理:
            self.代理.关闭()
        self.exit()

    def action_切换文件面板(self):
        """切换左侧文件面板的显示/隐藏"""
        面板 = self.query_one("#file-panel", 文件面板)
        面板.display = not 面板.display
        self.文件面板可见 = 面板.display

        状态 = "显示" if 面板.display else "隐藏"
        try:
            对话 = self.query_one("#chat-panel", 对话面板)
            对话.显示系统消息(f"文件面板已{状态}")
        except Exception:
            pass

    def action_新建会话(self):
        """创建新会话"""
        if not self.代理:
            return

        标题 = "新对话"
        # TODO: 后续可弹出输入框让用户输入标题
        self.代理.启动新会话(标题)

        对话 = self.query_one("#chat-panel", 对话面板)
        对话.清屏()
        对话.显示系统消息(f"🐋 新会话已创建")

        输入 = self.query_one("#input-area", 输入框)
        输入.设置标题(标题)

        self._更新状态栏()

    def action_清屏(self):
        """清空对话面板"""
        try:
            对话 = self.query_one("#chat-panel", 对话面板)
            对话.清屏()
        except Exception:
            pass

    def action_保存会话(self):
        """保存当前会话到数据库（消息已自动保存，此为确认操作）"""
        if not self.代理 or not self.代理.当前会话id:
            return

        try:
            对话 = self.query_one("#chat-panel", 对话面板)
            # 统计 token 用量
            tokens = self.代理.数据库.统计Token用量(self.代理.当前会话id)
            对话.显示成功(f"会话已保存（当前累计 {tokens} tokens）")
        except Exception:
            pass

    def action_显示帮助(self):
        """显示帮助信息（中文）"""
        try:
            对话 = self.query_one("#chat-panel", 对话面板)
            对话.显示分隔线()
            对话.显示系统消息("""
🐋 智能鲸鱼 帮助
━━━━━━━━━━━━━━━━━━━━
快捷键：
  Ctrl+Enter  发送消息
  Ctrl+Q      退出程序
  Ctrl+B      切换文件面板
  Ctrl+N      新建会话
  Ctrl+L      清空对话
  Ctrl+S      保存当前会话
  F1          显示此帮助
  Esc         清空输入框

使用技巧：
  - 输入 "帮我看看 [文件名]" 让 AI 读取文件
  - 输入 "搜索 [关键词]" 让 AI 搜索代码
  - 直接粘贴图片路径让 AI 分析图片
  - AI 会自动调用工具读取项目文件
━━━━━━━━━━━━━━━━━━━━
""")
            对话.显示分隔线()
        except Exception:
            pass

    def action_发送消息(self):
        """发送消息（Ctrl+Enter）—— 快速 UI 操作 + 后台 API 调用"""
        if not self.代理:
            return

        输入 = self.query_one("#input-area", 输入框)
        文本 = 输入.获取并清空()

        if not 文本:
            return

        对话 = self.query_one("#chat-panel", 对话面板)

        # ── 主线程：快速 UI 更新 ────────────────────
        对话.显示用户消息(文本)
        对话.显示AI消息("")  # AI 响应占位

        # ── 后台线程：阻塞 API 调用 ─────────────────
        import threading
        thread = threading.Thread(
            target=self._发送消息_worker, args=(文本,), daemon=True
        )
        thread.start()

    # ── 后台工作者 ─────────────────────────────────────

    def _发送消息_worker(self, 文本: str):
        """
        在后台线程中调用 API，通过 call_from_thread 安全更新 UI。

        运行在独立线程中，不阻塞 Textual 事件循环。
        所有 UI 操作通过 self.call_from_thread() 回到主线程。
        """
        try:
            for 块 in self.代理.处理消息(文本):
                self.call_from_thread(self._追加流式文本, 块)
        except Exception as e:
            self.call_from_thread(self._显示API错误, str(e))
        finally:
            self.call_from_thread(self._发送完成)

    def _追加流式文本(self, 块: str):
        """（主线程）向对话面板追加流式文本块"""
        try:
            对话 = self.query_one("#chat-panel", 对话面板)
            对话.显示流式文本(块)
        except Exception:
            pass

    def _显示API错误(self, 错误信息: str):
        """（主线程）在对话面板显示 API 错误"""
        try:
            对话 = self.query_one("#chat-panel", 对话面板)
            对话.显示错误(f"对话失败：{错误信息}")
        except Exception:
            pass

    def _发送完成(self):
        """（主线程）对话完成后的收尾工作"""
        try:
            对话 = self.query_one("#chat-panel", 对话面板)
            对话.刷新流式缓冲()   # 将缓冲区残余文本写入面板
            对话.滚动到底部()
        except Exception:
            pass
        self._更新状态栏()

    # ── 内部方法 ──────────────────────────────────────

    def _更新状态栏(self):
        """更新顶部状态栏"""
        if not self.代理:
            return

        try:
            状态 = self.query_one("#status-bar", Static)

            if self.代理.当前会话id:
                tokens = self.代理.数据库.统计Token用量(self.代理.当前会话id)
                会话信息 = f"当前会话：ID {self.代理.当前会话id}"
            else:
                tokens = 0
                会话信息 = "当前会话：未创建"

            状态.update(
                f" 🐋 智能鲸鱼 | {会话信息} | Token：{tokens} "
            )
        except Exception:
            pass

    def _文件被点击(self, 文件路径: str):
        """
        文件树中文件被点击时的回调。

        参数：
            文件路径: 被点击的文件路径
        """
        # 自动发送查看文件的消息
        输入 = self.query_one("#input-area", 输入框)
        输入.获取并清空()  # 清空现有内容

        # 将文件路径放入输入框，让用户可以再编辑
        textarea = 输入.query_one("#message-input")
        textarea.text = f"帮我看看这个文件：{文件路径}"
        textarea.focus()

        # 也可直接发送（取消下面注释即可）
        # self.action_发送消息()