"""login, signup, and profiles."""

# citations — heavily used for reference:
# https://flask-login.readthedocs.io/
# https://flask.palletsprojects.com/en/stable/tutorial/views/
# https://flask-wtf.readthedocs.io/en/1.2.x/csrf/

import re
from bson.objectid import ObjectId
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin):
    """store the signed-in user."""

    def __init__(self, doc):
        """load the account fields."""
        self.id = str(doc["_id"])
        self.record_id = doc["_id"]
        self.email = doc["email"]
        self.display_name = doc["display_name"]


def register_account_routes(app, db):
    """add the account routes."""
    manager = LoginManager(app)
    manager.login_view = "show_login_form"
    manager.login_message = None

    CSRFProtect(app)

    @manager.user_loader
    def load_account_from_session(user_id):
        """find the signed-in user."""
        if not ObjectId.is_valid(user_id):
            return None
        doc = db.users.find_one({"_id": ObjectId(user_id)})
        return User(doc) if doc else None

    @app.before_request
    def require_login():
        """require login for private pages."""
        # just running black makes it look like this.
        # was all one line originally.
        if request.endpoint and request.endpoint not in {
            "static",
            "show_login_form",
            "authenticate_account",
            "show_signup_form",
            "create_account",
        }:
            if not current_user.is_authenticated:
                return redirect(url_for("show_login_form"))

    @app.after_request
    def disable_private_page_caching(response):
        """do not cache private pages."""
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.route("/login")
    def show_login_form():
        """display the login form."""
        return render_template("login.html")

    @app.route("/login", methods=["POST"])
    def authenticate_account():
        """check the password and log in."""
        # 1) find the account and check the password
        email = request.form["email"].strip().casefold()
        password = request.form["password"]
        doc = db.users.find_one({"email": email})
        # just running black makes it look like this.
        # was all one line originally.
        if (
            doc is None
            or len(password) > 128
            or not check_password_hash(doc["password_hash"], password)
        ):
            # just running black makes it look like this.
            # was all one line originally.
            return (
                render_template("login.html", error="email or password is incorrect."),
                401,
            )

        # 2) clear the old session
        session.clear()
        login_user(User(doc))
        return redirect(url_for("show_home"))

    @app.route("/signup")
    def show_signup_form():
        """display the signup form."""
        return render_template("signup.html")

    @app.route("/signup", methods=["POST"])
    def create_account():
        """check the signup fields and create the account."""
        # 1) check the signup fields; format and length limits are app rules
        email = request.form["email"].strip().casefold()
        password = request.form["password"]
        display_name = request.form["display_name"].strip()
        error = None
        if len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            error = "check email address."
        elif len(password) < 12:
            error = "password is too short."
        elif len(password) > 128:
            error = "password is too long."
        elif not display_name:
            error = "enter your display name."
        elif len(display_name) > 80:
            error = "display name is too long."
        if error:
            return render_template("signup.html", error=error), 400

        # 2) reject duplicate emails
        # just running black makes it look like this.
        # was all one line originally.
        doc = {
            "email": email,
            "password_hash": generate_password_hash(
                password, method="pbkdf2:sha256:1000000"
            ),
            "display_name": display_name,
        }
        try:
            db.users.insert_one(doc)
        except DuplicateKeyError:
            # just running black makes it look like this.
            # was all one line originally.
            return (
                render_template("signup.html", error="email already present."),
                400,
            )

        # 3) log in to the new account
        session.clear()
        login_user(User(doc))
        flash("account created.")
        return redirect(url_for("show_home"))

    @app.route("/profile")
    def show_profile():
        """show the profile."""
        return render_template("profile.html")

    @app.route("/profile", methods=["POST"])
    def update_display_name():
        """save the display name."""
        # 1) check the name
        display_name = request.form["display_name"].strip()
        if not display_name:
            # just running black makes it look like this.
            # was all one line originally.
            return (
                render_template("profile.html", error="enter your display name."),
                400,
            )
        if len(display_name) > 80:
            # just running black makes it look like this.
            # was all one line originally.
            return (
                render_template("profile.html", error="display name is too long."),
                400,
            )

        # 2) take the account id from the session, never from the form
        # just running black makes it look like this.
        # was all one line originally.
        db.users.update_one(
            {"_id": current_user.record_id}, {"$set": {"display_name": display_name}}
        )
        flash("profile saved.")
        return redirect(url_for("show_profile"))

    @app.route("/logout", methods=["POST"])
    def log_out_account():
        """log out."""
        logout_user()
        session.clear()
        return redirect(url_for("show_login_form"))
