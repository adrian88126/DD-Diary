from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Flask-SQLAlchemy instance（所有 Model 繼承 db.Model）
db = SQLAlchemy()

# Flask-Login instance
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '請先登入後台管理系統'
login_manager.login_message_category = 'warning'


# 強制 SQLite 啟用外鍵約束（全局監聽）
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
