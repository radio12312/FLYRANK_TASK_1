"""
SQLite implementation of TaskRepository.

Behavior is identical to the raw sqlite3 code that used to live directly
in main.py (Week 3) — it has just been moved behind the TaskRepository
interface so it can be swapped for a different backend without touching
the service or the routes.
"""

import os
import sqlite3

from repository import TaskRepository, TaskRecord


class SQLiteTaskRepository(TaskRepository):
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        if os.path.exists(self.db_path):
            return

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN DEFAULT 0
            )
        """)

        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Buy milk", False),
                ("Walk the dog", True),
                ("Write report", False),
            ],
        )

        conn.commit()
        conn.close()

    def list_tasks(self) -> list[TaskRecord]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": row[0], "title": row[1], "done": bool(row[2])} for row in rows]

    def get_task(self, task_id: int) -> TaskRecord | None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None
        return {"id": row[0], "title": row[1], "done": bool(row[2])}

    def create_task(self, title: str, done: bool = False) -> TaskRecord:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (title, done))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"id": new_id, "title": title, "done": done}

    def update_task(self, task_id: int, title: str, done: bool) -> TaskRecord | None:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            conn.close()
            return None

        cursor.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?", (title, done, task_id)
        )
        conn.commit()
        conn.close()
        return {"id": task_id, "title": title, "done": done}

    def delete_task(self, task_id: int) -> bool:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            conn.close()
            return False

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return True
