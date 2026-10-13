from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from werkzeug.security import generate_password_hash

from app import db
from app.forms import UserCreateForm, UserEditForm
from app.models import User

bp = Blueprint("users", __name__, url_prefix="/users")


def admin_required(view):
    from functools import wraps

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            return render_template("errors/403.html"), 403
        return view(*args, **kwargs)

    return wrapped


def _active_admins():
    return User.query.filter_by(role="admin", is_active=True).count()


@bp.get("/")
@admin_required
def index():
    users = User.query.order_by(User.role.asc(), User.full_name.asc()).all()
    return render_template("users/index.html", users=users)


@bp.route("/new", methods=["GET", "POST"])
@admin_required
def create():
    form = UserCreateForm()
    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        if User.query.filter(func.lower(User.username) == username).first():
            form.username.errors.append("That username is already in use.")
        else:
            db.session.add(
                User(
                    username=username,
                    full_name=form.full_name.data.strip(),
                    role=form.role.data,
                    password_hash=generate_password_hash(form.password.data),
                    must_change_password=True,
                    is_active=True,
                )
            )
            db.session.commit()
            flash(f"Account {username} was created. They will set a new password at first sign-in.", "success")
            return redirect(url_for("users.index"))
    return render_template("users/form.html", form=form, editing=None)


@bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return render_template("errors/404.html"), 404
    form = UserEditForm(obj=user) if request.method == "GET" else UserEditForm()
    if request.method == "GET":
        form.password.data = ""
        form.confirm_password.data = ""
    if form.validate_on_submit():
        demoting = user.role == "admin" and user.is_active and (
            form.role.data != "admin" or not form.is_active.data
        )
        if user.id == current_user.id and not form.is_active.data:
            form.is_active.errors.append("You cannot deactivate the account you are using.")
        elif demoting and _active_admins() <= 1:
            flash("Keep at least one active administrator.", "error")
        else:
            user.full_name = form.full_name.data.strip()
            user.role = form.role.data
            user.is_active = bool(form.is_active.data)
            if form.password.data:
                user.password_hash = generate_password_hash(form.password.data)
                user.must_change_password = True
            db.session.commit()
            flash(f"{user.username} was updated.", "success")
            return redirect(url_for("users.index"))
    return render_template("users/form.html", form=form, editing=user)
