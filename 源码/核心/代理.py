"""
智能鲸鱼代理
===========
Agent 的大脑 —— 负责对话循环、工具调用和管理。

用法：
    from 源码.核心.代理 import 智能鲸鱼代理
    agent = 智能鲸鱼代理()
    session_id = agent.启动新会话("写一个爬虫")
    for chunk in agent.处理消息("帮我看看当前目录有哪些文件"):
        print(chunk, end="")
"""

import base64
import json
import re
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from 源码.配置 import get_config
from 源码.接口.深度求索接口 import 深度求索客户端
from 源码.存储.数据库 import 聊天数据库
from 源码.核心.提示词 import 获取系统提示词
from 源码.核心.工具集 import (
    读取文件,
    写入文件,
    列出目录,
    执行命令,
    搜索代码,
    获取文件信息,
)


# ── 工具名 → 函数映射 ─────────────────────────────────
_工具映射: Dict[str, Any] = {
    "读取文件": 读取文件,
    "写入文件": 写入文件,
    "列出目录": 列出目录,
    "执行命令": 执行命令,
    "搜索代码": 搜索代码,
    "获取文件信息": 获取文件信息,
}

# 工具调用标记的正则：匹配 【调用工具：工具名(参数)】
_工具调用模式 = re.compile(r"【调用工具：(.+?)\((.+?)\)】")

# 最大工具调用轮次，防止死循环
_最大工具轮次 = 5


# ── 工具调用解析 ───────────────────────────────────────

def _解析工具调用(文本: str) -> List[Tuple[str, str]]:
    """
    从文本中提取所有工具调用。

    参数：
        文本: AI 回复文本

    返回：
        [(工具名, 参数字符串), ...] 列表
    """
    return _工具调用模式.findall(文本)


def _执行工具调用(工具名: str, 参数字符串: str) -> str:
    """
    执行单个工具调用并返回格式化结果。

    参数：
        工具名: 工具函数的中文名称
        参数字符串: JSON 格式的参数，如 '"requirements.txt"' 或 '{"命令":"echo hi","需要确认":false}'

    返回：
        格式化的结果字符串
    """
    # 查找工具函数
    函数 = _工具映射.get(工具名.strip())
    if not 函数:
        return f"【工具结果：{工具名}】\n❌ 未知工具：{工具名}\n可用工具：{', '.join(_工具映射.keys())}"

    # 解析参数
    try:
        # 尝试作为 JSON 解析（支持对象参数）
        参数 = json.loads(参数字符串)
    except json.JSONDecodeError:
        # JSON 解析失败，作为普通字符串
        参数 = 参数字符串.strip().strip('"\'')

    # 调用工具
    try:
        if isinstance(参数, dict):
            结果 = 函数(**参数)
        else:
            结果 = 函数(参数)
    except TypeError as e:
        return f"【工具结果：{工具名}】\n❌ 参数不匹配：{e}\n提示：参数应为字符串或 JSON 对象"
    except Exception as e:
        return f"【工具结果：{工具名}】\n❌ 执行失败：{e}"

    # 格式化结果
    if isinstance(结果, dict):
        结果文本 = json.dumps(结果, ensure_ascii=False, indent=2)
    else:
        结果文本 = str(结果)

    return f"【工具结果：{工具名}】\n{结果文本}"


# ══════════════════════════════════════════════════════════
# 代理类
# ══════════════════════════════════════════════════════════

