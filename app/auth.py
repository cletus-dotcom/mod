from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.forms import AccountForm, LoginForm
from app.models import User

bp = Blueprint("auth", __name__)


def _safe_next(target):
    if not target:
        return url_for("main.dashboard")
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/"):
        return url_for("main.dashboard")
    return target


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.must_change_password:
            return redirect(url_for("auth.account"))
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        user = User.query.filter(func.lower(User.username) == username).first()
        if user and user.is_active and check_password_hash(user.password_hash, form.password.data):
            from app.models import utcnow

            user.last_login_at = utcnow()
            db.session.commit()
            login_user(user, remember=form.remember.data)
            if user.must_change_password:
                return redirect(url_for("auth.account"))
            return redirect(_safe_next(request.args.get("next")))
        flash("Those credentials do not match an active registry account.", "error")
    return render_template("login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You are signed out.", "info")
    return redirect(url_for("main.landing"))


@bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = AccountForm(obj=current_user if request.method == "GET" else None)
    if request.method == "GET":
        form.new_password.data = ""
        form.confirm_password.data = ""
    if form.validate_on_submit():
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            form.current_password.errors.append("The current password is not correct.")
        elif current_user.must_change_password and not form.new_password.data:
            form.new_password.errors.append("Set a new password to continue.")
        elif form.new_password.data and form.new_password.data == form.current_password.data:
            form.new_password.errors.append("Choose a password different from the one you just used.")
        else:
            current_user.full_name = form.full_name.data.strip()
            if form.new_password.data:
                current_user.password_hash = generate_password_hash(form.new_password.data)
                current_user.must_change_password = False
            db.session.commit()
            flash("Your account was updated.", "success")
            if not current_user.must_change_password:
                return redirect(url_for("main.dashboard"))
    return render_template("account.html", form=form)
