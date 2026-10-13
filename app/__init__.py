import os
from datetime import timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect
from sqlalchemy.exc import OperationalError

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = "auth.login"
login_manager.login_message = "Sign in to open the registry."
login_manager.login_message_category = "info"
MANILA = ZoneInfo("Asia/Manila")


def create_app():
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    from app.config import Config

    app.config.from_object(Config)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.auth import bp as auth_bp
    from app.cards import bp as cards_bp
    from app.main import bp as main_bp
    from app.members import bp as members_bp
    from app.users import bp as users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(users_bp)

    @app.template_filter("manila")
    def manila(value, fmt="%d %b %Y, %I:%M %p"):
        if not value:
            return "—"
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(MANILA).strftime(fmt)

    @app.context_processor
    def inject_registry():
        return {"record_year": app.config["RECORD_YEAR"]}

    @app.before_request
    def bootstrap_seed():
        if app.extensions.get("motorela_seeded"):
            return None
        if request.endpoint == "static":
            return None
        from app.seed import ensure_seeded

        ensure_seeded()
        app.extensions["motorela_seeded"] = True
        return None

    @app.before_request
    def require_password_change():
        if not current_user.is_authenticated or not current_user.must_change_password:
            return None
        if request.endpoint in {"auth.account", "auth.logout", "static"}:
            return None
        return redirect(url_for("auth.account"))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def missing(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_error):
        flash("That photograph is larger than 3 MB.", "error")
        return redirect(request.referrer or url_for("members.index"))

    @app.errorhandler(CSRFError)
    def csrf_failed(_error):
        flash("The form expired. Sign in again and retry.", "error")
        return redirect(url_for("auth.login"))

    @app.errorhandler(OperationalError)
    def database_down(_error):
        try:
            db.session.rollback()
        except Exception:
            pass
        return render_template("errors/db.html"), 503

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response

    import click

    @app.cli.command("seed")
    @click.option("--replace", is_flag=True, help="Delete registry rows and import the workbook again.")
    @click.option("--yes", is_flag=True, help="Confirm replacement of existing rows.")
    def seed_command(replace, yes):
        from app.seed import ensure_users, import_members

        with app.app_context():
            db.create_all()
            ensure_users()
            if replace and not yes:
                raise click.ClickException("Add --yes to replace existing registry rows.")
            count = import_members(replace=replace)
            click.echo(f"Imported {count} registry rows.")

    return app
