"""
项目上下文管理器
==============
让 agent 更懂当前项目 —— 扫描文件结构、生成摘要、搜索相关文件。

用法：
    from 源码.核心.上下文 import 项目上下文
    ctx = 项目上下文()
    ctx.扫描项目(".")
    print(ctx.获取项目摘要())
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


class 项目上下文:
    """
    项目上下文管理器。

    负责扫描项目结构、缓存文件信息，
    并提供摘要生成和关键词搜索功能。
    """

    def __init__(self):
        """初始化上下文管理器"""
        self.根目录: Optional[Path] = None
        self._文件信息列表: List[Dict[str, Any]] = []
        self._已扫描: bool = False

    # ── 扫描项目 ───────────────────────────────────────

    # 感兴趣的文件后缀（要收集信息的）
    _关注后缀 = {".py", ".md", ".json", ".toml", ".yaml", ".yml", ".css", ".txt", ".cfg", ".ini"}

    # 需要跳过的目录名
    _忽略目录 = {
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
        ".deepseek-cn",
        "截图",
    }

    def 扫描项目(self, 根目录: str = "."):
        """
        扫描项目目录，收集关键文件信息。

        参数：
            根目录: 项目根目录路径（默认当前目录）

        收集规则：
          - 关注 .py / .md / .json / .toml / .yaml 等关键文件
          - 跳过 __pycache__ / .git / .venv 等目录
          - 每个文件记录：路径、大小、前 5 行预览
        """
        self.根目录 = Path(根目录).resolve()
        self._文件信息列表 = []

        for 文件 in self.根目录.rglob("*"):
            # 跳过隐藏文件
            if 文件.name.startswith(".") and 文件.name not in {".gitignore", ".env.example"}:
                continue

            # 跳过忽略目录
            if any(part in self._忽略目录 for part in 文件.parts):
                continue

            # 只处理关注的后缀
            if not 文件.is_file():
                continue
            if 文件.suffix.lower() not in self._关注后缀:
                continue

            # 收集文件信息
            try:
                文件信息 = 文件.stat()
                相对路径 = str(文件.relative_to(self.根目录)).replace("\\", "/")

                # 读取前 5 行预览
                预览 = ""
                try:
                    with open(文件, "r", encoding="utf-8", errors="replace") as f:
                        行列表 = []
                        for i, 行 in enumerate(f):
                            if i >= 5:
                                break
                            行列表.append(行.rstrip())
                        预览 = "\n".join(行列表)
                except Exception:
                    预览 = "(无法读取)"

                self._文件信息列表.append({
                    "路径": 相对路径,
                    "大小": 文件信息.st_size,
                    "修改时间": 文件信息.st_mtime,
                    "后缀": 文件.suffix.lower(),
                    "预览": 预览,
                })

            except (OSError, PermissionError):
                pass

        # 按路径排序
        self._文件信息列表.sort(key=lambda x: x["路径"])
        self._已扫描 = True

    # ── 获取项目摘要 ───────────────────────────────────

    def 获取项目摘要(self) -> str:
        """
        生成项目文件树摘要。

        返回：
            格式化的项目摘要文本，例如：
            📂 项目：智能鲸鱼
            📁 源码/ (5个子目录)
              ├── 界面/ (4个Python文件)
              ├── 核心/ (3个Python文件)
              ...
            📄 说明.md (2.3KB)
            📊 总计：15个Python文件，2340行代码
        """
        if not self._已扫描:
            self.扫描项目()

        # ── 构建目录树 ────────────────────────────────
        目录树: Dict[str, Any] = {}
        文件统计: Dict[str, int] = {}  # 后缀 → 数量
        总行数 = 0
        总大小 = 0

        for 信息 in self._文件信息列表:
            路径 = 信息["路径"]
            后缀 = 信息["后缀"]
            大小 = 信息["大小"]

            # 统计
            文件统计[后缀] = 文件统计.get(后缀, 0) + 1
            总大小 += 大小

            # 统计行数
            try:
                if 后缀 == ".py":
                    预览行数 = 信息["预览"].count("\n") + 1
                    总行数 += 预览行数
            except Exception:
                pass

            # 构建目录树
            部分 = Path(路径).parts
            当前节点 = 目录树
            for i, 部分名 in enumerate(部分):
                if i == len(部分) - 1:
                    # 叶子节点（文件）
                    if "__文件__" not in 当前节点:
                        当前节点["__文件__"] = []
                    当前节点["__文件__"].append({
                        "名称": 部分名,
                        "大小": 大小,
                        "后缀": 后缀,
                    })
                else:
                    if 部分名 not in 当前节点:
                        当前节点[部分名] = {}
                    当前节点 = 当前节点[部分名]

        # ── 格式化输出 ────────────────────────────────
        输出行: List[str] = []
        项目名 = self.根目录.name if self.根目录 else "项目"
        输出行.append(f"📂 项目：{项目名}")

        # 递归打印目录树
        self._打印目录树(目录树, 输出行, 缩进="")

        # 根目录文件
        if "__文件__" in 目录树:
            for 文件 in 目录树["__文件__"]:
                名称 = 文件["名称"]
                大小 = self._格式化大小(文件["大小"])
                输出行.append(f"📄 {名称} ({大小})")

        输出行.append("")

        # ── 统计汇总 ──────────────────────────────────
        py数量 = 文件统计.get(".py", 0)
        md数量 = 文件统计.get(".md", 0)
        其他数量 = sum(v for k, v in 文件统计.items() if k not in {".py", ".md"})

        汇总 = [f"📊 总计：{py数量} 个 Python 文件"]
        if 总行数 > 0:
            汇总.append(f"约 {总行数} 行 Python 代码")
        if md数量 > 0:
            汇总.append(f"{md数量} 个 Markdown 文档")
        if 其他数量 > 0:
            汇总.append(f"{其他数量} 个其他文件")
        汇总.append(f"总大小 {self._格式化大小(总大小)}")

        输出行.append("，".join(汇总))

        return "\n".join(输出行)

    def _打印目录树(self, 节点: Dict, 输出行: List[str], 缩进: str):
        """
        递归打印目录树。

        参数：
            节点:   当前目录树节点
            输出行: 输出行列表（原地修改）
            缩进:   当前缩进字符串
        """
        # 提取所有子目录
        子目录列表 = [
            (k, v) for k, v in 节点.items()
            if k != "__文件__" and isinstance(v, dict)
        ]

        for i, (名称, 子节点) in enumerate(子目录列表):
            是最后 = (i == len(子目录列表) - 1 and "__文件__" not in 节点)
            前缀 = "└── " if 是最后 else "├── "

            # 统计该目录下的文件
            文件数 = len(子节点.get("__文件__", []))
            子目录数 = len([k for k in 子节点 if k != "__文件__" and isinstance(子节点[k], dict)])

            描述 = []
            if 文件数 > 0:
                描述.append(f"{文件数}个文件")
            if 子目录数 > 0:
                描述.append(f"{子目录数}个子目录")
            描述文本 = f" ({', '.join(描述)})" if 描述 else ""

            输出行.append(f"{缩进}{前缀}📁 {名称}/{描述文本}")

            # 递归
            新缩进 = 缩进 + ("    " if 是最后 else "│   ")
            self._打印目录树(子节点, 输出行, 新缩进)

        # 打印该目录下的文件
        if "__文件__" in 节点:
            for i, 文件 in enumerate(节点["__文件__"]):
                是最后 = (i == len(节点["__文件__"]) - 1)
                前缀 = "└── " if 是最后 else "├── "
                名称 = 文件["名称"]
                大小 = self._格式化大小(文件["大小"])
                后缀图标 = {".py": "🐍", ".md": "📝", ".json": "📋", ".toml": "⚙️", ".css": "🎨"}.get(文件["后缀"], "📄")
                输出行.append(f"{缩进}{前缀}{后缀图标} {名称} ({大小})")

    # ── 获取相关文件 ──────────────────────────────────

    def 获取相关文件(self, 关键词: str) -> List[str]:
        """
        根据关键词搜索相关文件。

        参数：
            关键词: 搜索关键词（匹配文件名和文件内容）

        返回：
            匹配的文件路径列表（相对路径）
        """
        if not self._已扫描:
            self.扫描项目()

        匹配列表: List[str] = []

        for 信息 in self._文件信息列表:
            路径 = 信息["路径"]
            预览 = 信息["预览"]

            # 匹配文件名
            if 关键词.lower() in Path(路径).name.lower():
                匹配列表.append(路径)
                continue

            # 匹配文件内容预览
            if 关键词.lower() in 预览.lower():
                匹配列表.append(路径)
                continue

            # 匹配路径
            if 关键词.lower() in 路径.lower():
                匹配列表.append(路径)

        return 匹配列表

    # ── 获取文件详情 ────────────────────────────────

    def 获取文件详情(self, 文件路径: str) -> Optional[Dict[str, Any]]:
        """
        获取指定文件的详细信息。

        参数：
            文件路径: 相对于项目根目录的文件路径

        返回：
            文件信息字典，未找到返回 None
        """
        if not self._已扫描:
            self.扫描项目()

        # 标准化路径以便跨平台匹配（统一用 / 分隔）
        标准化输入 = str(Path(文件路径)).replace("\\", "/")

        for 信息 in self._文件信息列表:
            if 信息["路径"] == 标准化输入:
                return 信息
        return None

    # ── 工具函数 ──────────────────────────────────────

    @staticmethod
    def _格式化大小(字节数: int) -> str:
        """将字节数转为人类可读的大小字符串"""
        if 字节数 < 1024:
            return f"{字节数}B"
        elif 字节数 < 1024 * 1024:
            return f"{字节数 / 1024:.1f}KB"
        else:
            return f"{字节数 / (1024 * 1024):.2f}MB"

    # ── 重置 ───────────────────────────────────────────

    def 重置(self):
        """清除所有缓存数据"""
        self.根目录 = None
        self._文件信息列表 = []
        self._已扫描 = False
