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

    migrations = [
        ("songs", "source", "String", "'upload'"),
        ("songs", "source_id", "String", "NULL"),
        ("songs", "source_url", "String", "NULL"),
        ("songs", "artist", "String", "NULL"),
    ]
    with engine.connect() as conn:
        for table, col, col_type, default in migrations:
            try:
                conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type} DEFAULT {default}")
                )
            except Exception:
                pass  # Column already exists
        conn.commit()
