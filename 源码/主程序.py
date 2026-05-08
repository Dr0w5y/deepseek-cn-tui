"""
智能鲸鱼 — 主程序入口
=====================
用户启动程序时的入口文件。

启动流程：
  1. 显示启动横幅
  2. 初始化配置（首次引导输入密钥）
  3. 验证并保存密钥
  4. 启动 Textual 应用

用法：
    python -m 源码.主程序
    python -m 源码.主程序 --model deepseek-chat
    deepseek-cn --version
"""

import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# ── 版本号 ─────────────────────────────────────────────
__version__ = "0.1.0"
版本号 = f"🐋 智能鲸鱼 v{__version__}"


# ── 启动横幅 ──────────────────────────────────────────

启动横幅 = """
╔══════════════════════════════════╗
║      🐋 智 能 鲸 鱼            ║
║   deepseek-cn v0.1.0           ║
║   终端里的中文编程搭子          ║
╚══════════════════════════════════╝"""

# retro ASCII 艺术（保留，--ascii 参数可用）
鲸鱼LOGO = r"""
                    ████████
                ████▓▓▓▓▓▓████
            ████▓▓▓▓▓▓▓▓▓▓▓▓████
         ████▓▓▓▓░░░░░░░░▓▓▓▓▓▓████
       ████▓▓░░  ░░░░  ░░░░▓▓▓▓▓▓██
     ████▓▓░░  ░░░░░░░░  ░░░░▓▓▓▓██
    ████▓▓░░  ░░░░░░░░░░░░  ░░▓▓▓▓██          🐋
   ████▓▓░░  ░░░░████░░░░░░  ░░░░▓▓▓▓██
   ██▓▓░░  ░░░░████████░░░░  ░░░░▓▓▓▓██
   ██▓▓░░  ░░░░██    ██░░░░  ░░░░▓▓██
   ██▓▓░░  ░░░░████████░░░   ░░░░▓▓██     智 能 鲸 鱼
  ████▓▓░░  ░░░░██████░░░    ░░▓▓▓▓██
  ██▓▓▓▓░░  ░░░░░░░░░░    ░░░░▓▓▓▓██     DeepSeek V4 Pro
  ██▓▓▓▓░░  ░░░░░░░░    ░░░░▓▓▓▓██
  ██▓▓▓▓▓▓░░          ░░░░▓▓▓▓▓▓██      终端中文编程搭子
  ██▓▓▓▓▓▓▓▓░░░░░░░░░░░░▓▓▓▓▓▓▓▓██
   ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
   ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓████
     ██████████████████████████
       ██████████████████████
"""


# ── 命令行参数解析 ────────────────────────────────────

