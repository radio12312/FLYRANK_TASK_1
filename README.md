# Task API — A Docker + Postgres–Backed CRUD API

A RESTful API for managing tasks, backed by PostgreSQL running in Docker. Built with FastAPI to demonstrate CRUD operations, HTTP status codes, request validation, Swagger UI documentation, layered architecture, and containerized local infrastructure.

**Week 4 Update:** Storage moved from SQLite (Week 3) to Postgres running in Docker, with a persistent volume. `docker compose up` starts the whole stack — app + database — with one command. **The switch from SQLite to Postgres changed exactly one thing: which repository class gets constructed in `main.py`.** `service.py` and every route are byte-for-byte the same as Week 3 — see [Architecture](#architecture--why-the-swap-was-one-file) below for how and why.

## Quick Start (Docker + Postgres — recommended)

### One Command to Run

```bash
git clone https://github.com/radio12312/FLYRANK_TASK_1.git
cd FLYRANK_TASK_1
cp .env.example .env
docker compose up
```

**What happens:**
1. Docker builds the app image and pulls `postgres:16-alpine`
2. Postgres starts first; the app waits for it to report healthy (`depends_on: condition: service_healthy`)
3. On Postgres's **first** start against an empty volume, `db/init.sql` runs automatically: creates the `tasks` table and inserts 3 seed rows
4. App container starts, connects to Postgres over the internal Docker network, and serves the API

**URLs (default ports — override in `.env` if they clash with something already running on your machine):**
- API: [http://localhost:8020](http://localhost:8020)
- Swagger UI: [http://localhost:8020/docs](http://localhost:8020/docs)
- Postgres (for a DB client): `localhost:5433`, db `tasks`, user/password `taskapi` / `taskapi`

**Data persists** in the named Docker volume `pgdata`. Stop and restart the stack as many times as you like:

```bash
docker compose down    # stops + removes containers, KEEPS the volume (data survives)
docker compose up      # recreates containers, same data is still there

docker compose down -v # add -v only if you want to wipe the volume and start fresh
```

### Explore the API

```bash
curl http://localhost:8020/tasks
curl http://localhost:8020/tasks/1
curl -X POST http://localhost:8020/tasks -H "Content-Type: application/json" -d '{"id":0,"title":"Buy groceries","done":false}'
curl -X PUT http://localhost:8020/tasks/1 -H "Content-Type: application/json" -d '{"id":1,"title":"Buy groceries and cook","done":false}'
curl -X DELETE http://localhost:8020/tasks/1
curl http://localhost:8020/health
```

---

## Quick Start (SQLite, no Docker — Week 3 fallback)

The original SQLite path from Week 3 still works, for a quick local check without Docker:

```bash
git clone https://github.com/radio12312/FLYRANK_TASK_1.git
cd FLYRANK_TASK_1
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Force the SQLite backend (default DB_BACKEND in .env is "postgres")
# Windows PowerShell:
$env:DB_BACKEND="sqlite"; uvicorn main:app --reload
# Mac/Linux:
DB_BACKEND=sqlite uvicorn main:app --reload
```

`tasks.db` creates automatically with 3 seeded tasks at `http://localhost:8000`.

---

## API Endpoints

| Method | Path | Status | Description |
|--------|------|--------|-------------|
| GET | `/` | 200 | API info and available endpoints |
| GET | `/health` | 200 | Server health check |
| GET | `/tasks` | 200 | List all tasks |
| GET | `/tasks/{id}` | 200/404 | Get a single task; 404 if not found |
| POST | `/tasks` | 201/400 | Create a new task; 400 if title is empty |
| PUT | `/tasks/{id}` | 200/400/404 | Update a task; 400 if title invalid, 404 if not found |
| DELETE | `/tasks/{id}` | 204/404 | Delete a task; 204 no content, 404 if not found |

### Task Object

```json
{
  "id": 1,
  "title": "Buy milk",
  "done": false
}
```

---

## Example: Full CRUD Cycle (against the Docker stack)

### 1. Create a task

```bash
$ curl -i -X POST http://localhost:8020/tasks \
  -H "Content-Type: application/json" \
  -d '{"id":0,"title":"Learn Postgres","done":false}'

HTTP/1.1 201 Created
content-type: application/json
content-length: 46

{"id":4,"title":"Learn Postgres","done":false}
```

### 2. List all tasks

```bash
$ curl http://localhost:8020/tasks

[{"id":1,"title":"Buy milk","done":false},{"id":2,"title":"Walk the dog","done":true},{"id":3,"title":"Write report","done":false},{"id":4,"title":"Learn Postgres","done":false}]
```

### 3. Get a single task

```bash
$ curl http://localhost:8020/tasks/4

{"id":4,"title":"Learn Postgres","done":false}
```

### 4. Update the task

```bash
$ curl -X PUT http://localhost:8020/tasks/4 \
  -H "Content-Type: application/json" \
  -d '{"id":4,"title":"Learn Postgres and Docker","done":true}'

{"id":4,"title":"Learn Postgres and Docker","done":true}
```

### 5. Delete the task

```bash
$ curl -i -X DELETE http://localhost:8020/tasks/4

HTTP/1.1 204 No Content
```

---

## Swagger UI

Open [http://localhost:8020/docs](http://localhost:8020/docs) (Docker/Postgres) or [http://localhost:8000/docs](http://localhost:8000/docs) (SQLite fallback) in your browser to see interactive API documentation with "Try it out" buttons for each endpoint. Swagger UI reads the OpenAPI schema auto-generated by FastAPI.

**Features in Swagger UI:**
- View all endpoints with their methods and descriptions
- See request/response schemas
- Try each endpoint with custom values
- Automatic validation of inputs
- Full CRUD cycle in a visual interface

![Swagger UI Screenshot](swagger-ui-screenshot.png)

---

## Input Validation

The API validates incoming data:

- **Create (POST):** `title` field is required and cannot be empty
- **Update (PUT):** `title` field is required and cannot be empty
- Invalid requests return HTTP 400 Bad Request with an error message

Example validation error (all fields present, `title` empty — this is what actually reaches our validation and returns 400; omitting fields entirely returns FastAPI/Pydantic's own `422` instead):

```bash
$ curl -i -X POST http://localhost:8020/tasks \
  -H "Content-Type: application/json" \
  -d '{"id":0,"title":"","done":false}'

HTTP/1.1 400 Bad Request
content-type: application/json

{"detail":"title is required and cannot be empty"}
```

---

## Status Codes

The API uses standard HTTP status codes:

- **200 OK** — Request succeeded, data returned
- **201 Created** — Resource created successfully
- **204 No Content** — Request succeeded, no content to return (DELETE)
- **400 Bad Request** — Invalid input (empty title, missing fields)
- **404 Not Found** — Resource doesn't exist
- **422 Unprocessable Entity** — Validation error from Pydantic

---

## Architecture — why the swap was one file

The service was deliberately layered so storage could be swapped without touching business logic or HTTP routing:

```
main.py  (FastAPI routes)
   │  picks ONE repository based on config.DB_BACKEND
   ▼
service.py  (TaskService — validation, orchestration; framework-agnostic)
   │  depends only on the abstract interface below
   ▼
repository.py  (TaskRepository — abstract interface: list/get/create/update/delete)
   ▲                                   ▲
   │                                   │
sqlite_repository.py          postgres_repository.py
(SQLiteTaskRepository)         (PostgresTaskRepository)
```

- **`repository.py`** defines the contract every backend must implement.
- **`sqlite_repository.py`** and **`postgres_repository.py`** each implement that same contract — one with `sqlite3`, one with `psycopg2` — and are otherwise interchangeable.
- **`service.py`** validates input (`title` required) and calls whichever repository it was given. It has no idea which database is behind it.
- **`main.py`** is the only place that decides *which* repository to construct, based on `DB_BACKEND` from `.env`:

  ```python
  if config.DB_BACKEND == "postgres":
      from postgres_repository import PostgresTaskRepository
      repository = PostgresTaskRepository(config.DATABASE_URL)
  else:
      repository = SQLiteTaskRepository(config.SQLITE_PATH)
  ```

**Honest accounting of the diff between Week 3 and Week 4:** `main.py` gained this one `if` block (previously it always constructed `SQLiteTaskRepository`), and a new `postgres_repository.py` file was added. `service.py` was not touched at all, and every route function's body is unchanged — they still just call `service.xxx()` and translate `InvalidTaskError`/`TaskNotFoundError` to HTTP 400/404. That is the architecture proving itself: routes and business logic never needed to know Postgres exists.

---

## Environment Configuration (`.env`)

| Variable | Used by | Purpose |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `docker-compose.yml`, `db/init.sql` | Postgres credentials and database name |
| `POSTGRES_PORT` | `docker-compose.yml` | Host port Postgres is published on (default `5433`, not `5432`, in case something else on your machine already uses it) |
| `DATABASE_URL` | `config.py` → `postgres_repository.py` | Connection string used when running `uvicorn` **directly on the host** (outside Docker), e.g. `postgresql://taskapi:taskapi@localhost:5433/tasks` |
| `DB_BACKEND` | `main.py` | `postgres` or `sqlite` — which repository gets constructed |
| `APP_PORT` | `docker-compose.yml` | Host port the app is published on when run via `docker compose up` (default `8020`) |

- `.env` is **gitignored** — it holds your real local values.
- `.env.example` is **committed** — it documents every variable above with comments, so `cp .env.example .env` gets a stranger to a working config immediately.
- When the app runs **inside** `docker-compose` (the `app` service), it does **not** read `DATABASE_URL` from `.env` — `docker-compose.yml` builds it directly from the `POSTGRES_*` vars using the Docker network hostname `db` (container-to-container traffic never goes through `localhost`). The `DATABASE_URL` in `.env` is specifically for running `uvicorn` on the host against the same Postgres container via its published port.

---

## SQL: table creation and seeding

`db/init.sql` is mounted into the Postgres container at `/docker-entrypoint-initdb.d/init.sql` — Postgres's own convention for running init scripts **automatically, exactly once**, the first time it starts against an empty data volume:

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO tasks (title, done)
SELECT * FROM (VALUES
    ('Buy milk', FALSE),
    ('Walk the dog', TRUE),
    ('Write report', FALSE)
) AS seed(title, done)
WHERE NOT EXISTS (SELECT 1 FROM tasks);
```

- **Table auto-created if missing:** `CREATE TABLE IF NOT EXISTS` — also guarded again in `postgres_repository.py` as a fallback if the app is ever pointed at a Postgres instance that wasn't bootstrapped by this script.
- **Seeded only on first run:** because Postgres only executes `docker-entrypoint-initdb.d/*` scripts against a **fresh, empty** volume — on every later `docker compose up`/restart, the volume already has data, so the script does not run again. The `WHERE NOT EXISTS` guard additionally makes it safe even if run by hand twice.
- **Verified:** wiped the volume (`docker compose down -v`), brought the stack back up, and confirmed the table existed with exactly the 3 seed rows — then restarted again and confirmed the count was still 3 (not 6).

---

## Proving persistence (how it was checked)

This is the actual test performed, not a theoretical claim:

1. Started the stack: `docker compose up -d` — confirmed `GET /tasks` returned the 3 seed rows.
2. Created a marker row: `POST /tasks` with `{"title": "Persistence proof row", "done": true}` → got back `201` with `id: 6`.
3. Confirmed it was there: `GET /tasks` showed 4 rows including the marker.
4. **Fully tore down both containers** (not just a restart — actually removed them): `docker compose down` (no `-v`, so the volume was kept).
5. Brought the stack back up from scratch: `docker compose up -d` — new `app` and `db` containers, same volume.
6. `GET /tasks` again → **the marker row was still there.** Also confirmed directly against Postgres with `docker exec task-api-db psql -U taskapi -d tasks -c "SELECT * FROM tasks ORDER BY id;"` to rule out any app-level caching explaining it.
7. Cleaned the marker row back out afterward so the repo's seed state stays exactly 3 rows.

This proves persistence lives in the Docker **volume**, not in the containers — the containers are disposable, the `pgdata` volume is not.

---

## Database Visualization

![Database Screenshot](database-screenshot.png)

*The tasks table stores id, title, and done status. Three example tasks are pre-loaded on first run.*

## Exploring SQL Directly

**Against Postgres (Docker) —** connect with `psql` or any GUI client (DBeaver, TablePlus, pgAdmin, DB Browser for SQLite's Postgres-capable cousins, etc.) using:
- Host: `localhost`, Port: `5433` (or your `POSTGRES_PORT`)
- Database: `tasks`, User/Password: `taskapi` / `taskapi` (or your `.env` values)

Or without installing anything, run queries straight through the running container:

```bash
docker exec -it task-api-db psql -U taskapi -d tasks
```

```sql
-- List all tasks
SELECT * FROM tasks;

-- Only completed tasks
SELECT * FROM tasks WHERE done = true;

-- Count total tasks
SELECT COUNT(*) FROM tasks;

-- Mark all tasks done
UPDATE tasks SET done = true;

-- Delete all completed tasks
DELETE FROM tasks WHERE done = true;
```

**Key insight:** Changes made this way appear instantly through the API — the API and `psql` are reading and writing the exact same Postgres database, there is no syncing involved.

**Against SQLite (Week 3 fallback path) —** open `tasks.db` in [DB Browser for SQLite](https://sqlitebrowser.org/) the same way as before; same idea, same one-source-of-truth guarantee.

---

## Project Structure

```
.
├── main.py                   # FastAPI routes only — picks a repository, calls the service
├── service.py                # TaskService — validation + orchestration, framework-agnostic
├── repository.py             # Abstract TaskRepository interface (the shared contract)
├── sqlite_repository.py      # SQLite implementation of TaskRepository
├── postgres_repository.py    # Postgres implementation of TaskRepository
├── config.py                 # Loads .env via python-dotenv
├── db/init.sql                # Postgres schema + seed data, run once by the container
├── docker-compose.yml         # app + db services, persistent volume
├── Dockerfile                 # Builds the FastAPI app image
├── .dockerignore
├── .env.example               # Committed template — copy to .env
├── .env                       # Gitignored — real local values
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .gitignore
└── venv/                      # Python virtual environment (not committed)
```

---

## Development

### Docker (Postgres)
```bash
docker compose up            # foreground, logs streaming
docker compose up -d         # detached
docker compose up --build    # rebuild the app image after code changes
docker compose down          # stop + remove containers, KEEP the volume
docker compose down -v       # stop + remove containers AND the volume (fresh start)
docker compose logs -f app   # tail app logs
docker compose ps            # container status
```

### Local (SQLite, no Docker)
```bash
DB_BACKEND=sqlite uvicorn main:app --reload
```

### Install more dependencies
```bash
pip install <package-name>
pip freeze > requirements.txt  # Update requirements
```

---

## Troubleshooting

**"Bind for 0.0.0.0:5432/8000 failed: port is already allocated"**
- Something else on your machine (another project's container, a local Postgres install, etc.) is already using that port.
- Change `POSTGRES_PORT` and/or `APP_PORT` in `.env` to a free port and re-run `docker compose up`.

**"the input device is not a TTY" / Docker Desktop not responding**
- Make sure Docker Desktop is actually running (`docker info` should succeed) before `docker compose up`.

**"Module not found" errors (SQLite/local path only)**
```bash
# Activate virtual environment first
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

**Want to fully reset the Postgres data**
```bash
docker compose down -v   # removes the pgdata volume too
docker compose up        # db/init.sql runs again on the fresh, empty volume
```

---

## Lessons Learned

1. **CRUD Operations** — Mapping SQL/data operations to HTTP methods (GET, POST, PUT, DELETE)
2. **HTTP Status Codes** — Using 200, 201, 204, 400, 404 to communicate outcomes
3. **Request Validation** — The server never trusts the client; always validate input
4. **In-Memory vs. Persistent** — Data in RAM vanishes on restart; that's why databases exist
5. **API Documentation** — Swagger UI auto-generated from code makes APIs discoverable
6. **Layering pays off later** — A repository interface written in Week 3 for "just SQLite" meant Week 4's Postgres swap touched one `if` block instead of rewriting every route
7. **Containers vs. volumes** — Containers are disposable; a named volume is where the data that matters actually lives
8. **Docker networking** — Container-to-container traffic uses the service name as hostname (`db`), never `localhost`, which inside a container means "this container itself"

---

## Next Steps

- Add authentication: Secure endpoints with JWT tokens or API keys
- Add query parameters: Filter tasks (e.g., `?done=true`) or search by title
- Add a migrations tool (Alembic) instead of a hand-written `init.sql`
- Deploy to the cloud: Host the API + a managed Postgres on AWS/GCP/Azure/Render

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [HTTP Methods & Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP)
- [RESTful API Design](https://restfulapi.net)
- [Swagger UI](https://swagger.io/tools/swagger-ui)

---

**Built for FlyRank Backend Track · Week 2 (A1) → Week 3 (A2, SQLite) → Week 4 (A3, Docker + Postgres)**
