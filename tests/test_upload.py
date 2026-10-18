"""
basic checks for the catalog upload without atlas access.
"""

import copy
import os
import runpy
from unittest.mock import mock_open, patch
from bson.objectid import ObjectId


def upload(database, ski_areas, runs):
    """
    run the script using isolated catalog data and a mock database.
    """

    with patch("builtins.open", mock_open()), patch(
        "json.load", side_effect=[{"features": ski_areas}, {"features": runs}]
    ), patch("dotenv.load_dotenv"), patch(
        "pymongo.MongoClient", return_value=database.client
    ), patch.dict(
        os.environ, {"MONGO_DBNAME": database.name}
    ), patch(
        "sys.argv", ["upload.py", "ski_areas.geojson", "runs.geojson"]
    ):
        runpy.run_path("upload.py")


def test_upload(database):
    """
    only us downhill data is uploaded; repeated builds preserve saved ids.
    """

    area = {
        "properties": {
            "id": "area-build-one",
            "name": "Example Resort",
            "activities": ["downhill"],
            "sources": [{"type": "skimap.org", "id": 1}],
            "places": [
                {"iso3166_1Alpha2": "US", "localized": {"en": {"region": "Colorado"}}}
            ],
        }
    }

    run = {
        "geometry": {"type": "LineString", "coordinates": [[2, 1, 100], [3, 2, 90]]},
        "properties": {
            "id": "run-build-one",
            "name": "Example Run",
            "uses": ["downhill"],
            "difficulty": "easy",
            "snowmaking": False,
            "difficultyConvention": "north_america",
            "sources": [{"type": "openstreetmap", "id": "way/2"}],
            "skiAreas": [{"properties": {"id": "area-build-one"}}],
        },
    }

    foreign = copy.deepcopy(area)
    foreign["properties"].update(
        id="foreign",
        name="Canadian Resort",
        sources=[{"type": "skimap.org", "id": 3}],
    )
    foreign["properties"]["places"][0]["iso3166_1Alpha2"] = "CA"

    nordic = copy.deepcopy(run)
    nordic["properties"].update(
        uses=["nordic"], sources=[{"type": "openstreetmap", "id": "way/4"}]
    )

    upload(database, [area, foreign], [run, nordic])

    resort_id = database.resorts.find_one()["_id"]
    run_id = database.runs.find_one()["_id"]

    assert isinstance(run_id, ObjectId)
    assert database.resorts.find_one()["source_ids"] == ["skimap.org:1"]
    assert database.runs.find_one()["snowmaking"] is False
    assert database.runs.find_one()["difficultyConvention"] == "north_america"
    assert database.runs.find_one()["geometry"]["coordinates"] == [[2, 1], [3, 2]]

    database.saved_runs.insert_one({"run_id": run_id, "list": "today"})

    area["properties"]["id"] = "area-build-two"
    run["properties"]["skiAreas"][0]["properties"]["id"] = "area-build-two"
    run["properties"].update(id="run-build-two", name="Updated Run")

    upload(database, [area], [run])

    assert database.resorts.count_documents({}) == 1
    assert database.runs.count_documents({}) == 1
    assert database.resorts.find_one()["_id"] == resort_id
    assert database.runs.find_one()["_id"] == run_id
    assert database.runs.find_one()["name"] == "Updated Run"
    assert database.saved_runs.find_one()["run_id"] == run_id
