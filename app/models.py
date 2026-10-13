from datetime import datetime, timezone

from flask_login import UserMixin

from app import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime(timezone=True))

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def role_label(self):
        return "Administrator" if self.role == "admin" else "Staff"


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    body_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    owner_name = db.Column(db.String(160), nullable=False, index=True)
    address = db.Column(db.String(200), nullable=False)
    association = db.Column(db.String(40), index=True)
    franchise_number = db.Column(db.String(40), nullable=False, index=True)
    driver_name = db.Column(db.String(160), nullable=False, index=True)
    driver_is_owner = db.Column(db.Boolean, nullable=False, default=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Active", index=True)
    contact_number = db.Column(db.String(40))
    notes = db.Column(db.Text)
    photo_filename = db.Column(db.String(80))
    record_year = db.Column(db.Integer, nullable=False, default=2026)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow, index=True
    )
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    updated_by = db.relationship("User")

    @property
    def driver_display(self):
        if self.driver_is_owner and (self.driver_name or "").strip().upper() == "OWNER":
            return self.owner_name
        return self.driver_name

    @property
    def driver_role(self):
        return "Owner-driver" if self.driver_is_owner else "Assigned driver"

    @property
    def barangay(self):
        return (self.address or "").split(",")[0].strip()
