"""saved runs, attempts, and ratings."""

# citations — heavily used for reference:
# https://github.com/nyu-software-engineering/flask-pymongo-web-app-example
# https://flask.palletsprojects.com/en/stable/patterns/fileuploads/


import datetime
from pathlib import Path
from bson.objectid import ObjectId
# just running black makes it look like this.
# was all one line originally.
from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user
from werkzeug.utils import secure_filename


def register_activity_routes(app, db):
    """add the activity routes."""
    uploads = Path(app.static_folder) / "uploads"

    # get the user id from the session
    @app.route("/")
    def show_home():
        """show the homepage counts."""
        user_id = current_user.record_id
        # just running black makes it look like this.
        # was all one line originally.
        today_count = db.saved_runs.count_documents(
            {"user_id": user_id, "list": "today"}
        )
        # just running black makes it look like this.
        # was all one line originally.
        someday_count = db.saved_runs.count_documents(
            {"user_id": user_id, "list": "someday"}
        )
        attempt_count = db.attempts.count_documents({"user_id": user_id})
        # just running black makes it look like this.
        # was all one line originally.
        return render_template(
            "index.html",
            today_count=today_count,
            someday_count=someday_count,
            attempt_count=attempt_count,
        )

    @app.route("/today")
    @app.route("/someday")
    def show_saved_runs():
        """show today or someday."""
        destination = request.path[1:]
        # 1) get this user's saved runs
        # just running black makes it look like this.
        # was all one line originally.
        saved = {
            doc["run_id"]: doc
            for doc in db.saved_runs.find(
                {"user_id": current_user.record_id, "list": destination}
            )
        }
        docs = list(db.runs.find({"_id": {"$in": list(saved)}}).sort("name", 1))

        # 2) get the resorts and attempts
        # just running black makes it look like this.
        # was all one line originally.
        resorts = {
            doc["_id"]: doc
            for doc in db.resorts.find(
                {"_id": {"$in": [doc["resort_id"] for doc in docs]}}
            )
        }
        attempts = {}
        # just running black makes it look like this.
        # was all one line originally.
        for attempt in db.attempts.find(
            {
                "user_id": current_user.record_id,
                "run_id": {"$in": [doc["_id"] for doc in docs]},
            }
        ).sort("skied_at", -1):
            # just running black makes it look like this.
            # was all one line originally.
            summary = attempts.setdefault(
                attempt["run_id"], {"count": 0, "latest": attempt["skied_at"]}
            )
            summary["count"] += 1
        # just running black makes it look like this.
        # was all one line originally.
        return render_template(
            "saved_runs.html",
            docs=docs,
            destination=destination,
            saved=saved,
            resorts=resorts,
            attempts=attempts,
        )

    @app.route("/runs/<run_id>/save", methods=["POST"])
    def save_run_to_list(run_id):
        """add a run to today or someday."""
        # 1) check the run and list
        doc = db.runs.find_one({"_id": ObjectId(run_id)})
        if doc is None:
            abort(404)
        destination = request.form["destination"]
        if destination not in ("today", "someday"):
            abort(400)

        # 2) do not save the same run twice
        # just running black makes it look like this.
        # was all one line originally.
        saved_run = {
            "user_id": current_user.record_id,
            "run_id": doc["_id"],
            "list": destination,
        }
        # just running black makes it look like this.
        # was all one line originally.
        db.saved_runs.update_one(
            saved_run,
            {"$setOnInsert": {**saved_run, "created_at": datetime.datetime.now()}},
            upsert=True,
        )
        flash("saved to " + destination + ".")
        return redirect("/" + destination)

    @app.route("/runs/<run_id>/remove/<destination>")
    def confirm_saved_run_removal(run_id, destination):
        """confirm removal from the list."""
        if destination not in ("today", "someday"):
            abort(400)
        # just running black makes it look like this.
        # was all one line originally.
        doc = db.saved_runs.find_one(
            {
                "user_id": current_user.record_id,
                "run_id": ObjectId(run_id),
                "list": destination,
            }
        )
        if doc is None:
            abort(404)
        run = db.runs.find_one({"_id": doc["run_id"]})
        return render_template(
            "confirm.html",
            title="Remove run?",
            message="Remove " + run["name"] + " from " + destination + "?",
            action=url_for("remove_saved_run", run_id=run_id, destination=destination),
            cancel="/" + destination,
            button="Remove",
        )

    @app.route("/runs/<run_id>/remove/<destination>", methods=["POST"])
    def remove_saved_run(run_id, destination):
        """remove the saved run."""
        if destination not in ("today", "someday"):
            abort(400)
        # just running black makes it look like this.
        # was all one line originally.
        db.saved_runs.delete_one(
            {
                "user_id": current_user.record_id,
                "run_id": ObjectId(run_id),
                "list": destination,
            }
        )
        flash("run removed.")
        return redirect("/" + destination)

    def update_community_rating(run_id, difficulty):
        """update the difficulty rating if one was given."""
        if difficulty is not None:
            # just running black makes it look like this.
            # was all one line originally.
            db.ratings.update_one(
                {"user_id": current_user.record_id, "run_id": run_id},
                {"$set": {"difficulty": difficulty}},
                upsert=True,
            )

    def read_attempt_form():
        """
        Validate and process submitted attempt data, including the date,
        completion status, difficulty rating, and personal notes.
        """
        # 1) check the form fields
        try:
            skied_at = datetime.datetime.strptime(request.form["skied_at"], "%Y-%m-%d")
        except ValueError:
            abort(400)
        completed = request.form["completed"]
        notes = request.form["notes"].strip()
        if completed not in ("yes", "no") or len(notes) > 2000:
            abort(400)
        difficulty = request.form.get("difficulty", "")
        if difficulty and difficulty not in ("1", "2", "3", "4", "5"):
            abort(400)
        # just running black makes it look like this.
        # was all one line originally.
        return {
            "skied_at": skied_at,
            "completed": completed == "yes",
            "notes": notes,
            "difficulty": int(difficulty) if difficulty else None,
        }

    def save_attempt_photo(document):
        """save the photo with a unique filename."""
        photo = request.files.get("photo")
        if photo and photo.filename:
            extension = Path(secure_filename(photo.filename)).suffix.lower()
            if extension not in (".jpg", ".jpeg", ".png"):
                abort(400, "use a jpg or png.")
            photo_name = str(ObjectId()) + extension
            uploads.mkdir(parents=True, exist_ok=True)
            photo.save(uploads / photo_name)
            document["photo"] = photo_name

    @app.route("/runs/<run_id>/attempts/new")
    def show_new_attempt_form(run_id):
        """show the attempt form."""
        run = db.runs.find_one({"_id": ObjectId(run_id)})
        if run is None:
            abort(404)
        doc = {"skied_at": datetime.datetime.now(), "notes": "", "completed": True}
        # just running black makes it look like this.
        # was all one line originally.
        return render_template(
            "attempt.html",
            doc=doc,
            run=run,
            action=url_for("create_attempt", run_id=run_id),
        )

    @app.route("/runs/<run_id>/attempts/new", methods=["POST"])
    def create_attempt(run_id):
        """save the attempt and clear both lists."""
        run = db.runs.find_one({"_id": ObjectId(run_id)})
        if run is None:
            abort(404)
        doc = read_attempt_form()
        doc["run_id"] = run["_id"]
        doc["user_id"] = current_user.record_id
        save_attempt_photo(doc)
        attempt_id = db.attempts.insert_one(doc).inserted_id
        update_community_rating(run["_id"], doc["difficulty"])
        # just running black makes it look like this.
        # was all one line originally.
        db.saved_runs.delete_many(
            {"user_id": current_user.record_id, "run_id": run["_id"]}
        )
        flash("attempt saved.")
        return redirect(url_for("show_attempt_details", attempt_id=attempt_id))

    @app.route("/history")
    def show_attempt_history():
        """show the attempt history."""
        # 1) get this user's attempts, newest first
        # just running black makes it look like this.
        # was all one line originally.
        docs = list(
            db.attempts.find({"user_id": current_user.record_id}).sort(
                [("skied_at", -1), ("_id", -1)]
            )
        )
        # 2) get the runs for these attempts
        # just running black makes it look like this.
        # was all one line originally.
        runs = {
            doc["_id"]: doc
            for doc in db.runs.find(
                {"_id": {"$in": [attempt["run_id"] for attempt in docs]}}
            )
        }
        return render_template("history.html", docs=docs, runs=runs)

    @app.route("/attempts/<attempt_id>")
    def show_attempt_details(attempt_id):
        """show the attempt."""
        # just running black makes it look like this.
        # was all one line originally.
        doc = db.attempts.find_one(
            {"_id": ObjectId(attempt_id), "user_id": current_user.record_id}
        )
        if doc is None:
            abort(404)
        run = db.runs.find_one({"_id": doc["run_id"]})
        # hide the photo if its file is missing
        if doc.get("photo") and not (uploads / doc["photo"]).is_file():
            doc["photo"] = None
        return render_template("reflection.html", doc=doc, run=run)

    @app.route("/static/uploads/<filename>")
    def show_attempt_photo(filename):
        """show the photo to its owner."""
        # just running black makes it look like this.
        # was all one line originally.
        doc = db.attempts.find_one(
            {"photo": filename, "user_id": current_user.record_id}
        )
        if doc is None:
            abort(404)
        response = send_from_directory(uploads, doc["photo"])
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.route("/attempts/<attempt_id>/edit")
    def show_edit_attempt_form(attempt_id):
        """show the edit form."""
        # just running black makes it look like this.
        # was all one line originally.
        doc = db.attempts.find_one(
            {"_id": ObjectId(attempt_id), "user_id": current_user.record_id}
        )
        if doc is None:
            abort(404)
        run = db.runs.find_one({"_id": doc["run_id"]})
        # just running black makes it look like this.
        # was all one line originally.
        return render_template(
            "attempt.html",
            doc=doc,
            run=run,
            action=url_for("update_attempt", attempt_id=attempt_id),
        )

    @app.route("/attempts/<attempt_id>/edit", methods=["POST"])
    def update_attempt(attempt_id):
        """save the edited attempt."""
        # just running black makes it look like this.
        # was all one line originally.
        attempt = db.attempts.find_one(
            {"_id": ObjectId(attempt_id), "user_id": current_user.record_id}
        )
        if attempt is None:
            abort(404)
        doc = read_attempt_form()
        save_attempt_photo(doc)
        # just running black makes it look like this.
        # was all one line originally.
        result = db.attempts.update_one(
            {"_id": ObjectId(attempt_id), "user_id": current_user.record_id},
            {"$set": doc},
        )
        if result.matched_count == 0:
            abort(404)
        # no new upload leaves the previous photo in place
        if doc.get("photo") and attempt.get("photo"):
            (uploads / attempt["photo"]).unlink(missing_ok=True)
        update_community_rating(attempt["run_id"], doc["difficulty"])
        flash("attempt updated.")
        return redirect(url_for("show_attempt_details", attempt_id=attempt_id))

    @app.route("/attempts/<attempt_id>/delete")
    def confirm_attempt_deletion(attempt_id):
        """confirm deleting the attempt."""
        # just running black makes it look like this.
        # was all one line originally.
        doc = db.attempts.find_one(
            {"_id": ObjectId(attempt_id), "user_id": current_user.record_id}
        )
        if doc is None:
            abort(404)
        return render_template(
            "confirm.html",
            title="Delete attempt?",
            message="Delete this attempt from your history?",
            action=url_for("delete_attempt", attempt_id=attempt_id),
            cancel=url_for("show_attempt_details", attempt_id=attempt_id),
            button="Delete",
        )

    @app.route("/attempts/<attempt_id>/delete", methods=["POST"])
    def delete_attempt(attempt_id):
        """delete the attempt and its photo."""
        # just running black makes it look like this.
        # was all one line originally.
        doc = db.attempts.find_one_and_delete(
            {"_id": ObjectId(attempt_id), "user_id": current_user.record_id}
        )
        if doc is None:
            abort(404)
        if doc.get("photo"):
            (uploads / doc["photo"]).unlink(missing_ok=True)
        flash("attempt deleted.")
        return redirect(url_for("show_attempt_history"))
