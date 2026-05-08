"""
配置管理模块
============
管理所有配置项，支持首次密钥引导输入。

配置优先级：
  1. 环境变量 DEEPSEEK_API_KEY（最高）
  2. 用户目录 .deepseek-cn/config.json
  3. 内置默认值

用法：
    from 源码.配置 import get_config, 初始化配置, 保存配置, 验证密钥
    config = get_config()
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# ── 默认配置 ────────────────────────────────────────────
_默认配置: Dict[str, Any] = {
    "api_key": "",
    "model": "deepseek-v4-pro",
    "base_url": "https://api.deepseek.com",
    "max_tokens": 80000,
    "temperature": 0.7,
}

# ── 配置文件路径 ────────────────────────────────────────
_配置目录 = Path.home() / ".deepseek-cn"
_配置文件 = _配置目录 / "config.json"


def _从文件加载() -> Dict[str, Any]:
    """从 ~/.deepseek-cn/config.json 读取配置"""
    if not _配置文件.exists():
        return {}

    try:
        with open(_配置文件, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️ 配置文件解析失败（{_配置文件}）：{e}")
        return {}


def _从环境变量加载() -> Dict[str, Any]:
    """从环境变量读取配置"""
    config: Dict[str, Any] = {}
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if api_key:
        config["api_key"] = api_key
    return config


def get_config() -> Dict[str, Any]:
    """
    获取完整配置字典。
    加载优先级：环境变量 > JSON 配置文件 > 默认值
    """
    config = dict(_默认配置)
    文件配置 = _从文件加载()
    config.update(文件配置)
    环境配置 = _从环境变量加载()
    for key, value in 环境配置.items():
        if value:
            config[key] = value
    return config


# ── 首次配置引导 ───────────────────────────────────────

def 初始化配置() -> Optional[Dict[str, Any]]:
    """
    初始化配置 —— 尝试获取 API 密钥。

    检查顺序：
      1. 环境变量 DEEPSEEK_API_KEY
      2. ~/.deepseek-cn/config.json 中的 api_key
      3. 都没有 → 返回 None（表示需要首次配置）

    返回：
        包含 api_key 的配置字典；无密钥时返回 None
    """
    # 检查环境变量
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if api_key:
        return {"api_key": api_key, "model": _默认配置["model"]}

    # 检查配置文件
    文件配置 = _从文件加载()
    if 文件配置.get("api_key", "").strip():
        return {
            "api_key": 文件配置["api_key"].strip(),
            "model": 文件配置.get("model", _默认配置["model"]),
        }

    # 两者都没有
    return None


def 保存配置(api_key: str, model: str = "deepseek-v4-pro"):
    """
    保存 API 密钥到配置文件。

    参数：
        api_key: DeepSeek API 密钥
        model:   模型名称（默认 deepseek-v4-pro）

    操作：
        - 自动创建 ~/.deepseek-cn/ 目录
        - 写入 config.json
    """
    _配置目录.mkdir(parents=True, exist_ok=True)

    数据 = {
        "api_key": api_key.strip(),
        "model": model,
    }

    with open(_配置文件, "w", encoding="utf-8") as f:
        json.dump(数据, f, ensure_ascii=False, indent=2)

    print(f"📁 配置已保存到：{_配置文件}")

    # 同时设置到当前进程环境变量
    os.environ["DEEPSEEK_API_KEY"] = api_key.strip()


def 验证密钥(api_key: str) -> bool:
    """
    验证 DeepSeek API 密钥是否有效。

    参数：
        api_key: 要验证的 API 密钥

    返回：
        True   — 密钥有效
        False  — 密钥无效（已打印中文错误原因）
    """
    try:
        from openai import OpenAI

        客户端 = OpenAI(
            api_key=api_key.strip(),
            base_url="https://api.deepseek.com",
        )

        # 调用 models 接口验证密钥
        客户端.models.list()

        return True

    except Exception as e:
        错误信息 = str(e)

        # 翻译常见错误为中文
        if "401" in 错误信息 or "Unauthorized" in 错误信息:
            print("❌ 密钥无效：认证失败，请检查密钥是否正确")
        elif "403" in 错误信息 or "Forbidden" in 错误信息:
            print("❌ 密钥无效：没有访问权限，请确认账户状态")
        elif "429" in 错误信息 or "Rate limit" in 错误信息:
            print("❌ 请求过于频繁，请稍后再试")
        elif "timeout" in 错误信息.lower() or "connect" in 错误信息.lower():
            print("❌ 网络连接失败，请检查网络或 API 地址")
        else:
            # 截断过长的错误信息
            if len(错误信息) > 200:
                错误信息 = 错误信息[:200] + "..."
            print(f"❌ 密钥验证失败：{错误信息}")

        return False


# ── 模块级单例（避免重复加载） ───────────────────────────
_config_cache: Dict[str, Any] | None = None


def _get_cached_config() -> Dict[str, Any]:
    """获取缓存的配置（模块级单例）"""
    global _config_cache
    if _config_cache is None:
        _config_cache = get_config()
    return _config_cache
