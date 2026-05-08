"""
工具集
=====
Agent 可调用的工具函数集合，全部中文命名。

所有工具函数统一返回 dict，包含操作结果或错误信息。

用法：
    from 源码.核心.工具集 import 读取文件, 写入文件, 执行命令
    result = 读取文件("src/main.py")
"""

import os
import stat
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# ── 文件类型判定 ────────────────────────────────────────

_图片后缀 = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_Word后缀 = {".docx"}
_Excel后缀 = {".xlsx", ".xlsm"}
_PPT后缀 = {".pptx"}

# ── 危险命令列表 ────────────────────────────────────────
# 匹配即拒绝，不区分大小写
_危险命令 = [
    "rm -rf /",
    "rm -rf --no-preserve-root",
    "rm -rf /*",
    "del /f /s",
    "format",
    "mkfs",
    "dd if=",
    ":(){ :|:& };:",
    "> /dev/sda",
    "shutdown",
    "reboot",
    "chmod 777 /",
    "chmod -R 777 /",
]

# ── 危险命令（需确认）───────────────────────────────────
_需确认命令 = [
    "git push --force",
    "git push -f",
    "git reset --hard",
    "chmod 777",
    "chmod -R",
    "rm -rf",
    "rm -r",
    "del /f",
    "pip uninstall",
    "npm uninstall",
    "docker rm",
    "docker rmi",
]


def _格式化文件大小(字节数: int) -> str:
    """将字节数转为人类可读的大小字符串"""
    if 字节数 < 1024:
        return f"{字节数}B"
    elif 字节数 < 1024 * 1024:
        return f"{字节数 / 1024:.1f}KB"
    else:
        return f"{字节数 / (1024 * 1024):.2f}MB"


def _获取文件类型(文件路径: str) -> str:
    """
    根据后缀判断文件类型。

    返回: "图片" / "Word文档" / "Excel文档" / "PPT文档" / "文本"
    """
    后缀 = Path(文件路径).suffix.lower()
    if 后缀 in _图片后缀:
        return "图片"
    elif 后缀 in _Word后缀:
        return "Word文档"
    elif 后缀 in _Excel后缀:
        return "Excel文档"
    elif 后缀 in _PPT后缀:
        return "PPT文档"
    else:
        return "文本"


def _格式化时间(时间戳: float) -> str:
    """将 Unix 时间戳转为 YYYY-MM-DD HH:MM 格式"""
    return datetime.fromtimestamp(时间戳).strftime("%Y-%m-%d %H:%M")


# ══════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════

# ── 工具1：读取文件 ────────────────────────────────────

def 读取文件(文件路径: str) -> Dict[str, Any]:
    """
    读取文件，自动判断类型并调用对应解析器。

    参数：
        文件路径: 文件路径（相对或绝对）

    返回：
        - 图片:  {"类型": "图片", "数据": "<base64>"}
        - Office: {"类型": "文本", "数据": "<解析文本>"}
        - 文本:   {"类型": "文本", "数据": "<文件内容>"}
        - 失败:   {"错误": "❌ ..."}
    """
    路径 = Path(文件路径)

    if not 路径.exists():
        return {"错误": f"❌ 文件不存在：{文件路径}"}

    if not 路径.is_file():
        return {"错误": f"❌ 路径不是文件：{文件路径}"}

    文件类型 = _获取文件类型(文件路径)

    # ── 图片 → 调用图片解析器 ────────────────────────
    if 文件类型 == "图片":
        try:
            from 源码.解析器.图片解析器 import 图片转Base64
            base64_str = 图片转Base64(文件路径)
            if not base64_str:
                return {"错误": f"❌ 图片编码失败：{文件路径}"}
            return {"类型": "图片", "数据": base64_str}
        except ImportError as e:
            return {"错误": f"❌ 图片解析器加载失败：{e}"}
        except Exception as e:
            return {"错误": f"❌ 图片读取失败：{e}"}

    # ── Word → 调用 Word 解析器 ──────────────────────
    if 文件类型 == "Word文档":
        try:
            from 源码.解析器.Word解析器 import 解析Word文档
            文本 = 解析Word文档(文件路径)
            if 文本.startswith("❌"):
                return {"错误": 文本}
            return {"类型": "文本", "数据": 文本}
        except ImportError as e:
            return {"错误": f"❌ Word解析器加载失败：{e}"}
        except Exception as e:
            return {"错误": f"❌ Word文档解析失败：{e}"}

    # ── Excel → 调用 Excel 解析器 ───────────────────
    if 文件类型 == "Excel文档":
        try:
            from 源码.解析器.Excel解析器 import 解析Excel文档
            文本 = 解析Excel文档(文件路径)
            if 文本.startswith("❌"):
                return {"错误": 文本}
            return {"类型": "文本", "数据": 文本}
        except ImportError as e:
            return {"错误": f"❌ Excel解析器加载失败：{e}"}
        except Exception as e:
            return {"错误": f"❌ Excel文档解析失败：{e}"}

    # ── PPT → 调用 PPT 解析器 ───────────────────────
    if 文件类型 == "PPT文档":
        try:
            from 源码.解析器.PPT解析器 import 解析PPT文档
            文本 = 解析PPT文档(文件路径)
            if 文本.startswith("❌"):
                return {"错误": 文本}
            return {"类型": "文本", "数据": 文本}
        except ImportError as e:
            return {"错误": f"❌ PPT解析器加载失败：{e}"}
        except Exception as e:
            return {"错误": f"❌ PPT文档解析失败：{e}"}

    # ── 普通文本 → 直接读取 ─────────────────────────
    try:
        with open(路径, "r", encoding="utf-8") as f:
            内容 = f.read()
        return {"类型": "文本", "数据": 内容}
    except UnicodeDecodeError:
        # UTF-8 失败用 GBK 重试
        try:
            with open(路径, "r", encoding="gbk") as f:
                内容 = f.read()
            return {"类型": "文本", "数据": 内容}
        except Exception as e:
            return {"错误": f"❌ 文件编码无法识别：{e}"}
    except Exception as e:
        return {"错误": f"❌ 读取文件失败：{e}"}


