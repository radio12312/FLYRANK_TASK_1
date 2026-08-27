from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sqlite_repository import SQLiteTaskRepository
from service import TaskService, InvalidTaskError, TaskNotFoundError

app = FastAPI()

class TaskIn(BaseModel):
    id: int
    title: str
    done: bool

# Repository + service wiring.
# Swapping storage backends (e.g. to Postgres) only ever touches this
# block — routes below never change.
repository = SQLiteTaskRepository()
repository.init()
service = TaskService(repository)

# Stage 0 & 1: Root and Health endpoints
@app.get("/")
def read_root():
    """API information endpoint. Returns details about the Task API."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health_check():
    """Health check endpoint. Verifies the server is running and healthy."""
    return {"status": "ok"}

# Stage 1: Read endpoints
@app.get("/tasks")
def list_tasks():
    """Retrieve all tasks. Returns a list of all task objects with their current state."""
    return service.list_tasks()

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Retrieve a single task by ID. Returns the task object if found, or 404 if not."""
    try:
        return service.get_task(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Stage 2: Create endpoint
@app.post("/tasks", status_code=201)
def create_task(task: TaskIn):
    """Create a new task. Accepts a task object with a title, assigns a new ID, and returns the created task."""
    try:
        return service.create_task(task.title, task.done)
    except InvalidTaskError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Stage 3: Update endpoint
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskIn):
    """Update an existing task. Replace the task's title and/or done status with the provided values."""
    try:
        return service.update_task(task_id, task.title, task.done)
    except InvalidTaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Stage 3: Delete endpoint
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by ID. Returns 204 No Content on success, or 404 if task not found."""
    try:
        service.delete_task(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
