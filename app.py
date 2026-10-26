"""set up stoked."""

# citations — heavily used for reference:
# https://github.com/nyu-software-engineering/flask-pymongo-web-app-example

import os
from pathlib import Path
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import Flask, render_template
from pymongo import MongoClient
from werkzeug.exceptions import HTTPException
from accounts import register_account_routes
from catalog import register_catalog_routes
from activity import register_activity_routes


def create_app():
    """set up flask and mongodb."""
    # 1) load the settings
    load_dotenv(Path(__file__).parent / ".env")
    app = Flask(__name__)
    app.secret_key = os.environ["SECRET_KEY"]
    if len(app.secret_key) < 32:
        raise ValueError("give SECRET_KEY at least 32 random characters")

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "false") == "true",
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    )

    # 2) connect to mongodb
    client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=3000)
    db = client[os.environ["MONGO_DBNAME"]]
    # prevent duplicates and index the fields we search
    db.users.create_index("email", unique=True)
    # just running black makes it look like this.
    # was all one line originally.
    db.saved_runs.create_index(
        [("user_id", 1), ("run_id", 1), ("list", 1)], unique=True
    )
    db.ratings.create_index([("user_id", 1), ("run_id", 1)], unique=True)
    db.resorts.create_index([("country_code", 1), ("name", 1)])
    db.runs.create_index([("resort_id", 1), ("name", 1)])
    db.attempts.create_index([("user_id", 1), ("skied_at", -1)])

    # 3) add the routes
    register_account_routes(app, db)
    register_catalog_routes(app, db)
    register_activity_routes(app, db)

    # 4) show errors on the error page
    @app.errorhandler(Exception)
    def show_error_page(error):
        """show the error page."""
        code = error.code if isinstance(error, HTTPException) else 500
        if isinstance(error, InvalidId):
            code = 400
        message = "file is too large." if code == 413 else str(error).lower()
        return render_template("error.html", message=message), code

    return app


app = create_app()
