"""
文件面板
=======
左侧文件树面板，展示项目文件结构。

点击文件自动触发查看请求。

用法：
    panel = 文件面板(".")
    panel.文件被点击_callback = lambda path: print(f"查看 {path}")
"""

import os
from pathlib import Path
from typing import Callable, Optional

from textual.widgets import DirectoryTree


class UI文件面板(DirectoryTree):
    """
    项目文件树面板（继承 DirectoryTree）。

    特性：
      - 自动过滤 __pycache__、.git、.venv、node_modules 等目录
      - 点击文件触发自定义回调
      - 隐藏以点开头的隐藏文件
    """

    # 需要过滤的目录名
    _过滤目录 = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "dist",
        "build",
        ".egg-info",
    }

    def __init__(self, 路径: str = ".", **kwargs):
        super().__init__(Path(路径), **kwargs)
        self.文件被点击_callback: Optional[Callable[[str], None]] = None

    # ── 过滤逻辑 ───────────────────────────────────────

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        """
        过滤文件树显示。

        过滤规则：
          - 跳过隐藏文件（以 . 开头）
          - 跳过 _过滤目录 中的目录
          - 跳过二进制文件（图片、编译产物等）
        """
        过滤后 = []
        for 路径 in paths:
            # 跳过隐藏文件/目录
            if 路径.name.startswith("."):
                continue

            # 跳过过滤的目录
            if 路径.is_dir() and 路径.name in self._过滤目录:
                continue

            # 跳过二进制文件后缀
            if 路径.is_file():
                后缀 = 路径.suffix.lower()
                if 后缀 in {".pyc", ".pyo", ".exe", ".dll", ".so", ".bin"}:
                    continue

            过滤后.append(路径)

        return 过滤后

    # ── 点击处理 ───────────────────────────────────────

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ):
        """
        文件被选中时触发，调用自定义回调。

        参数：
            event: 文件选择事件，包含 path 属性
        """
        if self.文件被点击_callback:
            路径 = str(event.path)
            self.文件被点击_callback(路径)
