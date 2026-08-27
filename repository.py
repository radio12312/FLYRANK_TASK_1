"""
Repository interface for task storage.

Any storage backend (SQLite, Postgres, in-memory, ...) implements this
same interface. The service layer and API routes depend only on this
abstract contract — they never know which backend is actually running.
"""

from abc import ABC, abstractmethod
from typing import Optional, TypedDict


class TaskRecord(TypedDict):
    id: int
    title: str
    done: bool


class TaskRepository(ABC):
    """Abstract contract every storage backend must fulfill."""

    @abstractmethod
    def init(self) -> None:
        """Create schema and seed data if they don't already exist."""
        raise NotImplementedError

    @abstractmethod
    def list_tasks(self) -> list[TaskRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_task(self, task_id: int) -> Optional[TaskRecord]:
        raise NotImplementedError

    @abstractmethod
    def create_task(self, title: str, done: bool = False) -> TaskRecord:
        raise NotImplementedError

    @abstractmethod
    def update_task(self, task_id: int, title: str, done: bool) -> Optional[TaskRecord]:
        """Returns the updated task, or None if task_id doesn't exist."""
        raise NotImplementedError

    @abstractmethod
    def delete_task(self, task_id: int) -> bool:
        """Returns True if a task was deleted, False if task_id didn't exist."""
        raise NotImplementedError
