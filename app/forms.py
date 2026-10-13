from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(max=32)],
        render_kw={"autocomplete": "username", "autofocus": True},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "current-password"},
    )
    remember = BooleanField("Keep me signed in on this desk")


class AccountForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    current_password = PasswordField(
        "Current password",
        validators=[DataRequired()],
        render_kw={"autocomplete": "current-password"},
    )
    new_password = PasswordField(
        "New password",
        validators=[Optional(), Length(min=10, max=128)],
        render_kw={"autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[Optional(), Length(max=128)],
        render_kw={"autocomplete": "new-password"},
    )

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators)
        if self.new_password.data or self.confirm_password.data:
            if (self.new_password.data or "") != (self.confirm_password.data or ""):
                self.confirm_password.errors.append("The new passwords do not match.")
                ok = False
        return ok


class UserCreateForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=32),
            Regexp(r"^[A-Za-z0-9._-]+$", message="Use letters, numbers, dots, hyphens, or underscores."),
        ],
    )
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    role = SelectField(
        "Role",
        choices=[("staff", "Staff"), ("admin", "Administrator")],
        validators=[DataRequired()],
    )
    password = PasswordField(
        "Temporary password",
        validators=[DataRequired(), Length(min=10, max=128)],
        render_kw={"autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirm temporary password",
        validators=[DataRequired(), Length(max=128)],
        render_kw={"autocomplete": "new-password"},
    )

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators)
        if (self.password.data or "") != (self.confirm_password.data or ""):
            self.confirm_password.errors.append("The passwords do not match.")
            ok = False
        return ok


class UserEditForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    role = SelectField(
        "Role",
        choices=[("staff", "Staff"), ("admin", "Administrator")],
        validators=[DataRequired()],
    )
    is_active = BooleanField("Active account")
    password = PasswordField(
        "Reset password",
        validators=[Optional(), Length(min=10, max=128)],
        render_kw={"autocomplete": "new-password"},
    )
    confirm_password = PasswordField(
        "Confirm reset password",
        validators=[Optional(), Length(max=128)],
        render_kw={"autocomplete": "new-password"},
    )

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators)
        if self.password.data or self.confirm_password.data:
            if (self.password.data or "") != (self.confirm_password.data or ""):
                self.confirm_password.errors.append("The passwords do not match.")
                ok = False
        return ok


class MemberForm(FlaskForm):
    body_number = StringField(
        "Body number",
        validators=[
            DataRequired(),
            Length(max=20),
            Regexp(r"^[A-Za-z0-9-]+$", message="Use letters, numbers, and hyphens only."),
        ],
        render_kw={"placeholder": "J-001"},
    )
    owner_name = StringField(
        "Owner",
        validators=[DataRequired(), Length(max=160)],
        render_kw={"placeholder": "Surname, given name"},
    )
    address = StringField(
        "Address",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Barangay, Jagna"},
    )
    association = StringField(
        "Association",
        validators=[Length(max=40)],
        render_kw={"placeholder": "JAMODA", "list": "associations"},
    )
    franchise_number = StringField(
        "Franchise number",
        validators=[DataRequired(), Length(max=40)],
        render_kw={"placeholder": "JBF-00-0000-00-M"},
    )
    driver_name = StringField(
        "Driver",
        validators=[DataRequired(), Length(max=160)],
        render_kw={"placeholder": "OWNER if the owner drives the unit"},
    )
    status = SelectField(
        "Status",
        choices=[("Active", "Active"), ("Suspended", "Suspended"), ("Expired", "Expired")],
        validators=[DataRequired()],
        default="Active",
    )
    contact_number = StringField("Contact number", validators=[Optional(), Length(max=40)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
    photo = FileField(
        "Photograph",
        validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Upload a JPG, PNG, or WebP image.")],
        render_kw={"accept": "image/jpeg,image/png,image/webp"},
    )
    remove_photo = BooleanField("Remove the current photograph")