def 解析命令行参数(参数列表: list[str] | None = None) -> argparse.Namespace:
    """
    解析命令行参数（全部使用中文提示）。
    """
    解析器 = argparse.ArgumentParser(
        prog="deepseek-cn",
        description="🐋 智能鲸鱼 — 终端中文编程搭子",
        epilog="项目地址：https://github.com/Dr0w5y/deepseek-cn-tui",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    解析器.add_argument(
        "--model",
        type=str,
        default="deepseek-v4-pro",
        metavar="模型名",
        help="使用的模型名称（默认：deepseek-v4-pro）",
    )

    解析器.add_argument(
        "--session",
        type=int,
        default=None,
        metavar="会话ID",
        help="加载指定会话 ID 的历史记录",
    )

    解析器.add_argument(
        "--dir",
        type=str,
        default=".",
        metavar="目录",
        help="指定工作目录（默认：当前目录）",
    )

    解析器.add_argument(
        "--ascii",
        action="store_true",
        help="显示经典 ASCII 鲸鱼 LOGO",
    )

    解析器.add_argument(
        "--version",
        action="version",
        version=版本号,
        help="显示版本号并退出",
    )

    return 解析器.parse_args(参数列表)


# ── 启动流程 ──────────────────────────────────────────

def _显示启动横幅(ascii_mode: bool = False):
    """显示启动横幅"""
    if ascii_mode:
        print("\033[96m" + 鲸鱼LOGO + "\033[0m")
        print(f"\033[1;92m  {版本号}\033[0m")
        print(f"\033[90m  {'─' * 56}\033[0m")
    else:
        print("\033[96m" + 启动横幅 + "\033[0m")
    print()


def _首次配置引导() -> Dict[str, Any]:
    """
    首次配置引导 —— 等待用户输入 API 密钥。

    返回：
        包含 api_key 的配置字典
    """
    print("🔑 首次使用需要配置 API 密钥")
    print("   获取地址：https://platform.deepseek.com/api_keys")
    print()

    while True:
        try:
            密钥 = getpass.getpass("   请输入你的 DeepSeek API 密钥：")
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 已取消")
            sys.exit(0)

        密钥 = 密钥.strip()
        if not 密钥:
            print("   ⚠️ 密钥不能为空，请重新输入\n")
            continue

        print()
        print("⏳ 正在验证密钥...")

        from 源码.配置 import 验证密钥

        if 验证密钥(密钥):
            print("✅ 密钥验证成功！")
            from 源码.配置 import 保存配置
            保存配置(密钥)
            return {"api_key": 密钥, "model": "deepseek-v4-pro"}
        else:
            print("   请重新输入\n")


def _创建配置(参数: argparse.Namespace) -> Dict[str, Any]:
    """根据参数创建最终配置"""
    from 源码.配置 import get_config
    配置 = get_config()
    if 参数.model:
        配置["model"] = 参数.model
    return 配置


# ── 主入口 ────────────────────────────────────────────

def main(参数列表: list[str] | None = None):
    """
    智能鲸鱼主入口函数。

    启动流程：
        1. 显示启动横幅
        2. 初始化配置（首次引导输入密钥）
        3. 验证并保存密钥
        4. 初始化代理
        5. 启动 Textual 应用
    """

    # ── 1. 显示启动横幅 ────────────────────────────
    参数 = 解析命令行参数(参数列表)
    _显示启动横幅(ascii_mode=参数.ascii)

    # ── 2. 初始化配置 ──────────────────────────────
    from 源码.配置 import 初始化配置

    现有配置 = 初始化配置()

    if 现有配置 is None:
        # 首次使用，引导输入密钥
        现有配置 = _首次配置引导()
    else:
        print("🔑 已找到 API 密钥，跳过配置")
        print()

    # ── 3. 合并命令行参数 ──────────────────────────
    from 源码.配置 import get_config
    完整配置 = get_config()
    if 参数.model:
        完整配置["model"] = 参数.model

    # 二次确认密钥存在
    if not 完整配置.get("api_key"):
        print("❌ 未找到 API 密钥，无法启动")
        print("   请设置环境变量 DEEPSEEK_API_KEY 或删除配置文件后重新启动")
        sys.exit(1)

    # ── 4. 启动代理 ────────────────────────────────
    print("🚀 正在启动智能鲸鱼...")
    print()

    from 源码.核心.代理 import 智能鲸鱼代理

    代理 = 智能鲸鱼代理()

    if 参数.session:
        try:
            代理.加载会话(参数.session)
            print(f"📂 已加载会话 {参数.session}")
        except Exception as e:
            print(f"⚠️ 加载会话失败：{e}")
            print("   将创建新会话")

    if 代理.当前会话id is None:
        代理.启动新会话()
        print(f"📂 新会话已创建（ID: {代理.当前会话id}）")

    print(f"📂 工作目录：{Path(参数.dir).resolve()}")
    print(f"📋 模型：{完整配置['model']}")
    print()

    # ── 5. 启动 Textual 应用 ───────────────────────
    print("🐋 正在启动终端界面...")
    print()

    from 源码.界面.应用 import UI智能鲸鱼应用

    应用 = UI智能鲸鱼应用(工作目录=参数.dir)
    应用.代理 = 代理

    try:
        应用.run()
    except KeyboardInterrupt:
        print("\n👋 再见！鲸鱼游走了...")
    finally:
        代理.关闭()


# ── 直接运行入口 ──────────────────────────────────────

if __name__ == "__main__":
    main()
