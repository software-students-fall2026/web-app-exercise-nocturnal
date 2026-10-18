"""
basic isolated tests for lookup and personal records.
"""

from bson.objectid import ObjectId


def post(client, path, **data):
    """
    submit a form.
    """

    return client.post(path, data=data, follow_redirects=True)


def catalog(database):
    """
    create a united states resort and run for a test.
    """

    resort_id = database.resorts.insert_one(
        {"name": "Example Resort", "country": "US", "state": "Colorado"}
    ).inserted_id

    run_id = database.runs.insert_one(
        {
            "resort_id": resort_id,
            "name": "Example Run",
            "difficulty": "intermediate",
            "grooming": None,
            "snowmaking": False,
            "description": "<script>source description</script>",
            "difficultyConvention": "north_america",
            "geometry": {"type": "LineString", "coordinates": [[2, 1], [3, 2]]},
        }
    ).inserted_id

    return str(resort_id), str(run_id)


def test_lookup(client, database):
    """
    state, resort, and run filters stay on one read-only page.
    """

    resort_id, run_id = catalog(database)

    database.resorts.insert_one(
        {"name": "Other Resort", "country": "US", "state": "Utah"}
    )
    foreign_id = database.resorts.insert_one(
        {"name": "Canadian Resort", "country": "CA", "state": "Ontario"}
    ).inserted_id

    assert b"Colorado" in client.get("/find").data
    assert b"Example Resort" not in client.get("/find").data

    response = client.get("/find?state=Colorado")

    assert b"Example Resort" in response.data
    assert b"Other Resort" not in response.data
    assert b"Example Run" not in response.data

    path = "/find?state=Colorado&resort_id=" + resort_id

    assert b"Example Run" in client.get(path).data
    assert b"Example Run" in client.get(path + "&name=run").data
    assert b"No runs found" in client.get(path + "&name=.*").data

    assert (
        b"Example Run" not in client.get("/find?state=Utah&resort_id=" + resort_id).data
    )
    assert client.get("/find?resort_id=" + str(foreign_id)).status_code == 404
    assert client.get("/find?resort_id=invalid").status_code == 404

    assert b"<polyline" in client.get("/run/" + run_id).data

    details = client.get("/run/" + run_id).data

    assert b"snowmaking: false" in details
    assert b"difficultyConvention: north_america" in details
    assert b"&lt;script&gt;source description&lt;/script&gt;" in details
    assert b"grooming:" not in details

    assert b"Example Run" in client.get("/find?resort_id=" + resort_id).data
    assert database.saved_runs.count_documents({}) == 0


def test_empty_catalog_and_removed_routes(client):
    """
    empty results are clear and the old service routes are absent.
    """

    assert b"No catalog uploaded" in client.get("/find").data
    assert b"No resorts" in client.get("/find?state=Unknown").data

    for path in (
        "/login",
        "/signup",
        "/profile",
        "/find/resorts",
        "/resort/invalid/refresh",
    ):
        assert client.get(path).status_code == 404

    response = client.get("/")

    assert b"<nav>" in response.data
    assert b"<li>" in response.data
    assert b"<script" not in response.data


def test_saved_runs(client, database):
    """
    saving is repeatable and independent for each list.
    """

    _, run_id = catalog(database)
    path = "/run/" + run_id + "/save"

    for destination in ("someday", "someday", "today"):
        assert post(client, path, destination=destination).status_code == 200

    assert database.saved_runs.count_documents({}) == 2

    for page in ("someday", "today"):
        assert b"Example Run" in client.get("/" + page).data

    document = database.saved_runs.find_one({"list": "today"})
    post(client, "/saved/" + str(document["_id"]) + "/delete")

    assert database.saved_runs.count_documents({"list": "someday"}) == 1


def test_attempts(client, database):
    """
    attempts can be saved, edited, and deleted without changing the catalog.
    """

    _, run_id = catalog(database)
    data = {"skied_at": "2026-10-18T12:00", "notes": "", "difficulty_rating": ""}

    assert post(client, "/run/" + run_id + "/log", **data).status_code == 200

    document = database.attempts.find_one()
    path = "/attempt/" + str(document["_id"])

    data.update(notes="<script>reflection</script>", difficulty_rating="advanced")

    assert b"&lt;script&gt;" in post(client, path, **data).data
    assert b"Example Run" in client.get("/history").data

    assert post(client, path, skied_at="invalid").status_code == 400

    post(client, path + "/delete")

    assert database.attempts.count_documents({}) == 0
    assert database.runs.count_documents({"_id": ObjectId(run_id)}) == 1


def test_database_unavailable(client, database, monkeypatch):
    """show a useful error without leaking connection details."""

    def unavailable(*args, **kwargs):
        raise RuntimeError("private connection details")

    monkeypatch.setattr(database.resorts, "distinct", unavailable)

    response = client.get("/find")

    assert response.status_code == 503
    assert b"Database unavailable" in response.data
    assert b"private connection details" not in response.data