# ── 工具2：写入文件 ────────────────────────────────────

def 写入文件(文件路径: str, 内容: str) -> Dict[str, Any]:
    """
    写入文件，自动创建不存在的父目录。

    参数：
        文件路径: 文件路径（相对或绝对）
        内容:     要写入的文本内容

    返回：
        {"成功": True, "路径": "...", "大小": "1.2KB"}
        或 {"错误": "❌ 写入失败：原因"}
    """
    try:
        路径 = Path(文件路径)

        # 自动创建父目录
        路径.parent.mkdir(parents=True, exist_ok=True)

        with open(路径, "w", encoding="utf-8") as f:
            f.write(内容)

        大小 = 路径.stat().st_size
        return {
            "成功": True,
            "路径": str(路径),
            "大小": _格式化文件大小(大小),
        }
    except PermissionError:
        return {"错误": f"❌ 写入失败：没有权限写入 {文件路径}"}
    except OSError as e:
        return {"错误": f"❌ 写入失败：{e}"}
    except Exception as e:
        return {"错误": f"❌ 写入失败：{e}"}


# ── 工具3：列出目录 ────────────────────────────────────

def 列出目录(路径: str = ".") -> Dict[str, Any]:
    """
    列出指定目录的文件和子目录。

    参数：
        路径: 目录路径（默认当前目录）

    返回：
        {
            "文件": ["a.py", "b.txt", ...],
            "子目录": ["src", "tests", ...],
            "总计": "5个文件，3个目录"
        }
    """
    目录路径 = Path(路径)

    if not 目录路径.exists():
        return {"错误": f"❌ 目录不存在：{路径}"}

    if not 目录路径.is_dir():
        return {"错误": f"❌ 路径不是目录：{路径}"}

    try:
        文件列表: List[str] = []
        目录列表: List[str] = []

        for 条目 in sorted(目录路径.iterdir()):
            if 条目.name.startswith("."):
                continue  # 跳过隐藏文件
            if 条目.is_file():
                文件列表.append(条目.name)
            elif 条目.is_dir():
                目录列表.append(条目.name)

        return {
            "文件": 文件列表,
            "子目录": 目录列表,
            "总计": f"{len(文件列表)}个文件，{len(目录列表)}个目录",
        }
    except PermissionError:
        return {"错误": f"❌ 没有权限访问目录：{路径}"}
    except Exception as e:
        return {"错误": f"❌ 列出目录失败：{e}"}


# ── 工具4：执行命令 ────────────────────────────────────

def 执行命令(命令: str, 需要确认: bool = False) -> Dict[str, Any]:
    """
    执行终端命令，内置安全检查。

    参数：
        命令:   要执行的终端命令
        需要确认: 是否已获用户确认（默认 False）

    返回：
        - 危险命令拒绝: {"错误": "⛔ 此命令可能造成数据丢失，已拒绝执行"}
        - 需确认但未确认: {"需要确认": True, "命令": "...", "警告": "⚠️ ..."}
        - 执行成功: {"输出": "...", "返回码": 0}
        - 执行失败: {"错误": "❌ 命令执行失败：..."}
    """

    命令_小写 = 命令.lower().strip()

    # ── 危险命令 → 直接拒绝 ──────────────────────────
    for 危险 in _危险命令:
        if 危险 in 命令_小写:
            return {"错误": "⛔ 此命令可能造成数据丢失，已拒绝执行"}

    # ── 需确认命令 → 检查是否已确认 ──────────────────
    if not 需要确认:
        for 可疑 in _需确认命令:
            if 可疑 in 命令_小写:
                return {
                    "需要确认": True,
                    "命令": 命令.strip(),
                    "警告": f"⚠️ 此命令可能危险，请确认后执行",
                }

    # ── 执行命令 ─────────────────────────────────────
    try:
        结果 = subprocess.run(
            命令,
            shell=True,
            capture_output=True,
            timeout=30,
            cwd=os.getcwd(),
        )

        # 手动解码以适应 Windows 混合编码环境
        输出 = ""
        if 结果.stdout:
            try:
                输出 += 结果.stdout.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    输出 += 结果.stdout.decode("gbk", errors="replace")
                except Exception:
                    输出 += 结果.stdout.decode("utf-8", errors="replace")
        if 结果.stderr:
            if 输出:
                输出 += "\n"
            try:
                输出 += 结果.stderr.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    输出 += 结果.stderr.decode("gbk", errors="replace")
                except Exception:
                    输出 += 结果.stderr.decode("utf-8", errors="replace")

        return {
            "输出": 输出.strip() or "(无输出)",
            "返回码": 结果.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"错误": "❌ 命令执行超时（30秒）"}
    except Exception as e:
        return {"错误": f"❌ 命令执行失败：{e}"}


