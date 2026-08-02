from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    done: bool

# In-memory task list with 3 example tasks
tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": True},
    {"id": 3, "title": "Write report", "done": False},
]

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

# Stage 2: Read endpoints
@app.get("/tasks")
def list_tasks():
    """Retrieve all tasks. Returns a list of all task objects with their current state."""
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Retrieve a single task by ID. Returns the task object if found, or 404 if not."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# Stage 3: Create endpoint
@app.post("/tasks", status_code=201)
def create_task(task: Task):
    """Create a new task. Accepts a task object with a title, assigns a new ID, and returns the created task."""
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    new_id = max([t["id"] for t in tasks]) + 1 if tasks else 1
    new_task = {"id": new_id, "title": task.title, "done": False}
    tasks.append(new_task)
    return new_task

# Stage 4: Update endpoint
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    """Update an existing task. Replace the task's title and/or done status with the provided values."""
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks[i]["title"] = task.title
            tasks[i]["done"] = task.done
            return tasks[i]
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# Stage 4: Delete endpoint
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by ID. Returns 204 No Content on success, or 404 if task not found."""
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# Optional: Stats endpoint
@app.get("/stats")
def get_stats():
    """Get statistics about tasks: total count, completed count, and open count."""
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    open_count = total - done
    return {
        "total": total,
        "done": done,
        "open": open_count
    }

# Optional: Reset to initial state
@app.post("/reset")
def reset_tasks():
    """Reset all tasks to the initial 3 example tasks. Useful for demos and testing."""
    global tasks
    tasks = [
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Walk the dog", "done": True},
        {"id": 3, "title": "Write report", "done": False},
    ]
    return {"status": "reset", "tasks": tasks}

# Optional: Filter tasks by done status
@app.get("/tasks/filter/by-status")
def filter_by_status(done: Optional[bool] = None):
    """Filter tasks by completion status. Use ?done=true or ?done=false."""
    if done is None:
        return tasks
    return [t for t in tasks if t["done"] == done]
