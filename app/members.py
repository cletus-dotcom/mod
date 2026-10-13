from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import Integer, cast, func, or_
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms import MemberForm
from app.models import Member, utcnow
from app.utils import clean_text, delete_photo_file, save_photo

bp = Blueprint("members", __name__, url_prefix="/members")

KNOWN_ASSOCIATIONS = ["JAMODA", "JHITGI", "JMOBA", "JMOMBA", "JTRIMODA", "NA", "NJTA"]
SORTS = {
    "body": "body",
    "owner": Member.owner_name,
    "driver": Member.driver_name,
    "association": Member.association,
    "franchise": Member.franchise_number,
    "address": Member.address,
    "status": Member.status,
}


def association_choices():
    found = [name for (name,) in db.session.query(Member.association).distinct() if name]
    return sorted(set(found) | set(KNOWN_ASSOCIATIONS))


def _filters(source=None):
    source = request.args if source is None else source
    term = (source.get("q") or "").strip()[:80]
    association = (source.get("association") or "").strip()[:40]
    kind = source.get("kind") or ""
    status = source.get("status") or ""
    sort = source.get("sort") or "body"
    direction = source.get("dir") or "asc"
    if kind not in {"owner", "hired"}:
        kind = ""
    if status not in {"Active", "Suspended", "Expired"}:
        status = ""
    if sort not in SORTS:
        sort = "body"
    if direction not in {"asc", "desc"}:
        direction = "asc"
    return {
        "q": term,
        "association": association,
        "kind": kind,
        "status": status,
        "sort": sort,
        "direction": direction,
    }


def _like(term):
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def filtered_members(filters):
    query = Member.query
    if filters["q"]:
        pattern = _like(filters["q"])
        query = query.filter(
            or_(
                Member.body_number.ilike(pattern, escape="\\"),
                Member.owner_name.ilike(pattern, escape="\\"),
                Member.driver_name.ilike(pattern, escape="\\"),
                Member.address.ilike(pattern, escape="\\"),
                Member.franchise_number.ilike(pattern, escape="\\"),
                Member.association.ilike(pattern, escape="\\"),
                Member.contact_number.ilike(pattern, escape="\\"),
            )
        )
    if filters["association"] == "__blank__":
        query = query.filter(or_(Member.association.is_(None), Member.association == ""))
    elif filters["association"]:
        query = query.filter(Member.association == filters["association"])
    if filters["kind"] == "owner":
        query = query.filter(Member.driver_is_owner.is_(True))
    elif filters["kind"] == "hired":
        query = query.filter(Member.driver_is_owner.is_(False))
    if filters["status"]:
        query = query.filter(Member.status == filters["status"])
    if filters["sort"] == "body":
        column = cast(func.nullif(func.regexp_replace(Member.body_number, "[^0-9]", "", "g"), ""), Integer)
    else:
        column = SORTS[filters["sort"]]
    ordering = column.desc() if filters["direction"] == "desc" else column.asc()
    return query.order_by(ordering, Member.body_number.asc())


def qurl(**updates):
    params = request.args.to_dict(flat=True)
    params.pop("partial", None)
    for key, value in updates.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    return url_for("members.index", **params)


def _has_filter(filters):
    return any(filters[key] for key in ("q", "association", "kind", "status"))


def _apply_member(member, form):
    member.body_number = clean_text(form.body_number.data, upper=True)
    member.owner_name = clean_text(form.owner_name.data, upper=True)
    member.address = clean_text(form.address.data)
    member.association = clean_text(form.association.data, upper=True) or None
    member.franchise_number = clean_text(form.franchise_number.data, upper=True)
    driver = clean_text(form.driver_name.data, upper=True)
    member.driver_name = driver
    member.driver_is_owner = driver == "OWNER" or driver == member.owner_name
    member.status = form.status.data
    member.contact_number = clean_text(form.contact_number.data) or None
    member.notes = clean_text(form.notes.data, keep_lines=True) or None
    member.record_year = current_app.config["RECORD_YEAR"]
    member.updated_at = utcnow()
    member.updated_by = current_user
    if form.photo.data:
        filename = save_photo(form.photo.data)
        if member.photo_filename:
            delete_photo_file(member.photo_filename)
        member.photo_filename = filename
    elif form.remove_photo.data and member.photo_filename:
        delete_photo_file(member.photo_filename)
        member.photo_filename = None


def _body_taken(body, member=None):
    existing = Member.query.filter(func.upper(Member.body_number) == body).first()
    return existing and (member is None or existing.id != member.id)


@bp.get("/")
@login_required
def index():
    filters = _filters()
    query = filtered_members(filters)
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    if pagination.pages and page > pagination.pages:
        page = pagination.pages
        pagination = query.paginate(page=page, per_page=20, error_out=False)
    context = {
        **filters,
        "pagination": pagination,
        "associations": association_choices(),
        "has_filter": _has_filter(filters),
        "qurl": qurl,
        "window_start": (pagination.page - 1) * pagination.per_page + 1 if pagination.total else 0,
        "window_end": min(pagination.page * pagination.per_page, pagination.total),
    }
    if request.args.get("partial"):
        return render_template("members/_table.html", **context)
    return render_template("members/index.html", **context)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = MemberForm()
    if form.validate_on_submit():
        body = clean_text(form.body_number.data, upper=True)
        if _body_taken(body):
            form.body_number.errors.append("This body number is already in the registry.")
        else:
            member = Member(created_at=utcnow())
            try:
                _apply_member(member, form)
            except ValueError as exc:
                form.photo.errors.append(str(exc))
            else:
                db.session.add(member)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    form.body_number.errors.append("This body number is already in the registry.")
                else:
                    flash(f"{member.body_number} was added to the registry.", "success")
                    return redirect(url_for("members.detail", member_id=member.id))
    return render_template(
        "members/form.html",
        form=form,
        member=None,
        associations=association_choices(),
    )


@bp.get("/<int:member_id>")
@login_required
def detail(member_id):
    member = db.session.get(Member, member_id)
    if member is None:
        return render_template("errors/404.html"), 404
    return render_template("members/detail.html", member=member)


@bp.route("/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
def edit(member_id):
    member = db.session.get(Member, member_id)
    if member is None:
        return render_template("errors/404.html"), 404
    form = MemberForm(obj=member) if request.method == "GET" else MemberForm()
    if form.validate_on_submit():
        body = clean_text(form.body_number.data, upper=True)
        if _body_taken(body, member):
            form.body_number.errors.append("This body number is already in the registry.")
        else:
            try:
                _apply_member(member, form)
            except ValueError as exc:
                form.photo.errors.append(str(exc))
            else:
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    form.body_number.errors.append("This body number is already in the registry.")
                else:
                    flash(f"{member.body_number} was updated.", "success")
                    return redirect(url_for("members.detail", member_id=member.id))
    return render_template(
        "members/form.html",
        form=form,
        member=member,
        associations=association_choices(),
    )


@bp.post("/<int:member_id>/delete")
@login_required
def delete(member_id):
    member = db.session.get(Member, member_id)
    if member is None:
        return render_template("errors/404.html"), 404
    label = member.body_number
    delete_photo_file(member.photo_filename)
    db.session.delete(member)
    db.session.commit()
    flash(f"{label} was removed from the registry.", "success")
    return redirect(url_for("members.index"))


@bp.get("/<int:member_id>/card")
@login_required
def card(member_id):
    member = db.session.get(Member, member_id)
    if member is None:
        return render_template("errors/404.html"), 404
    from app.cards import pdf_response

    return pdf_response([member])
