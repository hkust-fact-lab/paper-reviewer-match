"""
SQLite 数据库连接和表结构。
使用原生 sqlite3，不引入 ORM，保持轻量。
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "reviewmatch.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS papers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            hotcrp_id   TEXT UNIQUE,
            title       TEXT NOT NULL,
            abstract    TEXT,
            authors     TEXT,          -- JSON array of {name, email, institution}
            pdf_path    TEXT,
            topics      TEXT,          -- JSON array of strings
            methods     TEXT,          -- JSON array of strings
            required_expertise TEXT,   -- JSON array of strings
            analysis_status TEXT NOT NULL DEFAULT 'pending',
            -- pending | analyzing | analyzed | assigned | error
            analysis_error TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS reviewers (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            hotcrp_user_id      TEXT UNIQUE,
            name                TEXT NOT NULL,
            email               TEXT UNIQUE NOT NULL,
            institution         TEXT,
            scholar_url         TEXT,
            scholar_confirmed   INTEGER NOT NULL DEFAULT 0,  -- 0=未确认 1=已确认
            fetch_status        TEXT NOT NULL DEFAULT 'pending',
            -- pending | fetching | done | needs_confirmation | error | no_data
            fetch_error         TEXT,
            expertise_topics    TEXT,   -- JSON array
            publications        TEXT,   -- JSON array of {title, year, venue, url}
            load_min            INTEGER DEFAULT 0,
            load_max            INTEGER DEFAULT 15,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS match_scores (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id        INTEGER NOT NULL REFERENCES papers(id),
            reviewer_id     INTEGER NOT NULL REFERENCES reviewers(id),
            total_score     INTEGER NOT NULL,   -- 0-100
            topic_score     INTEGER NOT NULL,
            method_score    INTEGER NOT NULL,
            recency_score   INTEGER NOT NULL,
            rationale       TEXT,
            computed_at     TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(paper_id, reviewer_id)
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id        INTEGER NOT NULL REFERENCES papers(id),
            reviewer_id     INTEGER NOT NULL REFERENCES reviewers(id),
            source          TEXT NOT NULL DEFAULT 'auto',   -- auto | manual
            status          TEXT NOT NULL DEFAULT 'pending', -- pending | confirmed
            assigned_at     TEXT NOT NULL DEFAULT (datetime('now')),
            assigned_by     TEXT,
            UNIQUE(paper_id, reviewer_id)
        );

        CREATE TABLE IF NOT EXISTS conflicts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id        INTEGER NOT NULL REFERENCES papers(id),
            reviewer_id     INTEGER NOT NULL REFERENCES reviewers(id),
            source          TEXT NOT NULL,  -- institution | coauthor | self_reported | manual
            detail          TEXT,
            status          TEXT NOT NULL DEFAULT 'pending',  -- pending | confirmed | rejected
            reported_by     TEXT,
            confirmed_by    TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(paper_id, reviewer_id, source)
        );

        CREATE TABLE IF NOT EXISTS async_tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            type            TEXT NOT NULL,  -- analyze_paper | fetch_reviewer | run_assignment
            ref_id          INTEGER,        -- paper_id or reviewer_id, nullable for run_assignment
            status          TEXT NOT NULL DEFAULT 'pending',  -- pending | running | done | error
            progress        INTEGER NOT NULL DEFAULT 0,       -- 0-100
            result_summary  TEXT,
            error_message   TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            finished_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            hotcrp_user_id  TEXT UNIQUE NOT NULL,
            email           TEXT UNIQUE NOT NULL,
            name            TEXT NOT NULL,
            role            TEXT NOT NULL DEFAULT 'reviewer',  -- admin | reviewer
            reviewer_id     INTEGER REFERENCES reviewers(id),
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS assignment_config (
            id                  INTEGER PRIMARY KEY DEFAULT 1,  -- 单行配置
            reviewers_per_paper INTEGER NOT NULL DEFAULT 3,
            max_papers_per_reviewer INTEGER NOT NULL DEFAULT 15,
            min_papers_per_reviewer INTEGER NOT NULL DEFAULT 0,
            min_score_threshold INTEGER NOT NULL DEFAULT 40,
            coi_same_institution INTEGER NOT NULL DEFAULT 1,  -- 0|1
            coi_coauthor_years  INTEGER NOT NULL DEFAULT 5,
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        );

        INSERT OR IGNORE INTO assignment_config(id) VALUES(1);
        """)
