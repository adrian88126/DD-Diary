from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase
from app.config import settings

# 建立 SQLite 連線引擎，設定 check_same_thread=False 允許非同步執行緒共用
engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)

# 強制每次 SQLite 連線都啟用外鍵約束 (PRAGMA foreign_keys = ON)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# 建立 Session 類別
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 2.0 基礎宣告類別
class Base(DeclarativeBase):
    pass

def get_db():
    """FastAPI 路由相依性注入用的資料庫 Session 產生器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