# ── 工具5：搜索代码 ────────────────────────────────────

def 搜索代码(关键词: str, 目录: str = ".") -> Dict[str, Any]:
    """
    在指定目录中递归搜索包含关键词的文件。

    参数：
        关键词: 要搜索的文本（支持中文）
        目录:   搜索的根目录（默认当前目录）

    返回：
        {
            "结果": [
                {"文件": "src/main.py", "行号": 10, "内容": "匹配行文本"},
                ...
            ],
            "总计": "找到N处匹配"
        }
    """
    搜索路径 = Path(目录)

    if not 搜索路径.exists():
        return {"错误": f"❌ 目录不存在：{目录}"}

    if not 搜索路径.is_dir():
        return {"错误": f"❌ 路径不是目录：{目录}"}

    匹配结果: List[Dict[str, Any]] = []

    try:
        for 文件 in 搜索路径.rglob("*"):
            # 跳过隐藏文件和目录
            if any(part.startswith(".") for part in 文件.parts):
                continue
            # 跳过常见的二进制/非代码目录
            if any(skip in 文件.parts for skip in [".git", "__pycache__", "node_modules", ".venv", "venv"]):
                continue
            if not 文件.is_file():
                continue
            # 只搜索文本文件（跳过二进制）
            后缀 = 文件.suffix.lower()
            if 后缀 in {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".zip", ".tar", ".gz", ".7z", ".mp3", ".mp4", ".avi"}:
                continue

            try:
                with open(文件, "r", encoding="utf-8", errors="replace") as f:
                    for 行号, 行内容 in enumerate(f, 1):
                        if 关键词 in 行内容:
                            匹配结果.append({
                                "文件": str(文件.relative_to(搜索路径)),
                                "行号": 行号,
                                "内容": 行内容.strip()[:200],  # 限制长度
                            })
            except (OSError, PermissionError):
                pass

        总数 = len(匹配结果)
        return {
            "结果": 匹配结果,
            "总计": f"找到{总数}处匹配",
        }
    except Exception as e:
        return {"错误": f"❌ 搜索失败：{e}"}


# ── 工具6：获取文件信息 ────────────────────────────────

def 获取文件信息(文件路径: str) -> Dict[str, Any]:
    """
    获取文件的元信息。

    参数：
        文件路径: 文件路径（相对或绝对）

    返回：
        {
            "文件名": "main.py",
            "大小": "1.2KB",
            "修改时间": "2026-05-01 12:30",
            "类型": "Python文件"
        }
    """
    路径 = Path(文件路径)

    if not 路径.exists():
        return {"错误": f"❌ 文件不存在：{文件路径}"}

    if not 路径.is_file():
        return {"错误": f"❌ 路径不是文件：{文件路径}"}

    try:
        文件信息 = 路径.stat()
        后缀 = 路径.suffix.lower()

        # ── 类型映射 ─────────────────────────────────
        类型映射 = {
            ".py": "Python文件",
            ".js": "JavaScript文件",
            ".ts": "TypeScript文件",
            ".html": "HTML文件",
            ".css": "CSS文件",
            ".json": "JSON文件",
            ".toml": "TOML配置文件",
            ".yaml": "YAML文件",
            ".yml": "YAML文件",
            ".md": "Markdown文档",
            ".txt": "纯文本文件",
            ".csv": "CSV表格",
            ".sql": "SQL脚本",
            ".sh": "Shell脚本",
            ".bat": "批处理文件",
            ".rs": "Rust文件",
            ".go": "Go文件",
            ".java": "Java文件",
            ".cpp": "C++文件",
            ".c": "C文件",
            ".h": "C头文件",
            **{ext: f"{ext[1:].upper()}图片" for ext in _图片后缀},
            **{ext: "Word文档" for ext in _Word后缀},
            **{ext: "Excel文档" for ext in _Excel后缀},
            **{ext: "PPT文档" for ext in _PPT后缀},
        }
        文件类型 = 类型映射.get(后缀, f"{后缀}文件" if 后缀 else "未知类型")

        return {
            "文件名": 路径.name,
            "大小": _格式化文件大小(文件信息.st_size),
            "修改时间": _格式化时间(文件信息.st_mtime),
            "类型": 文件类型,
        }
    except Exception as e:
        return {"错误": f"❌ 获取文件信息失败：{e}"}
