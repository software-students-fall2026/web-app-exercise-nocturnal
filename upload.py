#!/usr/bin/env python3

"""
upload united states resorts and downhill runs from openskidata.
run from the repo: python upload.py ski_areas.geojson runs.geojson
"""

import os
import sys
import json
import pymongo
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env file

# grabbed this from https://docs.python.org/3/library/json.html
# data from https://www.openskidata.org/
with open(sys.argv[1], encoding="utf-8") as file:
    ski_areas = json.load(file)["features"]

with open(sys.argv[2], encoding="utf-8") as file:
    runs = json.load(file)["features"]

# connect to mongodb
connection = pymongo.MongoClient(os.getenv("MONGO_URI"))
database = connection[os.getenv("MONGO_DBNAME")]

database.resorts.create_index("source_ids")
database.runs.create_index([("source_ids", 1), ("resort_id", 1)])
database.resorts.create_index([("country", 1), ("state", 1), ("name", 1)])
database.runs.create_index("resort_id")

resorts = {}

# save united states downhill resorts
for feature in ski_areas:
    properties = feature["properties"]

    if not properties["name"] or "downhill" not in properties["activities"]:
        continue

    state = None
    for place in properties["places"]:
        if place["iso3166_1Alpha2"] == "US":
            state = place["localized"]["en"]["region"]
            break

    if not state or not properties["sources"]:
        continue

    source_ids = []
    for source in properties["sources"]:
        source_ids.append(source["type"] + ":" + str(source["id"]))

    criteria = {"source_ids": {"$in": source_ids}}
    document = {
        "source_ids": source_ids,
        "name": properties["name"],
        "country": "US",
        "state": state,
    }

    database.resorts.update_one(criteria, {"$set": document}, upsert=True)
    resorts[properties["id"]] = database.resorts.find_one(criteria)["_id"]

# save named downhill runs belonging to those resorts
for feature in runs:
    properties = feature["properties"]

    if not properties["name"] or "downhill" not in properties["uses"]:
        continue

    if not properties["sources"]:
        continue

    source_ids = []
    for source in properties["sources"]:
        source_ids.append(source["type"] + ":" + str(source["id"]))

    geometry = feature.get("geometry")
    if geometry and geometry["type"] == "LineString":
        geometry = {
            "type": "LineString",
            "coordinates": [point[:2] for point in geometry["coordinates"]],
        }
    else:
        geometry = None

    for area in properties["skiAreas"]:
        resort_id = resorts.get(area["properties"]["id"])
        if resort_id is None:
            continue

        criteria = {"source_ids": {"$in": source_ids}, "resort_id": resort_id}
        document = {
            "source_ids": source_ids,
            "resort_id": resort_id,
            "name": properties["name"],
            "geometry": geometry,
        }

        for field in (
            "ref",
            "description",
            "difficulty",
            "difficultyConvention",
            "grooming",
            "oneway",
            "lit",
            "gladed",
            "patrolled",
            "snowmaking",
        ):
            document[field] = properties.get(field)

        database.runs.update_one(criteria, {"$set": document}, upsert=True)

connection.close()