class 智能鲸鱼代理:
    """
    智能鲸鱼 AI 代理 —— 项目的核心大脑。

    负责管理对话会话、消息历史、调用 API 和执行工具。
    """

    def __init__(self):
        """初始化代理：加载配置、创建客户端和数据库连接。

        注意：此方法应在主线程调用。数据库连接配置了
        check_same_thread=False 和 WAL 模式，可在多线程中安全使用。
        """
        配置 = get_config()

        self.客户端 = 深度求索客户端(配置)
        self.数据库 = 聊天数据库()

        # 使用提示词模块中的系统提示词
        self.系统提示词 = 获取系统提示词()
        # 同步到 API 客户端
        self.客户端.system_prompt = self.系统提示词

        # 运行时状态
        self.当前会话id: Optional[int] = None
        self.消息历史: List[Dict[str, Any]] = []

    # ── 会话管理 ───────────────────────────────────────

    def 启动新会话(self, 标题: Optional[str] = None) -> int:
        """
        创建新会话并初始化消息历史。

        参数：
            标题: 会话标题（默认 "新对话"）

        返回：
            会话 ID（整数）
        """
        if not 标题:
            标题 = "新对话"

        # 创建数据库记录
        self.当前会话id = self.数据库.创建会话(标题)

        # 初始化消息历史（仅系统提示词）
        self.消息历史 = [
            {"role": "system", "content": self.系统提示词}
        ]

        # 将系统提示词也保存到数据库
        self.数据库.保存消息(self.当前会话id, "system", self.系统提示词[:200] + "...", 0)

        print(f"🐋 新会话已创建（ID: {self.当前会话id}）—— {标题}")
        return self.当前会话id

    def 加载会话(self, 会话id: int):
        """
        从数据库加载指定会话的消息历史。

        参数：
            会话id: 要加载的会话 ID
        """
        self.当前会话id = 会话id
        消息列表 = self.数据库.获取会话消息(会话id)

        if not 消息列表:
            # 空会话：初始化系统提示词
            print(f"⚠️ 会话 {会话id} 无消息记录，已初始化系统提示词")
            self.消息历史 = [
                {"role": "system", "content": self.系统提示词}
            ]
            return

        # 重建消息历史
        self.消息历史 = []
        有系统提示词 = False

        for 消息 in 消息列表:
            self.消息历史.append({
                "role": 消息["角色"],
                "content": 消息["内容"],
            })
            if 消息["角色"] == "system":
                有系统提示词 = True

        # 确保系统提示词存在
        if not 有系统提示词:
            self.消息历史.insert(0, {"role": "system", "content": self.系统提示词})

        print(f"📂 已加载会话 {会话id}，共 {len(消息列表)} 条消息")

    # ── 核心对话循环 ───────────────────────────────────

    def 处理消息(self, 用户输入: str) -> Generator[str, None, None]:
        """
        处理用户消息：调用 API，检测工具调用，执行工具并继续对话。

        参数：
            用户输入: 用户输入的文本

        生成：
            每次 yield 一个文本块（用于实时显示）

        流程：
            1. 用户消息加入历史
            2. 调用 API 流式对话
            3. yield 文本块给界面
            4. 检测工具调用 → 执行 → 将结果加入历史 → 继续 API 调用
            5. 最多 5 轮工具调用
            6. 保存完整消息到数据库
        """
        if self.当前会话id is None:
            self.启动新会话()

        # ── 加入用户消息 ──────────────────────────────
        self.消息历史.append({"role": "user", "content": 用户输入})
        self.数据库.保存消息(self.当前会话id, "user", 用户输入, 0)

        # ── 对话循环（含工具调用） ─────────────────────
        工具轮次 = 0

        while 工具轮次 <= _最大工具轮次:
            完整回复 = ""

            try:
                # 调用 API 流式对话
                for 文本块 in self.客户端.流式对话(self.消息历史):
                    完整回复 += 文本块
                    yield 文本块

            except Exception as e:
                yield f"\n❌ 对话异常：{e}"
                break

            # ── 检测工具调用 ───────────────────────────
            工具调用列表 = _解析工具调用(完整回复)

            if not 工具调用列表:
                # 无工具调用 → 保存回复并结束
                self.消息历史.append({"role": "assistant", "content": 完整回复})
                self.数据库.保存消息(self.当前会话id, "assistant", 完整回复, 0)
                break

            # ── 有工具调用：执行并继续 ─────────────────
            if 工具轮次 >= _最大工具轮次:
                yield "\n⚠️ 已达到最大工具调用次数（5次），已停止继续调用。"
                self.消息历史.append({"role": "assistant", "content": 完整回复})
                self.数据库.保存消息(self.当前会话id, "assistant", 完整回复, 0)
                break

            工具轮次 += 1
            yield f"\n\n🔧 正在执行工具（第 {工具轮次} 轮）...\n"

            # 将 AI 回复加入历史
            self.消息历史.append({"role": "assistant", "content": 完整回复})

            # 执行每个工具调用
            工具结果汇总 = []
            for 工具名, 参数 in 工具调用列表:
                yield f"   ⚙️ 调用：{工具名}({参数[:80]})\n"
                结果文本 = _执行工具调用(工具名, 参数)
                工具结果汇总.append(结果文本)

            # 将所有工具结果合并为一条 assistant 消息
            合并结果 = "\n\n".join(工具结果汇总)
            self.消息历史.append({"role": "assistant", "content": 合并结果})
            self.数据库.保存消息(self.当前会话id, "assistant", 合并结果, 0)

            # 继续循环，让 AI 基于工具结果生成最终回复

    # ── 图片消息处理 ───────────────────────────────────

    def 处理图片消息(
        self, 用户文本: str, 图片路径列表: List[str]
    ) -> Generator[str, None, None]:
        """
        处理包含图片的用户消息，使用视觉 API。

        参数：
            用户文本: 用户输入的文本
            图片路径列表: 图片文件路径列表

        生成：
            每次 yield 一个文本块（用于实时显示）
        """
        if self.当前会话id is None:
            self.启动新会话()

        # ── 读取图片并转为 base64 ─────────────────────
        图片base64列表 = []
        for 路径 in 图片路径列表:
            try:
                图片路径 = Path(路径)
                if not 图片路径.exists():
                    yield f"❌ 图片不存在：{路径}\n"
                    continue
                with open(图片路径, "rb") as f:
                    图片base64列表.append(base64.b64encode(f.read()).decode("ascii"))
            except Exception as e:
                yield f"❌ 读取图片失败（{路径}）：{e}\n"

        if not 图片base64列表:
            yield "❌ 没有可用的图片，已取消本次请求。"
            return

        # ── 构建用户消息 ──────────────────────────────
        消息内容 = 用户文本 or "请分析这张图片"
        if 图片路径列表:
            消息内容 += f"\n（附加了 {len(图片路径列表)} 张图片）"

        self.消息历史.append({"role": "user", "content": 消息内容})
        self.数据库.保存消息(self.当前会话id, "user", 消息内容, 0)

        # ── 调用视觉 API ──────────────────────────────
        完整回复 = ""

        try:
            for 文本块 in self.客户端.视觉对话(self.消息历史, 图片base64列表):
                完整回复 += 文本块
                yield 文本块
        except Exception as e:
            yield f"\n❌ 视觉对话异常：{e}"
            return

        # ── 保存回复 ──────────────────────────────────
        self.消息历史.append({"role": "assistant", "content": 完整回复})
        self.数据库.保存消息(self.当前会话id, "assistant", 完整回复, 0)

    # ── 生命周期 ───────────────────────────────────────

    def 关闭(self):
        """关闭数据库连接"""
        try:
            self.数据库.关闭()
        except Exception:
            pass

    def __del__(self):
        self.关闭()
