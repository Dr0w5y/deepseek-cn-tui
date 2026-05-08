"""
图片解析器
=========
图片处理工具：支持 Base64 编码和图片信息提取。
支持的格式：PNG、JPG/JPEG、WEBP、GIF（静态帧）

用法：
    from 源码.解析器.图片解析器 import 图片转Base64, 获取图片信息
    b64 = 图片转Base64("截图.png")
    info = 获取图片信息("照片.jpg")
"""

import base64
import os
from pathlib import Path
from typing import Any, Dict


# ── 支持的格式 ─────────────────────────────────────────
_支持的格式 = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _检查文件(文件路径: str) -> Path | None:
    """
    检查文件是否存在且格式受支持。

    返回:
        Path 对象（通过检查），或 None（未通过，已打印错误）
    """
    路径 = Path(文件路径)

    if not 路径.exists():
        print(f"❌ 文件不存在：{文件路径}")
        return None

    if not 路径.is_file():
        print(f"❌ 路径不是文件：{文件路径}")
        return None

    后缀 = 路径.suffix.lower()
    if 后缀 not in _支持的格式:
        print(f"❌ 不支持的图片格式（{后缀}），支持：{', '.join(sorted(_支持的格式))}")
        return None

    return 路径


def 图片转Base64(文件路径: str) -> str:
    """
    将图片文件转换为 Base64 编码字符串。

    参数：
        文件路径: 图片文件的路径（相对或绝对）

    返回：
        Base64 编码字符串（不含 data: 前缀）
        失败时返回空字符串，并打印中文错误信息
    """
    路径 = _检查文件(文件路径)
    if 路径 is None:
        return ""

    try:
        with open(路径, "rb") as f:
            图片数据 = f.read()
    except OSError as e:
        print(f"❌ 读取图片文件失败：{e}")
        return ""

    if len(图片数据) == 0:
        print(f"❌ 图片文件为空：{文件路径}")
        return ""

    try:
        return base64.b64encode(图片数据).decode("ascii")
    except Exception as e:
        print(f"❌ Base64 编码失败：{e}")
        return ""


def _格式化文件大小(字节数: int) -> str:
    """将字节数转为人类可读的大小字符串"""
    if 字节数 < 1024:
        return f"{字节数}B"
    elif 字节数 < 1024 * 1024:
        return f"{字节数 / 1024:.1f}KB"
    else:
        return f"{字节数 / (1024 * 1024):.2f}MB"


def 获取图片信息(文件路径: str) -> Dict[str, Any]:
    """
    获取图片文件的格式和尺寸信息。

    参数：
        文件路径: 图片文件的路径（相对或绝对）

    返回：
        字典，包含以下字段：
            "格式"   — 图片格式（如 "png"、"jpeg"）
            "宽度"   — 图片宽度（像素）
            "高度"   — 图片高度（像素）
            "大小"   — 文件大小（人类可读，如 "2.3MB"）
            "文件路径" — 原始文件路径

        失败时返回包含 "错误" 字段的字典
    """

    # ── 文件大小 ────────────────────────────────────────
    文件大小_str = "未知"

    try:
        字节数 = os.path.getsize(文件路径)
        文件大小_str = _格式化文件大小(字节数)
    except OSError:
        pass

    # ── 格式检查 ────────────────────────────────────────
    路径 = _检查文件(文件路径)
    if 路径 is None:
        return {
            "错误": f"无法读取图片：{文件路径}",
            "文件路径": 文件路径,
        }

    # ── 用 Pillow 读取图片信息 ─────────────────────────
    try:
        from PIL import Image
    except ImportError:
        return {
            "错误": "缺少 Pillow 依赖，请执行：pip install Pillow",
            "文件路径": 文件路径,
        }

    try:
        with Image.open(路径) as img:
            宽度, 高度 = img.size

            # 格式名称统一小写
            格式 = (img.format or 路径.suffix.lstrip(".")).lower()
            if 格式 == "jpeg":
                格式 = "jpg"

            return {
                "格式": 格式,
                "宽度": 宽度,
                "高度": 高度,
                "大小": 文件大小_str,
                "文件路径": str(路径),
            }

    except Exception as e:
        print(f"❌ 无法读取图片信息：{e}")
        return {
            "错误": f"图片解析失败：{e}",
            "文件路径": 文件路径,
        }
