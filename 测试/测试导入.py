"""
测试所有模块导入
================
逐个导入项目所有模块，验证导入链完整无误。
"""

import sys
import traceback
from pathlib import Path
from typing import List, Tuple

# 确保项目根目录在 sys.path 中
_项目根目录 = Path(__file__).resolve().parent.parent
if str(_项目根目录) not in sys.path:
    sys.path.insert(0, str(_项目根目录))

# ── 结果收集 ────────────────────────────────────────
成功列表: List[str] = []
失败列表: List[Tuple[str, str]] = []

def 测试导入(模块名: str, 导入语句: str):
    """执行一次导入测试"""
    try:
        exec(导入语句)
        成功列表.append(模块名)
        print(f"✅ {模块名}")
    except Exception:
        error = traceback.format_exc().strip().split("\n")[-1]
        失败列表.append((模块名, error))
        print(f"❌ {模块名} — {error}")


print("=" * 60)
print("  智能鲸鱼 — 模块导入测试")
print("=" * 60)
print()

# ── 第1层：基础模块（无内部依赖） ────────────────────
print("【第1层：基础模块】")

测试导入("源码               ", "from 源码 import __version__")
测试导入("源码.配置          ", "from 源码.配置 import get_config")
测试导入("源码.核心.提示词    ", "from 源码.核心.提示词 import 获取系统提示词")
测试导入("源码.解析器.Word解析器", "from 源码.解析器.Word解析器 import 解析Word文档")
测试导入("源码.解析器.Excel解析器", "from 源码.解析器.Excel解析器 import 解析Excel文档")
测试导入("源码.解析器.PPT解析器", "from 源码.解析器.PPT解析器 import 解析PPT文档")
测试导入("源码.解析器.图片解析器", "from 源码.解析器.图片解析器 import 图片转Base64, 获取图片信息")

print()

# ── 第2层：依赖基础模块 ──────────────────────────────
print("【第2层：中间模块】")

测试导入("源码.存储.数据库    ", "from 源码.存储.数据库 import 聊天数据库")
测试导入("源码.接口.深度求索接口", "from 源码.接口.深度求索接口 import 深度求索客户端")
测试导入("源码.核心.工具集    ", "from 源码.核心.工具集 import 读取文件, 写入文件, 列出目录, 执行命令, 搜索代码, 获取文件信息")
测试导入("源码.核心.上下文    ", "from 源码.核心.上下文 import 项目上下文")

print()

# ── 第3层：依赖中间模块 ──────────────────────────────
print("【第3层：高级模块】")

测试导入("源码.核心.代理      ", "from 源码.核心.代理 import 智能鲸鱼代理")

print()

# ── 第4层：界面模块（依赖 Textual） ──────────────────
print("【第4层：界面模块】")
try:
    import textual
    版 = textual.__version__
    print(f"   Textual 版本: {版}")
    测试导入("源码.界面.对话面板  ", "from 源码.界面.对话面板 import UI对话面板")
    测试导入("源码.界面.输入框    ", "from 源码.界面.输入框 import UI输入框")
    测试导入("源码.界面.文件面板  ", "from 源码.界面.文件面板 import UI文件面板")
    测试导入("源码.界面.应用      ", "from 源码.界面.应用 import UI智能鲸鱼应用")
except ImportError:
    print("   ⚠️ Textual 未安装，跳过界面模块测试")

print()

# ── 第5层：入口模块 ──────────────────────────────────
print("【第5层：入口模块】")

测试导入("源码.主程序        ", "from 源码.主程序 import main, 解析命令行参数, 版本号")

print()

# ── 统计 ────────────────────────────────────────────
总数 = len(成功列表) + len(失败列表)
print("=" * 60)
print(f"  结果：{len(成功列表)}/{总数} 通过")

if 失败列表:
    print(f"\n  ❌ 失败详情：")
    for 模块, 错误 in 失败列表:
        print(f"     - {模块}: {错误}")
    sys.exit(1)
else:
    print("  🎉 全部模块导入成功！")
    print("=" * 60)
