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

## User stories

[Link to user stories](https://github.com/software-students-fall2026/web-app-exercise-nocturnal/issues)

## Steps necessary to run the software

team nocturnal is excited you want to run our wonderous application. to start with you must make a choice:

- source data from our shared mongodb atlas (recommended)
- or attempt to run locally

we've looked ahead at the [course's docker notes](https://knowledge.kitchen/content/courses/software-engineering/slides/containers/) and use docker here to keep setup consistent across operating systems.

### shared mongodb atlas (recommended)

1. install and start docker desktop on macos/windows, or docker engine on linux.
2. open a terminal in this repository.
3. reach out to team nocturnal on discord for access to the `.env` file. place it in the repository root and leave `MONGO_LOCAL=false`.
4. build the app image: `docker build -f setup/Dockerfile -t nocturnal .`.
5. create the app network once: `docker network create nocturnal`.
6. start the app: `docker run -d --name ski-app --network nocturnal --env-file .env -p 5000:5000 nocturnal`.
7. open <http://localhost:5000>.

### local mongodb

1. install and start docker desktop on macos/windows, or docker engine on linux.
2. open a terminal in this repository. on windows, use git bash for the copy command below.
3. if you don't already have `.env`, copy the example: `cp .env.example .env`. set `MONGO_LOCAL=true` in `.env`; leave any saved cloud settings (or lack of settings) in place.
4. build the app image: `docker build -f setup/Dockerfile -t nocturnal .`.
5. create the app network once: `docker network create nocturnal`.
6. download the mongodb image: `docker pull mongo:latest`.
7. create the local database: `docker run -d --name ski-app-db --network nocturnal -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=nocturnal_yeti -e MONGO_INITDB_ROOT_PASSWORD=powder_after_dark -v nocturnal-data:/data/db mongo:latest`.
8. start the app: `docker run -d --name ski-app --network nocturnal --env-file .env -p 5000:5000 nocturnal`. `setup/setup.py` loads the seed automatically and preserves existing records and their ids.
9. open <http://localhost:5000>.

### switch modes

1. stop the app: `docker stop ski-app`.
2. remove the app container: `docker rm ski-app`. local database data stays in its volume.
3. set `MONGO_LOCAL=false` for cloud or `MONGO_LOCAL=true` for local in the same `.env` file.
4. for local mode, start the existing database if stopped: `docker start ski-app-db`. follow the local steps first if you haven't created it yet.
5. start the app again: `docker run -d --name ski-app --network nocturnal --env-file .env -p 5000:5000 nocturnal`.
6. open <http://localhost:5000>.

keep `.env` out of version control. use `docker logs ski-app` to inspect startup errors.

## Task boards

[Sprint 1](https://github.com/orgs/software-students-fall2026/projects/13)
[Sprint 2](https://github.com/orgs/software-students-fall2026/projects/13/views/6)
