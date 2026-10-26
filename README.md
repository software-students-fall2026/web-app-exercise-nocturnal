# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Team members

- [Christina Lin](https://github.com/christinalin06)
- [Daniel Zhang](https://github.com/danielzhang04/)
- [Jason Wang](https://github.com/TirpitzS128)
- [Rishi Ajoykumar](https://github.com/ajoykumarrishi)
- [Matthew Chen](https://github.com/23matthewc)

## Product vision statement

A mobile web app for skiers to keep track of the runs they're dreaming about, discover new runs, and celebrate the day they finally ride them.

## About our app

Ski-Oked allows users to plan what they want to ski, track each of their ski attempts, and look back on their ski history. Each user's account is only able to view and edit its own runs and attempts. 

### Features

- Sign up, log in, and edit display name through the profile page
- Browse ski runs by country, resort, then run 
- Save runs to the Today or Someday pages
- Log an attempt with information such as the date, completion status, difficulty, optional notes, and uploaded photo
- Edit or delete attempts in the History page
- See Ski-Oked average difficulty ratings for runs 

### How we made the app

- **Flask**
- **MongoDB**
- setup/setup.py loads the ski catalog into an empty database and starts the app
- user-uploaded photos are saved in static/uploads/ on the local computer

### Data

| collection | fields |
|---|---|
| `users` | `_id`, `email` (unique), `password_hash`, `display_name` |
| `resorts` | `_id`, `name`, `country_code`, `country_name`, `region`, `image` |
| `runs` | `_id`, `resort_id`, `name`, `difficulty` (1–5), `description` |
| `saved_runs` | `user_id`, `run_id`, `list` (`today` or `someday`), `created_at` |
| `attempts` | `_id`, `user_id`, `run_id`, `skied_at`, `completed`, `notes`, `difficulty` (1–5, optional), `photo` (optional) |
| `ratings` | `_id`, `user_id`, `run_id`, `difficulty` (1–5), one per user per run |

## User stories

[Link to user stories](https://github.com/software-students-fall2026/web-app-exercise-nocturnal/issues)

## Steps necessary to run the software

team nocturnal is excited you want to run our wonderous application. to start with you must make a choice:

- if you do not have mongodb, follow the docker setup below
- if you already have mongodb, connect to it and run the app directly

we've looked ahead at the [course's docker notes](https://knowledge.kitchen/content/courses/software-engineering/slides/containers/) and use docker here to keep setup consistent across operating systems.

### if you do not have mongodb

1. install and start docker desktop on macos/windows, or docker engine on linux.
2. open a terminal in this repository. on windows, use git bash for the copy command below.
3. copy the example settings: `cp .env.example .env`.
4. build the app image: `docker build -f setup/docker/Dockerfile -t nocturnal .`.
5. generate a session key: `docker run --rm nocturnal python -c "import secrets; print(secrets.token_hex(32))"`. put it after `SECRET_KEY=` in `.env`.
6. in `.env`, change the database host from `127.0.0.1` to `ski-app-db`.
7. create the app network once: `docker network create nocturnal`.
8. download the mongodb image: `docker pull mongo:8.0`.
9. create the local database: `docker run -d --name ski-app-db --network nocturnal -e MONGO_INITDB_ROOT_USERNAME=nocturnal_yeti -e MONGO_INITDB_ROOT_PASSWORD=powder_after_dark -v stoked-data:/data/db mongo:8.0`.
10. start the app: `docker run -d --name ski-app --network nocturnal --env-file .env -v stoked-uploads:/app/static/uploads -p 5000:5000 nocturnal`. `setup/setup.py` loads the catalog into empty collections; use a fresh database for this version.
11. open <http://localhost:5000> and create an account.

next time, start the database with `docker start ski-app-db`, then the app with `docker start ski-app`.

### if you already have mongodb

1. create and activate a python 3.12 virtual environment.
2. install the requirements: `python -m pip install -r requirements.txt`.
3. copy the example settings: `cp .env.example .env`. on windows, use git bash for this command.
4. set `MONGO_URI` to your mongodb connection and `MONGO_DBNAME` to a fresh database in `.env`.
5. generate a session key: `python -c "import secrets; print(secrets.token_hex(32))"`. put it after `SECRET_KEY=` in `.env`.
6. run `python setup/setup.py`.
7. open <http://localhost:5000> and create an account.

keep `.env` out of version control. use `docker logs ski-app` to inspect startup errors.

## Task boards

[Sprint 1](https://github.com/orgs/software-students-fall2026/projects/13)
[Sprint 2](https://github.com/orgs/software-students-fall2026/projects/13/views/6)
