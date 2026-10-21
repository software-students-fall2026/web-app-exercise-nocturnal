"""
prepare the local database when selected, then start the flask application.
"""

import gzip
import os
import sys

from bson import json_util
from pymongo import MongoClient, UpdateOne


def setup_local_database():
    """
    load the local ski catalog while keeping saved records and their ids.
    returns:
        none: the local connection settings and database are ready for flask.
    """

    # 1) give the nocturnal ski patrol its local database credentials
    local_username = "nocturnal_yeti"
    local_password = "powder_after_dark"
    local_database_name = "sweProject2"
    local_database_uri = (
        f"mongodb://{local_username}:{local_password}"
        "@ski-app-db:27017/?authSource=admin"
    )
    os.environ["MONGO_LOCAL_URI"] = local_database_uri
    os.environ["MONGO_DBNAME"] = local_database_name

    # 2) unpack the seed and restore the mongodb ids stored in the file
    with gzip.open("setup/catalog.json.gz", "rt", encoding="utf-8") as seed_file:
        catalog = json_util.loads(seed_file.read())

    # 3) connect to the local server and open the app database
    with MongoClient(local_database_uri) as connection:
        database = connection[local_database_name]

        # 4) keep an older local catalog if it already has its own record ids
        existing_resort = database.resorts.find_one({}, {"_id": 1})
        seed_resort_ids = {resort["_id"] for resort in catalog["resorts"]}

        if existing_resort is None or existing_resort["_id"] in seed_resort_ids:
            # 5) update or insert seed records without creating duplicate ids
            for collection_name, documents in catalog.items():
                database[collection_name].bulk_write(
                    [
                        UpdateOne(
                            {"_id": document["_id"]},
                            {
                                "$set": {
                                    field: value
                                    for field, value in document.items()
                                    if field != "_id"
                                }
                            },
                            upsert=True,
                        )
                        for document in documents
                    ]
                )

        # 6) index the fields used to find resorts and their runs
        database.resorts.create_index([("country", 1), ("state", 1), ("name", 1)])
        database.runs.create_index("resort_id")


if __name__ == "__main__":
    # 1) initialize local data only when the single env flag selects local mode
    if os.getenv("MONGO_LOCAL", "false").lower() == "true":
        setup_local_database()

    # 2) start flask with the selected connection settings and the same python runtime
    os.execvp(
        sys.executable,
        [sys.executable, "-m", "flask", "--app", "app", "run", "--host=0.0.0.0"],
    )
