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
    """Root endpoint describing the API."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Stage 2: Read endpoints
@app.get("/tasks")
def list_tasks():
    """List all tasks."""
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a single task by ID."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# Stage 3: Create endpoint
@app.post("/tasks", status_code=201)
def create_task(task: Task):
    """Create a new task."""
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    # Find next free ID
    new_id = max([t["id"] for t in tasks]) + 1 if tasks else 1
    new_task = {"id": new_id, "title": task.title, "done": False}
    tasks.append(new_task)
    return new_task

# Stage 4: Update endpoint
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    """Update a task's title and/or done status."""
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
    """Delete a task."""
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
