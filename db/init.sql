-- Runs automatically the FIRST time the Postgres container starts with an
-- empty data volume (Postgres's docker-entrypoint-initdb.d convention —
-- see docker-compose.yml). It will NOT re-run on later restarts, which is
-- exactly why the seed rows below use "only on first run" semantics.

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);

-- Seed data — only happens because this script only runs once, on an
-- empty volume. INSERT ... WHERE NOT EXISTS keeps it idempotent even if
-- the script were ever re-run by hand against a non-empty table.
INSERT INTO tasks (title, done)
SELECT * FROM (VALUES
    ('Buy milk', FALSE),
    ('Walk the dog', TRUE),
    ('Write report', FALSE)
) AS seed(title, done)
WHERE NOT EXISTS (SELECT 1 FROM tasks);
