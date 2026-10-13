from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import Integer, cast, func

from app.idcard import build_id_pdf, download_name
from app.members import _filters, association_choices, filtered_members
from app.models import Member

bp = Blueprint("cards", __name__, url_prefix="/print")


def qurl(**updates):
    params = request.args.to_dict(flat=True)
    for key, value in updates.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    return url_for("cards.index", **params)


def _ordered(ids):
    column = cast(func.nullif(func.regexp_replace(Member.body_number, "[^0-9]", "", "g"), ""), Integer)
    return (
        Member.query.filter(Member.id.in_(ids))
        .order_by(column.asc(), Member.body_number.asc())
        .all()
    )


def pdf_response(members):
    try:
        payload = build_id_pdf(members)
    except FileNotFoundError:
        flash("The ID template could not be opened. Printing is unavailable.", "error")
        return redirect(request.referrer or url_for("cards.index"))
    name = download_name(members)
    response = Response(payload, mimetype="application/pdf")
    response.headers["Content-Disposition"] = f'inline; filename="{name}"'
    return response


@bp.get("/")
@login_required
def index():
    filters = _filters()
    mode = request.args.get("mode") or "single"
    if mode not in {"single", "bulk"}:
        mode = "single"
    page = request.args.get("page", 1, type=int) or 1
    pagination = filtered_members(filters).paginate(page=page, per_page=12, error_out=False)
    return render_template(
        "print/index.html",
        mode=mode,
        pagination=pagination,
        associations=association_choices(),
        qurl=qurl,
        has_filter=any(filters[key] for key in ("q", "association", "kind", "status")),
        **filters,
    )


@bp.post("/")
@login_required
def create():
    scope = request.form.get("scope") or "selected"
    if scope == "matching":
        members = filtered_members(_filters(request.form)).all()
        if not members:
            flash("No records match this search.", "error")
            return redirect(url_for("cards.index", mode="bulk"))
        return pdf_response(members)

    raw_ids = request.form.getlist("member_id")
    ids = []
    for item in raw_ids:
        if item.isdigit():
            ids.append(int(item))
    ids = list(dict.fromkeys(ids))
    if not ids:
        flash("Select a record to print.", "error")
        mode = "bulk" if request.form.get("mode") == "bulk" else "single"
        return redirect(url_for("cards.index", mode=mode))
    members = _ordered(ids)
    if not members:
        flash("Those records are no longer in the registry.", "error")
        return redirect(url_for("cards.index"))
    return pdf_response(members)
