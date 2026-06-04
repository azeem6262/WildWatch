from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.config import DATABASE_URL
from pathlib import Path

# Ensure the data directory exists
db_path = DATABASE_URL.replace('sqlite:///', '')
Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_migrations(engine):
    from backend.models import tables
    
    with engine.connect() as conn:
        # Check if schema_migrations table exists
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")).fetchone()
        
        if not result:
            # Table doesn't exist. Check if sessions table exists (meaning this is a legacy V1 DB)
            has_sessions = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")).fetchone()
            
            conn.execute(text("CREATE TABLE schema_migrations (version INTEGER)"))
            
            if has_sessions:
                conn.execute(text("INSERT INTO schema_migrations (version) VALUES (1)"))
                conn.commit()
                current_version = 1
            else:
                conn.execute(text("INSERT INTO schema_migrations (version) VALUES (0)"))
                conn.commit()
                current_version = 0
        else:
            current_version = conn.execute(text("SELECT version FROM schema_migrations")).scalar()
            
    # Run iterative migrations
    if current_version < 1:
        tables.Base.metadata.create_all(bind=engine)
        with engine.begin() as conn:
            conn.execute(text("UPDATE schema_migrations SET version = 1"))
            
    if current_version < 2:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE files ADD COLUMN datetime_full DATETIME"))
            conn.execute(text("ALTER TABLE files ADD COLUMN relative_path TEXT"))
            conn.execute(text("ALTER TABLE files ADD COLUMN behaviour TEXT DEFAULT ''"))
            conn.execute(text("UPDATE schema_migrations SET version = 2"))
