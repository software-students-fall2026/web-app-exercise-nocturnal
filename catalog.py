"""country, resort, and run pages."""

# citations — heavily used for reference:
# https://www.mongodb.com/docs/languages/python/pymongo-driver/current/

import re
from bson.objectid import ObjectId
from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user


def register_catalog_routes(app, db):
    """add the catalog routes."""

    @app.template_filter("difficulty_label")
    def difficulty_label(value):
        """show the difficulty name."""
        return ("Beginner", "Easy", "Intermediate", "Advanced", "Expert")[value - 1]

    @app.route("/countries")
    def show_countries():
        """show the countries."""
        if request.args.get("country"):
            # just running black makes it look like this.
            # was all one line originally.
            return redirect(
                url_for("show_country_resorts", country_code=request.args["country"])
            )

        # 1) get the countries from the resorts
        # just running black makes it look like this.
        # was all one line originally.
        docs = list(
            db.resorts.aggregate(
                [
                    {
                        "$group": {
                            "_id": "$country_code",
                            "name": {"$first": "$country_name"},
                        }
                    },
                    {"$sort": {"name": 1}},
                ]
            )
        )
        return render_template("countries.html", docs=docs)

    @app.route("/countries/<country_code>/resorts")
    def show_country_resorts(country_code):
        """show the country's resorts."""
        # 1) find the selected country
        country = db.resorts.find_one({"country_code": country_code})
        if country is None:
            abort(404)
        if request.args.get("resort_id"):
            # just running black makes it look like this.
            # was all one line originally.
            selected = db.resorts.find_one(
                {
                    "_id": ObjectId(request.args["resort_id"]),
                    "country_code": country_code,
                }
            )
            if selected is None:
                abort(404)
            return redirect(url_for("show_resort_runs", resort_id=selected["_id"]))
        docs = list(db.resorts.find({"country_code": country_code}).sort("name", 1))
        return render_template("resorts.html", docs=docs, country=country)

    @app.route("/resorts/<resort_id>/runs")
    def show_resort_runs(resort_id):
        """show the resort's runs."""
        # 1) find the resort and get the search text
        resort = db.resorts.find_one({"_id": ObjectId(resort_id)})
        if resort is None:
            abort(404)
        search = request.args.get("search", "").strip()[:100]
        # 2) sort matching runs by name
        query = {"resort_id": resort["_id"]}
        if search:
            query["name"] = {"$regex": re.escape(search), "$options": "i"}
        docs = list(db.runs.find(query).sort([("name", 1), ("_id", 1)]))
        return render_template("runs.html", docs=docs, resort=resort, search=search)

    @app.route("/runs/<run_id>")
    def show_run_details(run_id):
        """show the run details."""
        # 1) find the run and its resort
        doc = db.runs.find_one({"_id": ObjectId(run_id)})
        if doc is None:
            abort(404)
        resort = db.resorts.find_one({"_id": doc["resort_id"]})

        # 2) show this user's saves
        # just running black makes it look like this.
        # was all one line originally.
        saved = db.saved_runs.distinct(
            "list", {"user_id": current_user.record_id, "run_id": doc["_id"]}
        )
        # 3) calculate the average difficulty
        # just running black makes it look like this.
        # was all one line originally.
        summary = list(
            db.ratings.aggregate(
                [
                    {"$match": {"run_id": doc["_id"]}},
                    {"$group": {"_id": None, "average": {"$avg": "$difficulty"}}},
                ]
            )
        )
        community = summary[0] if summary else None
        # just running black makes it look like this.
        # was all one line originally.
        return render_template(
            "run.html", doc=doc, resort=resort, saved=saved, community=community
        )

    @app.route("/community")
    def show_community_ratings():
        """show runs with community ratings."""
        # 1) find runs with ratings
        run_ids = db.ratings.distinct("run_id")
        # just running black makes it look like this.
        # was all one line originally.
        docs = list(
            db.runs.find({"_id": {"$in": run_ids}}).sort([("name", 1), ("_id", 1)])
        )
        # 2) get their resorts
        # just running black makes it look like this.
        # was all one line originally.
        resorts = {
            doc["_id"]: doc
            for doc in db.resorts.find(
                {"_id": {"$in": [doc["resort_id"] for doc in docs]}}
            )
        }
        return render_template("community.html", docs=docs, resorts=resorts)
