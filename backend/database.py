"""FireSing SQLite database setup with SQLAlchemy."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path

from .config import DATA_DIR


class Base(DeclarativeBase):
    pass


# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "firesing.db"
engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)

# Enable WAL mode for better concurrent read performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Safe to call multiple times."""
    Base.metadata.create_all(bind=engine)
    _migrate_db()


def _migrate_db():
    """Add columns added after initial schema. Safe to call multiple times."""
    from sqlalchemy import text

    with engine.connect() as conn:
        # Each migration is a hardcoded ALTER TABLE statement so we avoid
        # f-string interpolation of SQL identifiers/values.
        # try/except provides idempotency (column already exists -> no-op).
        try:
            conn.execute(
                text("ALTER TABLE songs ADD COLUMN source VARCHAR DEFAULT 'upload'")
            )
        except Exception:
            pass

        try:
            conn.execute(
                text("ALTER TABLE songs ADD COLUMN source_id VARCHAR DEFAULT NULL")
            )
        except Exception:
            pass

        try:
            conn.execute(
                text("ALTER TABLE songs ADD COLUMN source_url VARCHAR DEFAULT NULL")
            )
        except Exception:
            pass

        try:
            conn.execute(
                text("ALTER TABLE songs ADD COLUMN artist VARCHAR DEFAULT NULL")
            )
        except Exception:
            pass

        try:
            conn.execute(
                text("ALTER TABLE songs ADD COLUMN pipeline_pct INTEGER DEFAULT 0")
            )
        except Exception:
            pass

        try:
            conn.execute(
                text("ALTER TABLE songs ADD COLUMN pipeline_task_id VARCHAR DEFAULT NULL")
            )
        except Exception:
            pass

        try:
            conn.execute(
                text("ALTER TABLE songs ADD COLUMN user_id VARCHAR DEFAULT NULL")
            )
        except Exception:
            pass

        conn.commit()
