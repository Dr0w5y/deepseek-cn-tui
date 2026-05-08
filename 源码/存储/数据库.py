"""
聊天记录数据库
============
用 SQLite 存储聊天记录，支持多会话管理。

数据库文件：~/.deepseek-cn/chat_history.db

用法：
    from 源码.存储.数据库 import 聊天数据库
    db = 聊天数据库()
    session_id = db.创建会话("Python 脚本编写")
    db.保存消息(session_id, "user", "帮我写个爬虫", 15)
"""

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class 聊天数据库:
    """
    聊天记录数据库管理器。

    自动创建目录和数据库文件，管理两个核心表：
      - 会话表：存储会话元信息
      - 消息表：存储对话中的每条消息
    """

    def __init__(self, 数据库路径: Optional[str] = None):
        """
        初始化数据库连接。

        参数：
            数据库路径: 可选的数据库文件路径（默认为 ~/.deepseek-cn/chat_history.db）
        """
        if 数据库路径:
            self._数据库文件 = Path(数据库路径)
        else:
            self._数据库文件 = Path.home() / ".deepseek-cn" / "chat_history.db"

        # 自动创建目录
        self._数据库文件.parent.mkdir(parents=True, exist_ok=True)

        # 建立连接并初始化表
        self._连接 = sqlite3.connect(
            str(self._数据库文件), check_same_thread=False
        )
        self._连接.execute("PRAGMA journal_mode=WAL")   # WAL 模式，读写并发更好
        self._连接.execute("PRAGMA foreign_keys=ON")     # 启用外键约束

        # 线程锁 — 序列化写入操作，防止多线程同时写入导致数据库损坏
        self._锁 = threading.Lock()
        self._建表()

    # ── 表结构 ─────────────────────────────────────────

    def _建表(self):
        """创建会话表和消息表（如不存在）"""
        self._连接.executescript("""
            CREATE TABLE IF NOT EXISTS 会话表 (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                标题        TEXT    NOT NULL DEFAULT '新对话',
                创建时间    REAL    NOT NULL,
                更新时间    REAL    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS 消息表 (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                会话id      INTEGER NOT NULL,
                角色        TEXT    NOT NULL CHECK(角色 IN ('user', 'assistant', 'system')),
                内容        TEXT    NOT NULL,
                token数     INTEGER NOT NULL DEFAULT 0,
                创建时间    REAL    NOT NULL,
                FOREIGN KEY (会话id) REFERENCES 会话表(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_消息_会话id ON 消息表(会话id);
        """)
        self._连接.commit()

    # ── 会话管理 ───────────────────────────────────────

    def 创建会话(self, 标题: str = "新对话") -> int:
        """
        创建新会话。

        参数：
            标题: 会话标题（默认 "新对话"）

        返回：
            新会话的 ID（整数）
        """
        现在 = time.time()
        with self._锁:
            游标 = self._连接.execute(
                "INSERT INTO 会话表 (标题, 创建时间, 更新时间) VALUES (?, ?, ?)",
                (标题, 现在, 现在),
            )
            self._连接.commit()
        return 游标.lastrowid

    def 获取会话列表(self) -> List[Dict[str, Any]]:
        """
        获取所有会话，按更新时间倒序排列。

        返回：
            会话列表，每项为：
            {
                "id": 1,
                "标题": "Python 脚本编写",
                "创建时间": 1749000000.0,
                "更新时间": 1749000100.0,
                "消息数": 12
            }
        """
        游标 = self._连接.execute("""
            SELECT
                s.id,
                s.标题,
                s.创建时间,
                s.更新时间,
                COUNT(m.id) AS 消息数
            FROM 会话表 s
            LEFT JOIN 消息表 m ON s.id = m.会话id
            GROUP BY s.id
            ORDER BY s.更新时间 DESC
        """)
        return [
            {
                "id": 行[0],
                "标题": 行[1],
                "创建时间": 行[2],
                "更新时间": 行[3],
                "消息数": 行[4],
            }
            for 行 in 游标.fetchall()
        ]

    def 获取会话消息(self, 会话id: int) -> List[Dict[str, Any]]:
        """
        获取指定会话的所有消息，按时间正序排列。

        参数：
            会话id: 会话 ID

        返回：
            消息列表，每项为：
            {
                "id": 42,
                "角色": "user",
                "内容": "帮我写个爬虫",
                "token数": 15,
                "创建时间": 1749000000.0
            }
        """
        游标 = self._连接.execute(
            "SELECT id, 角色, 内容, token数, 创建时间 FROM 消息表 WHERE 会话id = ? ORDER BY 创建时间 ASC",
            (会话id,),
        )
        return [
            {
                "id": 行[0],
                "角色": 行[1],
                "内容": 行[2],
                "token数": 行[3],
                "创建时间": 行[4],
            }
            for 行 in 游标.fetchall()
        ]

    def 删除会话(self, 会话id: int):
        """
        删除指定会话及其所有消息（CASCADE）。

        参数：
            会话id: 会话 ID
        """
        with self._锁:
            self._连接.execute("DELETE FROM 会话表 WHERE id = ?", (会话id,))
            self._连接.commit()

    # ── 消息管理 ───────────────────────────────────────

    def 保存消息(self, 会话id: int, 角色: str, 内容: str, token数: int = 0):
        """
        保存一条消息到指定会话，并更新会话的更新时间。

        参数：
            会话id: 会话 ID
            角色:   消息角色（user / assistant / system）
            内容:   消息文本内容
            token数: 该消息消耗的 Token 数（默认 0）
        """
        现在 = time.time()

        with self._锁:
            # 插入消息
            self._连接.execute(
                "INSERT INTO 消息表 (会话id, 角色, 内容, token数, 创建时间) VALUES (?, ?, ?, ?, ?)",
                (会话id, 角色, 内容, token数, 现在),
            )

            # 更新会话的更新时间
            self._连接.execute(
                "UPDATE 会话表 SET 更新时间 = ? WHERE id = ?",
                (现在, 会话id),
            )

            self._连接.commit()

    # ── 统计 ───────────────────────────────────────────

    def 统计Token用量(self, 会话id: Optional[int] = None) -> int:
        """
        统计 Token 用量。

        参数：
            会话id: 会话 ID；如为 None，则统计全部会话的总用量

        返回：
            Token 总数（整数）
        """
        if 会话id is not None:
            游标 = self._连接.execute(
                "SELECT COALESCE(SUM(token数), 0) FROM 消息表 WHERE 会话id = ?",
                (会话id,),
            )
        else:
            游标 = self._连接.execute(
                "SELECT COALESCE(SUM(token数), 0) FROM 消息表"
            )
        return 游标.fetchone()[0]

    # ── 生命周期 ───────────────────────────────────────

    def 关闭(self):
        """关闭数据库连接"""
        try:
            self._连接.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.关闭()

    def __del__(self):
        self.关闭()
