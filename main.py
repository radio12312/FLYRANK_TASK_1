from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    done: bool

DATABASE = "tasks.db"

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema and seed data."""
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Create tasks table
        cursor.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN DEFAULT 0
            )
        """)

        # Seed with 3 example tasks
        cursor.executemany("""
            INSERT INTO tasks (title, done) VALUES (?, ?)
        """, [
            ("Buy milk", False),
            ("Walk the dog", True),
            ("Write report", False),
        ])

        conn.commit()
        conn.close()

# Initialize database on startup
init_db()

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

# Stage 1: Read endpoints with SQL
@app.get("/tasks")
def list_tasks():
    """Retrieve all tasks. Returns a list of all task objects with their current state."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1], "done": bool(row[2])} for row in rows]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Retrieve a single task by ID. Returns the task object if found, or 404 if not."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return {"id": row[0], "title": row[1], "done": bool(row[2])}

# Stage 2: Create endpoint with SQL
@app.post("/tasks", status_code=201)
def create_task(task: Task):
    """Create a new task. Accepts a task object with a title, assigns a new ID, and returns the created task."""
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, task.done))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"id": new_id, "title": task.title, "done": task.done}

# Stage 3: Update endpoint with SQL
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    """Update an existing task. Replace the task's title and/or done status with the provided values."""
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="title is required and cannot be empty")

    conn = get_db()
    cursor = conn.cursor()

    # Check if task exists
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Update the task
    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (task.title, task.done, task_id))
    conn.commit()
    conn.close()

    return {"id": task_id, "title": task.title, "done": task.done}

# Stage 3: Delete endpoint with SQL
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task by ID. Returns 204 No Content on success, or 404 if task not found."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if task exists
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Delete the task
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
