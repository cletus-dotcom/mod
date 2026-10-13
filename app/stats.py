from sqlalchemy import func

from app import db
from app.models import Member


def summary():
    total = Member.query.count()
    owner_drivers = Member.query.filter_by(driver_is_owner=True).count()
    association_count = (
        db.session.query(func.count(func.distinct(Member.association)))
        .filter(Member.association.isnot(None), Member.association != "")
        .scalar()
        or 0
    )
    barangay = func.split_part(Member.address, ",", 1)
    barangay_count = db.session.query(func.count(func.distinct(barangay))).scalar() or 0
    association_rows = (
        db.session.query(Member.association, func.count())
        .group_by(Member.association)
        .order_by(func.count().desc(), Member.association.asc())
        .all()
    )
    barangay_rows = (
        db.session.query(barangay, func.count())
        .group_by(barangay)
        .order_by(func.count().desc(), barangay.asc())
        .limit(8)
        .all()
    )
    unspecified = sum(count for name, count in association_rows if not name)

    def pack(rows):
        packed = []
        for name, count in rows:
            packed.append(
                {
                    "name": name or "Unspecified",
                    "count": count,
                    "pct": round(count * 100 / total) if total else 0,
                }
            )
        return packed

    return {
        "total": total,
        "owner_drivers": owner_drivers,
        "assigned_drivers": total - owner_drivers,
        "owner_pct": round(owner_drivers * 100 / total) if total else 0,
        "association_count": association_count,
        "barangay_count": barangay_count,
        "by_association": pack(association_rows),
        "by_barangay": pack(barangay_rows),
        "unspecified": unspecified,
    }


def dashboard_stats():
    figures = summary()
    figures["recent"] = Member.query.order_by(Member.updated_at.desc(), Member.id.desc()).limit(6).all()
    return figures
