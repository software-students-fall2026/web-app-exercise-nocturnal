"""load the catalog and start stoked."""

import gzip
import os
from pathlib import Path
import secrets
import sys
from bson import json_util
from dotenv import load_dotenv
from pymongo import MongoClient

# 1) create .env if it is missing
root = Path(__file__).resolve().parent.parent
os.chdir(root)
if not Path(".env").exists():
    example = Path(".env.example").read_text()
    # just running black makes it look like this.
    # was all one line originally.
    Path(".env").write_text(
        example.replace("SECRET_KEY=\n", "SECRET_KEY=" + secrets.token_hex(32) + "\n")
    )
load_dotenv(".env")

# 2) load the catalog into empty collections
with MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=5000) as client:
    db = client[os.environ["MONGO_DBNAME"]]
    with gzip.open("setup/data/catalog.json.gz", "rt", encoding="utf-8") as file:
        catalog = json_util.loads(file.read())
    for name, docs in catalog.items():
        if db[name].count_documents({}) == 0:
            db[name].insert_many(docs)

# 3) start flask
# just running black makes it look like this.
# was all one line originally.
os.execvp(
    sys.executable,
    [
        sys.executable,
        "-m",
        "flask",
        "--app",
        "app",
        "run",
        "--host=" + os.getenv("FLASK_HOST", "127.0.0.1"),
        "--port=" + os.getenv("FLASK_PORT", "5000"),
    ],
)
