"""
深度求索 API 接口封装
====================
封装 DeepSeek V4 Pro API 调用，提供三种对话模式：
  - 流式对话：逐字返回，适合实时显示
  - 视觉对话：支持图片多模态输入
  - 普通对话：一次性返回完整回复

依赖：openai 库
"""

from typing import Any, Dict, Generator, List

from openai import OpenAI


class 深度求索客户端:
    """
    DeepSeek V4 Pro API 客户端。

    用法：
        from 源码.配置 import get_config
        config = get_config()
        client = 深度求索客户端(config)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化客户端。

        参数：
            config: 配置字典（由 源码.配置.get_config() 返回）
                   需要包含 api_key, base_url, model, max_tokens, temperature
        """
        self._api_key = config.get("api_key", "")
        self._base_url = config.get("base_url", "https://api.deepseek.com")
        self._model = config.get("model", "deepseek-v4-pro")
        self._max_tokens = config.get("max_tokens", 80000)
        self._temperature = config.get("temperature", 0.7)

        # 初始化 OpenAI 兼容客户端
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

        # 系统提示词（如未设置则使用默认）
        self._system_prompt = (
            "你是一个专业的AI编程助手，名为'智能鲸鱼'。"
            "你用中文与用户交流，帮助用户编写代码、分析问题、处理文件。"
            "你的回答应该准确、简洁、有结构。"
        )

    # ── 系统提示词 ──────────────────────────────────────

    @property
    def system_prompt(self) -> str:
        """获取当前系统提示词"""
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, prompt: str):
        """设置系统提示词"""
        self._system_prompt = prompt

    # ── 消息构建 ────────────────────────────────────────

    def _构建完整消息列表(self, 消息列表: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        在消息列表前面插入系统提示词，构建完整消息。

        参数：
            消息列表: 用户消息列表，每条为 {"role": ..., "content": ...}

        返回：
            带系统提示词的完整消息列表
        """
        return [
            {"role": "system", "content": self._system_prompt},
            *消息列表,
        ]

    # ── 方法1：流式对话 ─────────────────────────────────

    def 流式对话(self, 消息列表: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """
        流式对话：逐块返回 AI 回复文本。

        参数：
            消息列表: 用户消息列表

        生成：
            每次 yield 一个文本块（str）

        异常：
            API 调用失败时打印中文错误并终止生成
        """
        try:
            完整消息 = self._构建完整消息列表(消息列表)
            流 = self._client.chat.completions.create(
                model=self._model,
                messages=完整消息,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                stream=True,
            )

            for 块 in 流:
                if 块.choices and 块.choices[0].delta:
                    文本 = 块.choices[0].delta.content
                    if 文本:
                        yield 文本

        except Exception as e:
            print(f"❌ API 调用失败：{e}")

    # ── 方法2：视觉对话 ─────────────────────────────────

    def 视觉对话(
        self,
        消息列表: List[Dict[str, Any]],
        图片列表: List[str],
    ) -> Generator[str, None, None]:
        """
        视觉对话：支持图片多模态输入的流式对话。

        参数：
            消息列表: 用户消息列表（文本部分）
            图片列表: 图片的 base64 字符串列表（不含 data: 前缀）

        生成：
            每次 yield 一个文本块（str）

        用法：
            # 读取本地图片并转为 base64
            import base64
            with open("截图.png", "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()

            for chunk in client.视觉对话(消息列表, [img_b64]):
                print(chunk, end="")
        """
        try:
            完整消息 = self._构建完整消息列表(消息列表)

            # ── 构建多模态 content ─────────────────────
            # 将最后一条用户消息替换为多模态格式
            if 完整消息 and 完整消息[-1]["role"] == "user":
                文本内容 = 完整消息[-1]["content"]
                多模态内容: List[Dict[str, Any]] = [
                    {"type": "text", "text": 文本内容},
                ]
                # 添加图片（data:image/xxx;base64,xxx 格式）
                for 图片_base64 in 图片列表:
                    多模态内容.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{图片_base64}"
                        },
                    })
                完整消息[-1]["content"] = 多模态内容

            流 = self._client.chat.completions.create(
                model=self._model,
                messages=完整消息,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                stream=True,
            )

            for 块 in 流:
                if 块.choices and 块.choices[0].delta:
                    文本 = 块.choices[0].delta.content
                    if 文本:
                        yield 文本

        except Exception as e:
            print(f"❌ API 调用失败：{e}")

    # ── 方法3：普通对话 ─────────────────────────────────

    def 普通对话(self, 消息列表: List[Dict[str, Any]]) -> str:
        """
        普通对话：一次性返回完整 AI 回复。

        参数：
            消息列表: 用户消息列表

        返回：
            AI 的完整回复文本

        异常：
            API 调用失败时打印中文错误并返回空字符串
        """
        try:
            完整消息 = self._构建完整消息列表(消息列表)
            响应 = self._client.chat.completions.create(
                model=self._model,
                messages=完整消息,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                stream=False,
            )

            if 响应.choices and 响应.choices[0].message:
                return 响应.choices[0].message.content or ""
            return ""

        except Exception as e:
            print(f"❌ API 调用失败：{e}")
            return ""
