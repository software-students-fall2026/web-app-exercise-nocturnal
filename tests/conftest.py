"""use a fresh in-memory database for each test."""

import sys
from pathlib import Path

import mongomock
import pytest
import pymongo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def database():
    """create a test database."""

    return mongomock.MongoClient().ski_app


@pytest.fixture
def app(monkeypatch, database):
    """run the app without connecting to atlas."""

    monkeypatch.setattr(pymongo, "MongoClient", lambda *args, **kwargs: database.client)
    monkeypatch.setenv("MONGO_DBNAME", "ski_app")

    from app import create_app

    app = create_app()
    app.config["TESTING"] = True

    return app


@pytest.fixture
def client(app):
    """open a test browser."""

    return app.test_client()
