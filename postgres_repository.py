"""
Postgres implementation of TaskRepository.

Implements the exact same interface as SQLiteTaskRepository
(repository.py). The service layer and API routes in main.py were
written against that interface and don't know or care which concrete
class is behind it — that's the whole point of the pattern from Stage 1.

Schema creation and seeding is handled by db/init.sql (run automatically
by the Postgres container itself), so init() here is a lightweight
existence check rather than a CREATE TABLE — Postgres in Docker already
guarantees the table exists before the app can connect to it.
"""

import psycopg2
import psycopg2.extras

from repository import TaskRepository, TaskRecord


class PostgresTaskRepository(TaskRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg2.connect(self.database_url)

    def init(self) -> None:
        # db/init.sql (mounted into the Postgres container) already
        # creates the table and seeds it on first startup. We still
        # guard here with CREATE TABLE IF NOT EXISTS so the app doesn't
        # hard-crash if it's ever pointed at a Postgres instance that
        # wasn't bootstrapped with that script.
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def list_tasks(self) -> list[TaskRecord]:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks ORDER BY id")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [{"id": row[0], "title": row[1], "done": bool(row[2])} for row in rows]

    def get_task(self, task_id: int) -> TaskRecord | None:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return None
        return {"id": row[0], "title": row[1], "done": bool(row[2])}

    def create_task(self, title: str, done: bool = False) -> TaskRecord:
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id",
            (title, done),
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {"id": new_id, "title": title, "done": done}

    def update_task(self, task_id: int, title: str, done: bool) -> TaskRecord | None:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return None

        cursor.execute(
            "UPDATE tasks SET title = %s, done = %s WHERE id = %s", (title, done, task_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return {"id": task_id, "title": title, "done": done}

    def delete_task(self, task_id: int) -> bool:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return False

        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
