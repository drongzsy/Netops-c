import os
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import DATABASE_URL

_engine_args: dict = {}
if DATABASE_URL.startswith("mysql"):
    _engine_args.update(pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=3600)

engine = create_engine(DATABASE_URL, **_engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_database() -> None:
    """Create the database if it doesn't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        return
    except Exception:
        pass
    # Fallback: create DB via root
    from urllib.parse import urlparse
    root_url = os.getenv("MYSQL_ROOT_URL", "mysql+pymysql://root:root123@localhost:3306/mysql")
    parsed = urlparse(DATABASE_URL)
    db_name = parsed.path.lstrip("/").split("?")[0]
    root_engine = create_engine(root_url)
    with root_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()
    root_engine.dispose()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    ensure_database()
    Base.metadata.create_all(bind=engine)
