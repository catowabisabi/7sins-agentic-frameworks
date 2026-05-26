-- 7Sins Project Manager Schema
-- 基於通用 Manager Schema，適用於 Python 框架

CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN (
        'pending','dispatched','in_progress',
        'qa_pending','qa_passed','qa_failed',
        'done','cancelled','blocked'
    )),
    priority INTEGER DEFAULT 3 CHECK(priority BETWEEN 1 AND 5),
    attempt_count INTEGER DEFAULT 0,
    branch_name TEXT,
    related_files TEXT DEFAULT '[]',
    acceptance_criteria TEXT,
    last_commit TEXT,
    last_qa_report TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS check_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checked_at TEXT DEFAULT (datetime('now')),
    current_commit TEXT,
    git_status TEXT,
    analyze_result TEXT,
    action_taken TEXT,
    summary TEXT
);

CREATE TABLE IF NOT EXISTS dispatch_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    todo_id INTEGER REFERENCES todos(id),
    worker TEXT,
    dispatched_at TEXT DEFAULT (datetime('now')),
    order_text TEXT,
    result_summary TEXT,
    git_commit_before TEXT,
    git_commit_after TEXT
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status);
CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority);
CREATE INDEX IF NOT EXISTS idx_dispatch_todo ON dispatch_history(todo_id);
CREATE INDEX IF NOT EXISTS idx_check_runs_time ON check_runs(checked_at);

-- Views
CREATE VIEW IF NOT EXISTS v_active_todos AS
SELECT id, title, status, priority, attempt_count, branch_name,
       related_files, acceptance_criteria, last_commit, created_at, updated_at
FROM todos
WHERE status IN ('pending','dispatched','in_progress','qa_pending','qa_failed','blocked')
ORDER BY priority DESC, created_at ASC;

CREATE VIEW IF NOT EXISTS v_recent_dispatch AS
SELECT d.id, d.todo_id, t.title, d.worker, d.dispatched_at, d.result_summary
FROM dispatch_history d
JOIN todos t ON d.todo_id = t.id
ORDER BY d.dispatched_at DESC
LIMIT 20;

-- Initial meta
INSERT OR IGNORE INTO meta (key, value) VALUES ('project_name', '7Sins');
INSERT OR IGNORE INTO meta (key, value) VALUES ('last_full_audit', '');
