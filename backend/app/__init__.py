import logging

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


def create_app():
    app = Flask(__name__)

    from .config import Config

    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))

    from .auth import auth_bp
    from .database import db_bp
    from .routes import api_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(db_bp, url_prefix="/api/database")

    with app.app_context():
        from . import models  # noqa: F401

        try:
            db.create_all()
        except Exception:
            db.session.rollback()
        _seed_admin(app)

    from .reader import reader_service

    reader_service.init_app(app)
    reader_service.start()

    from .backup_scheduler import init_scheduler

    init_scheduler(app)

    return app


def _seed_admin(app):
    from .models import User

    username = app.config.get("ADMIN_USERNAME")
    password = app.config.get("ADMIN_PASSWORD")
    if not username or not password:
        return
    existing = User.query.filter_by(username=username).first()
    if existing:
        return
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    app.logger.info("Admin user '%s' created.", username)
