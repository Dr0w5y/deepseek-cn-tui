#!/bin/bash
# ═══════════════════════════════════════════════════
#  智能鲸鱼 一键启动脚本 (Mac/Linux)
#  自动检测环境、安装依赖、启动应用
# ═══════════════════════════════════════════════════

set -e

# 切换到脚本所在目录
cd "$(dirname "$0")"

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║      🐋 智 能 鲸 鱼            ║"
echo "  ║   deepseek-cn v0.1.0           ║"
echo "  ║   终端里的中文编程搭子          ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# ── 第1步：检测 Python ──────────────────────────
echo "[1/3] 检测 Python 环境..."

PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "  ❌ 未找到 Python，请先安装 Python 3.10+"
    echo "  📥 Ubuntu/Debian: sudo apt install python3"
    echo "  📥 macOS:         brew install python3"
    echo "  📥 官方:          https://www.python.org/downloads/"
    echo ""
    exit 1
fi

$PYTHON_CMD --version
echo "  ✅ Python 已就绪"
echo ""

# ── 第2步：检测并安装依赖 ──────────────────────
echo "[2/3] 检测依赖包..."

if $PYTHON_CMD -c "import textual, openai" 2>/dev/null; then
    echo "  ✅ 依赖包已就绪"
else
    echo "  ⏳ 正在安装依赖包（首次运行需要一点时间）..."
    echo ""
    $PYTHON_CMD -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
    $PYTHON_CMD -m pip install -r requirements.txt
    echo ""
    echo "  ✅ 依赖安装完成"
fi
echo ""

# ── 第3步：启动智能鲸鱼 ──────────────────────
echo "[3/3] 🚀 正在启动智能鲸鱼..."
echo ""
echo "  ┌────────────────────────────────────────┐"
echo "  │  首次使用需要输入 DeepSeek API 密钥     │"
echo "  │  获取地址：platform.deepseek.com       │"
echo "  │  密钥会安全保存在本地 ~/.deepseek-cn/   │"
echo "  └────────────────────────────────────────┘"
echo ""

$PYTHON_CMD -m 源码.主程序 "$@"

echo ""
echo "  👋 鲸鱼游走了~"
