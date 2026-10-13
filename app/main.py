from flask import Blueprint, render_template
from flask_login import login_required

from app.stats import dashboard_stats, summary

bp = Blueprint("main", __name__)


@bp.get("/")
def landing():
    return render_template("landing.html", figures=summary())


@bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", figures=dashboard_stats())
