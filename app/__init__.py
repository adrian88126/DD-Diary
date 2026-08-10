"""VTSong Database — Flask Application Factory"""
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── 初始化擴充套件 ──
    db.init_app(app)
    login_manager.init_app(app)

    # ── 匯入 ORM Models（確保 SQLAlchemy 註冊） ──
    with app.app_context():
        from app import models  # noqa: F401

    # ── 註冊 Blueprints ──
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.share import share_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(share_bp, url_prefix='/share')
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # ── 壓縮 (gzip) ──
    try:
        from flask_compress import Compress
        Compress(app)
    except ImportError:
        pass

    # ── 靜態資源快取 ──
    app.config.setdefault('SEND_FILE_MAX_AGE_DEFAULT', 31536000)

    # ── 註冊 Jinja2 全域工具函式 ──
    @app.template_filter('format_seconds')
    def format_seconds_filter(seconds):
        """秒數 → MM:SS 或 HH:MM:SS"""
        if seconds is None:
            return '00:00'
        seconds = int(seconds)
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        if h > 0:
            return f'{h}:{m:02d}:{s:02d}'
        return f'{m}:{s:02d}'

    @app.context_processor
    def inject_globals():
        """注入全域模板變數"""
        from app.i18n import _, get_locale_dict, get_locale
        return {
            'app_name': 'VTSong Database',
            '_': _,
            'current_locale_dict': get_locale_dict(),
            'current_lang': get_locale()
        }

    return app
