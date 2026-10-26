# architecture

single person scope.
united states only.

## routes

```text
get   /
get   /find
get   /run/<run_id>
post  /run/<run_id>/save
get   /someday
get   /today
post  /saved/<saved_id>/delete
get   /run/<run_id>/log
post  /run/<run_id>/log
get   /history
get   /attempt/<attempt_id>
post  /attempt/<attempt_id>
post  /attempt/<attempt_id>/delete
```

## models

one mongodb atlas cluster, one database, four collections.
mongodb generates every `_id`. references are objectids, not embedded copies.
optional source fields may be `none`; the run page omits them. source booleans
remain `true` or `false`, including explicit `false` values.

### resorts

```text
{
    "_id": objectid(),
    "source_ids": ["openstreetmap:way/12345"],
    "name": "example resort",
    "country": "us",
    "state": "colorado",
}
```

### runs

```text
{
    "_id": objectid(),
    "source_ids": ["openstreetmap:way/67890"],
    "resort_id": objectid("..."),
    "name": "example run",
    "ref": none,
    "description": none,
    "difficulty": "intermediate",
    difficulty convention: "north_america",
    "grooming": none,
    "oneway": true,
    "lit": none,
    "gladed": none,
    "patrolled": none,
    "snowmaking": true,
    "geometry": {
        "type": "linestring",
        "coordinates": [
            [-105.80, 39.60],
            [-105.79, 39.59],
        ],
    },
}
```

### saved_runs

```text
{
    "_id": objectid(),
    "run_id": objectid("..."),
    "list": "someday",
    "created_at": datetime.datetime.utcnow(),
}
```

### attempts

```text
{
    "_id": objectid(),
    "run_id": objectid("..."),
    "skied_at": datetime.datetime.utcnow(),
    "difficulty_rating": none,
    "notes": "",
    "photo": "filename.jpg",
}
```
