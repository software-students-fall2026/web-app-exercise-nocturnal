#!/usr/bin/env python3

"""single-person ski app."""

import os
import datetime
import re
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
)
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv, dotenv_values
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

load_dotenv(".env")  # load environment variables from .env file

DIFFICULTIES = (
    "novice",
    "easy",
    "intermediate",
    "advanced",
    "expert",
    "freeride",
    "extreme",
)


def create_app():
    """set up flask and mongodb."""

    app = Flask(__name__)

    # load flask configuration from env variables
    configuration = dotenv_values(".env")
    app.config.from_mapping(configuration)

    local_database = os.getenv("MONGO_LOCAL", "false").lower() == "true"
    connection = pymongo.MongoClient(
        os.environ["MONGO_LOCAL_URI"] if local_database else os.getenv("MONGO_URI")
    )
    database = connection[os.getenv("MONGO_DBNAME")]

    try:
        connection.admin.command("ping")
        print(" *", "Connected to MongoDB!")
    except Exception:
        print(" * MongoDB connection error. Check your local configuration.")

    def find_document(collection, document_id):
        """find a document or show a not-found page."""

        if not ObjectId.is_valid(document_id):
            abort(404)

        document = collection.find_one({"_id": ObjectId(document_id)})

        if not document:
            abort(404)

        return document

    """
    Validate and process submitted attempt data, including the date,
    completion status, difficulty rating, and personal notes.
    """
    def attempt_form(run_id):
        """Read the date, difficulty, notes, and completion status."""

        try:
            skied_at = datetime.datetime.fromisoformat(request.form["skied_at"])
        except (ValueError, KeyError):
            abort(400, "Enter a valid date and time.")

        difficulty = request.form.get("difficulty_rating") or None

        if difficulty is not None and difficulty not in DIFFICULTIES:
            abort(400, "Choose an OpenStreetMap difficulty category.")

        # Read and validate the completion status
        completed = request.form.get("completed")

        if completed not in ("yes", "no"):
            abort(400, "Please indicate whether you completed the run.")

        # based on https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
        photo = request.files.get("photo")
        photo_name = None
        if photo and photo.filename:
            photo_name = secure_filename(photo.filename)
            folder = os.path.join(app.static_folder, "uploads")
            os.makedirs(folder, exist_ok=True)
            photo.save(os.path.join(folder, photo_name))

        document = {
            "run_id": run_id,
            "skied_at": skied_at,
            "difficulty_rating": difficulty,
            "notes": request.form.get("notes", "").strip(),
            "completed": completed == "yes",
        }

        if photo_name:
            document["photo"] = photo_name

        return document

    def attach_community_ratings(runs):
        run_ids = [run["_id"] for run in runs]
        counts_by_run = {}

        if run_ids:
            ratings = database.community_ratings.find(
                {
                    "run_id": {"$in": run_ids},
                    "difficulty_rating": {"$in": DIFFICULTIES},
                },
                {"_id": 0, "run_id": 1, "difficulty_rating": 1},
            )

            for rating in ratings:
                run_id = rating["run_id"]
                difficulty = rating["difficulty_rating"]

                if run_id not in counts_by_run:
                    counts_by_run[run_id] = {}

                if difficulty not in counts_by_run[run_id]:
                    counts_by_run[run_id][difficulty] = 0

                counts_by_run[run_id][difficulty] += 1

        for run in runs:
            counts = counts_by_run.get(run["_id"], {})
            run["community_ratings"] = []
            run["report_count"] = 0

            for difficulty in DIFFICULTIES:
                count = counts.get(difficulty, 0)
                if count:
                    run["community_ratings"].append(
                        {"difficulty": difficulty, "count": count}
                    )
                    run["report_count"] += count

        return runs

    @app.route("/")
    def home():
        """Show the home page."""

        attempt_count = database.attempts.count_documents({})
        today_count = database.saved_runs.count_documents({"list": "today"})
        someday_count = database.saved_runs.count_documents({"list": "someday"})

        latest_attempt = database.attempts.find_one(sort=[("skiid_at", -1)])
        if latest_attempt:
            latest_run = database.runs.find_one({"_id": latest_attempt["run_id"]})
        else:
            latest_run = None

        return render_template(
            "index.html",
            attempt_count=attempt_count,
            today_count=today_count,
            someday_count=someday_count,
            latest_attempt=latest_attempt,
            latest_run=latest_run,
        )

    @app.route("/find")
    def find_runs():
        """Choose a state, resort, and run."""
        state = request.args.get("state", "")
        resort_id = request.args.get("resort_id", "")
        name = request.args.get("name", "").strip()

        states = sorted(
            database.resorts.distinct(
                "state", {"country": "US", "state": {"$ne": None}}
            )
        )
        resorts = (
            list(
                database.resorts.find({"country": "US", "state": state}).sort("name", 1)
            )
            if state
            else []
        )

        selected = None
        runs = []

        if resort_id:
            selected = find_document(database.resorts, resort_id)

            if selected.get("country") != "US":
                abort(404)

            if not state:
                state = selected["state"]
                resorts = list(
                    database.resorts.find({"country": "US", "state": state}).sort(
                        "name", 1
                    )
                )

            if selected["state"] != state:
                selected = None
            else:
                runs = list(
                    database.runs.find(
                        {
                            "resort_id": selected["_id"],
                            "name": {"$regex": re.escape(name), "$options": "i"},
                        }
                    ).sort("name", 1)
                )

        runs = attach_community_ratings(runs)

        return render_template(
            "find.html",
            states=states,
            state=state,
            resorts=resorts,
            selected=selected,
            runs=runs,
            name=name,
            difficulties=DIFFICULTIES,
        )

    @app.route("/run/<run_id>")
    def run_details(run_id):
        """show the run and its attempts."""

        document = find_document(database.runs, run_id)
        resort = database.resorts.find_one({"_id": document["resort_id"]})
        attempts = list(
            database.attempts.find({"run_id": document["_id"]}).sort("skied_at", -1)
        )

        return render_template(
            "run.html",
            document=document,
            resort=resort,
            attempts=attempts,
        )

    @app.route("/run/<run_id>/save", methods=["POST"])
    def save_run_post(run_id):
        """add the run to someday or today."""

        document = find_document(database.runs, run_id)
        destination = request.form["destination"]

        if destination not in ("someday", "today"):
            abort(400)

        criteria = {"run_id": document["_id"], "list": destination}
        database.saved_runs.update_one(
            criteria,
            {"$setOnInsert": {**criteria, "created_at": datetime.datetime.utcnow()}},
            upsert=True,
        )

        return redirect(url_for(destination))

    @app.route("/run/<run_id>/community-rating", methods=["POST"])
    def community_rating_post(run_id):
        run = find_document(database.runs, run_id)
        difficulty = request.form.get("difficulty_rating", "")
        next_url = request.form.get("next", "")

        if difficulty not in DIFFICULTIES:
            abort(400, "Choose a valid difficulty.")

        database.community_ratings.insert_one(
            {
                "run_id": run["_id"],
                "difficulty_rating": difficulty,
            }
        )

        # Only allow redirects back to this app.
        if not next_url.startswith("/") or next_url.startswith("//"):
            next_url = url_for("run_details", run_id=run_id)

        return redirect(next_url)

    def attach_run_details(documents):
        for document in documents:
            run = database.runs.find_one({"_id": document["run_id"]})
            document["run"] = run

            if run:
                document["resort"] = database.resorts.find_one(
                    {"_id": run["resort_id"]}
                )
                document["attempt_count"] = database.attempts.count_documents(
                    {"run_id": run["_id"]}
                )
                document["latest_attempt"] = list(
                    database.attempts.find({"run_id": run["_id"]})
                    .sort("skied_at", -1)
                    .limit(1)
                )

        return documents

    @app.route("/someday")
    def someday():
        """show someday runs."""

        name = request.args.get("name", "").strip().lower()
        difficulty = request.args.get("difficulty", "")
        state = request.args.get("state", "").strip()

        states = sorted(
            database.resorts.distinct(
                "state", {"country": "US", "state": {"$ne": None}}
            )
        )

        documents = attach_run_details(
            list(database.saved_runs.find({"list": "someday"}))
        )

        # Filter through Saved runs
        filtered = []
        for document in documents:
            run = document["run"]
            resort = document.get("resort")

            if name and (run is None or name not in run.get("name").lower()):
                continue
            if difficulty and (run is None or run.get("difficulty") != difficulty):
                continue
            if state and (resort is None or resort.get("state") != state):
                continue
            filtered.append(document)
        return render_template(
            "saved_runs.html",
            documents=filtered,
            title="Someday",
            name=name,
            difficulty=difficulty,
            state=state,
            states=states,
            difficulties=DIFFICULTIES,
        )

    @app.route("/today")
    def today():
        """show today runs."""

        documents = attach_run_details(
            list(database.saved_runs.find({"list": "today"}))
        )

        return render_template("saved_runs.html", documents=documents, title="Today")

    @app.route("/saved/<saved_id>/delete")
    def confirm_delete_saved(saved_id):
        """confirm before removing a run from one list"""

        document = find_document(database.saved_runs, saved_id)
        document["run"] = database.runs.find_one({"_id": document["run_id"]})

        return render_template("confirm_delete.html", document=document)

    @app.route("/saved/<saved_id>/delete", methods=["POST"])
    def delete_saved_post(saved_id):
        """remove a run from one list."""

        document = find_document(database.saved_runs, saved_id)
        database.saved_runs.delete_one({"_id": document["_id"]})

        return redirect(url_for("today" if document["list"] == "today" else "someday"))

    @app.route("/run/<run_id>/log")
    def log_attempt(run_id):
        """show the attempt form."""

        run = find_document(database.runs, run_id)

        document = {
            "skied_at": datetime.datetime.utcnow(),
            "notes": "",
            "difficulty_rating": None,
        }

        return render_template(
            "attempt.html", document=document, run=run, difficulties=DIFFICULTIES
        )

    @app.route("/run/<run_id>/log", methods=["POST"])
    def log_attempt_post(run_id):
        """
        Handle the submission of a new skiing attempt and save
        the attempt information to MongoDB.
        """

        run = find_document(database.runs, run_id)
        document = attempt_form(run["_id"])
        attempt_id = database.attempts.insert_one(document).inserted_id

        return redirect(url_for("attempt", attempt_id=attempt_id))

    @app.route("/history")
    def history():
        """
        Retrieve previously logged skiing attempts from MongoDB,
        apply optional resort and date filters, and display
        the results in reversed chronological order.
        """

        # Read filter values from the URL
        resort_id = request.args.get("resort_id", "").strip()
        selected_date = request.args.get("date", "").strip()

        # Init with no filters
        query = {}

        # Filter by resort
        if resort_id:
            if not ObjectId.is_valid(resort_id):
                abort(400, "Invalid resort.")

            runs = database.runs.find({"resort_id": ObjectId(resort_id)}, {"_id": 1})

            run_ids = [run["_id"] for run in runs]
            query["run_id"] = {"$in": run_ids}

        # Filter by date
        if selected_date:
            try:
                date = datetime.date.fromisoformat(selected_date)
            except ValueError:
                abort(400, "Invalid date.")

            start = datetime.datetime.combine(date, datetime.time.min)
            end = start + datetime.timedelta(days=1)

            query["skied_at"] = {"$gte": start, "$lt": end}

        # Retrieve matching attempts, newest first
        documents = list(database.attempts.find(query).sort("skied_at", -1))

        for document in documents:
            document["run"] = database.runs.find_one({"_id": document["run_id"]})

        # Retrieve resorts for the dropdown
        resorts = list(database.resorts.find().sort("name", 1))

        return render_template(
            "history.html",
            documents=documents,
            resorts=resorts,
            selected_resort_id=resort_id,
            selected_date=selected_date,
        )

    @app.route("/attempt/<attempt_id>")
    def attempt(attempt_id):
        """show an attempt."""

        document = find_document(database.attempts, attempt_id)
        run = find_document(database.runs, str(document["run_id"]))

        # photos saved on the computer that uploads them
        photo = document.get("photo")
        if photo and not os.path.exists(os.path.join(app.static_folder, "uploads", photo)):
            document["photo"] = None

        return render_template("reflection.html", document=document, run=run)

    @app.route("/attempt/<attempt_id>/edit")
    def edit_attempt(attempt_id):
        """show an attempt for editing."""

        document = find_document(database.attempts, attempt_id)
        run = find_document(database.runs, str(document["run_id"]))

        return render_template(
            "attempt.html", document=document, run=run, difficulties=DIFFICULTIES
        )

    @app.route("/attempt/<attempt_id>", methods=["POST"])
    def attempt_post(attempt_id):
        """save changes to an attempt."""

        document = find_document(database.attempts, attempt_id)
        update = attempt_form(document["run_id"])
        database.attempts.update_one({"_id": document["_id"]}, {"$set": update})

        return redirect(url_for("attempt", attempt_id=attempt_id))

    @app.route("/attempt/<attempt_id>/delete", methods=["POST"])
    def delete_attempt_post(attempt_id):
        """
        Delete a selected skiing attempt from MongoDB.
        """

        document = find_document(database.attempts, attempt_id)
        database.attempts.delete_one({"_id": document["_id"]})

        return redirect(url_for("history"))

    @app.errorhandler(Exception)
    def handle_error(error):
        """show an error without exposing private details."""

        if isinstance(error, HTTPException):
            return render_template("error.html", message=error.description), error.code

        return (
            render_template(
                "error.html",
                message="Database unavailable. Try again.",
            ),
            503,
        )

    return app


app = create_app()

if __name__ == "__main__":
    FLASK_PORT = os.getenv("FLASK_PORT", "5000")
    FLASK_ENV = os.getenv("FLASK_ENV")
    print(f"FLASK_ENV: {FLASK_ENV}, FLASK_PORT: {FLASK_PORT}")

    app.run(port=FLASK_PORT)
