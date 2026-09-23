"""
migrations.py — Safe, non-destructive schema migrations for NyayaSaathi.
"""

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def run_migrations(engine: Engine):
    """
    Run safe, idempotent and non-destructive PostgreSQL migrations.

    - Preserve existing Rights/Judgment history.
    - Ensure user_id ownership columns exist.
    - Create latest_judgments table if it does not already exist.
    """

    migration_sql = text("""
    DO $$
    BEGIN
        -- 1. Add user_id column to rights_queries if missing
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'rights_queries'
              AND column_name = 'user_id'
        ) THEN
            ALTER TABLE rights_queries
            ADD COLUMN user_id INTEGER
            REFERENCES users(id)
            ON DELETE SET NULL;

            CREATE INDEX IF NOT EXISTS ix_rights_queries_user_id
            ON rights_queries (user_id);
        END IF;

        -- 2. Add user_id column to judgment_analyses if missing
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'judgment_analyses'
              AND column_name = 'user_id'
        ) THEN
            ALTER TABLE judgment_analyses
            ADD COLUMN user_id INTEGER
            REFERENCES users(id)
            ON DELETE SET NULL;

            CREATE INDEX IF NOT EXISTS ix_judgment_analyses_user_id
            ON judgment_analyses (user_id);
        END IF;
    END $$;
    """)

    latest_judgments_sql = text("""
    CREATE TABLE IF NOT EXISTS latest_judgments (
        id SERIAL PRIMARY KEY,

        official_id VARCHAR(255) NOT NULL UNIQUE,

        case_title TEXT NOT NULL,
        case_number VARCHAR(255),
        diary_number VARCHAR(100),

        judgment_date TIMESTAMPTZ,
        uploaded_at TIMESTAMPTZ,

        official_pdf_url TEXT NOT NULL,
        source_url TEXT,

        pdf_sha256 VARCHAR(64),

        ai_headline TEXT,
        ai_summary TEXT,

        processing_status VARCHAR(50)
            NOT NULL DEFAULT 'pending',

        processing_error TEXT,

        metadata_json JSONB,

        created_at TIMESTAMPTZ
            NOT NULL DEFAULT NOW(),

        updated_at TIMESTAMPTZ
            NOT NULL DEFAULT NOW()
    );
    """)

    latest_indexes_sql = text("""
    CREATE INDEX IF NOT EXISTS ix_latest_judgments_official_id
        ON latest_judgments (official_id);

    CREATE INDEX IF NOT EXISTS ix_latest_judgments_case_number
        ON latest_judgments (case_number);

    CREATE INDEX IF NOT EXISTS ix_latest_judgments_diary_number
        ON latest_judgments (diary_number);

    CREATE INDEX IF NOT EXISTS ix_latest_judgments_judgment_date
        ON latest_judgments (judgment_date);

    CREATE INDEX IF NOT EXISTS ix_latest_judgments_uploaded_at
        ON latest_judgments (uploaded_at);

    CREATE INDEX IF NOT EXISTS ix_latest_judgments_pdf_sha256
        ON latest_judgments (pdf_sha256);

    CREATE INDEX IF NOT EXISTS ix_latest_judgments_processing_status
        ON latest_judgments (processing_status);
    """)

    try:
        with engine.begin() as conn:
            conn.execute(migration_sql)
            conn.execute(latest_judgments_sql)
            conn.execute(latest_indexes_sql)

        logger.info(
            "Database migrations executed successfully "
            "(user history ownership + latest_judgments verified)."
        )

    except Exception:
        logger.exception("Database migration failed.")
        raise