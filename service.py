"""
Task service — business logic sitting between the API routes and the
repository. It knows nothing about FastAPI or HTTP; it just validates
input and delegates storage to whichever TaskRepository it was given.

This is what makes swapping SQLite for Postgres a one-file change:
main.py and this file never change, only which repository gets
constructed in config.py does.
"""

from repository import TaskRepository, TaskRecord


class InvalidTaskError(ValueError):
    """Raised when task input fails validation (maps to HTTP 400)."""


class TaskNotFoundError(LookupError):
    """Raised when a task id doesn't exist (maps to HTTP 404)."""


class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or title.strip() == "":
            raise InvalidTaskError("title is required and cannot be empty")

    def list_tasks(self) -> list[TaskRecord]:
        return self.repository.list_tasks()

    def get_task(self, task_id: int) -> TaskRecord:
        task = self.repository.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return task

    def create_task(self, title: str, done: bool = False) -> TaskRecord:
        self._validate_title(title)
        return self.repository.create_task(title, done)

    def update_task(self, task_id: int, title: str, done: bool) -> TaskRecord:
        self._validate_title(title)
        task = self.repository.update_task(task_id, title, done)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return task

    def delete_task(self, task_id: int) -> None:
        deleted = self.repository.delete_task(task_id)
        if not deleted:
            raise TaskNotFoundError(f"Task {task_id} not found")
