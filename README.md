# AMCEF API

## Setting up the project

This project uses `docker-compose` to setup the stack quickly. Running `docker-compose up` after setting up environment
variables will start the development server on `http://localhost:8000`.

## Manual installation - without docker

If desired, the project can also be ran on it's own without docker containerization. This is useful when you already
have a PostgreSQL database ready and you don't want to spin up a new one. In this case you'll need to install `poetry`,
which is a tool used for managing python requirements and virtual environments. To install it, run `pip install
poetry`. After that, make sure you're in the root directory of the project and run `poetry install`. This will install
all project dependencies (including the development dependencies, such as linters, if you only want the production
dependencies, use `--no-dev` flag).

To run the project, you can then use `poetry run task run` (or `poetry run task run-dev` for debug logs and reloading).

## Environment Variables

For the project to work properly, you need to define all environment variables in `.env` file, which is then picked up
by docker, but also directly by decouple if used without docker.

This project requires defining these variables:
```bash
# Postgres database URL. Set automatically when using docker-compose.
# Note that the URL shouldn't include the scheme part - 'postgres://', it's already assumed
DATABASE_URL="amcef:amcef@127.0.0.1:5000/amcef"
# Redis database URL. Set automatically when using docker-compose.
# Note that the URL should include the schema part - 'redis://'
REDIS_URL=redis://<address>:<port>/<db id>?password=<password>
# URL for the external API to fetch and verify data against. Value below is default
API_BASE_URL="https://jsonplaceholder.typicode.com"

# When set to a truthy value, log level will be set to debug and admin endpoints will
# be shown in the API docs
DEBUG=1
# When set, a log file will be generated with given name. Note that if docker is used,
# this log file will be generated within the container
LOG_FILE="output.log"
# Used in combination with LOG_FILE. If set, the log file content will be getting rotated
# up to given file size in bytes.
LOG_MAX_FILE_SIZE=1000000

# How many requests can a member make to rate limited endpoitns in given time period (default 3)
REQUESTS_PER_PERIOD=3
# Time period (in seconds) during which a member can make REQUESTS_PER_PERIOD amount of requests
# (default 20 seconds)
TIME_PERIOD=20
# Cooldown period (in seconds), which is trigerred when a member makes more requests than they're
# allowed (default 100 seconds)
COOLDOWN_PERIOD=100
```

## Adding a new admin member for the API

To meaningfully use the API, you will need at least one admin member API token. While there are some unrestricted
endpoints such as GET on `/posts/{post_id}`, endpoints which actually edit some information are restricted and can only
be used with a valid member API token.

An admin level token can also access some privileged endpoints, like the POST on `/member`, with which new API members
can be easily created (both admins and non-admins).

To initially get an admin level API token, you can simply run the `/make_member.py` script. If you're running manually
(without using docker), this is as simple as running the script from the project's root. However if you are using
docker, you'll need to run a command from within that container. To do that, you can simply use `doceker-compose run
api [command]` where the command can simply be `./make_member.py`, executing the script.

After running the script, you will see a long string of random characters, which will be your API token, and a user id,
which is mostly irrelevant to you. You will want to copy this token and use it as described in the
[section below](#using-an-api-token).

![image](https://user-images.githubusercontent.com/20902250/178942172-63c28591-0098-43ef-b764-7b336cbd2b81.png)

## Using an API token

This API uses a so called "Bearer scheme" authentication. This is a commonly used format, where in order to make
authenticated requests, you'll need to set the `Authentication` header with value of `Bearer [your_token]`.

As an example, here's a request to POST on `/post` endpoint using curl:
```bash
curl -v -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwic2FsdCI6Im9iV3cxb0tVLWJ4eXR5SzBTUE0xNHcifQ.gmyviS8MTijK4MCPf3TKBqbmct1W9QqwkR7ynR0VWBc" -X POST http://localhost:8000/post --json '{"user_id": 1, "title: "Sample post", "body": "Some content"}'
```

Note that this is just an example token, you will need to get your token from an admin, or by generating it with
`./make_member.py` script, as described in the [above section](#adding-a-new-admin-member-for-the-api).

## Database migrations

We're using `alembic` to handle SQL migrations, which we have 2 taskipy aliases for:
```bash
poetry run task apply-migrations
poetry run task make-migrations
```

You can use `apply-migrations` whenever you pull in new changes, and there was a change in the database structure.
Alembic will automatically use the defined migrations to make your database up-to-date with the latest model.

You can use `make-migrations` when making changes to the database during development. You should always run this
command right after editing the database models, and before actually making the changes into database. Alembic will
then automatically pick up on the differences between the model and the actual db, and generate migrations based on
that (this might require intervention though). After that, you should run `apply-migrations` to actually update the
database with alembic, according to this new migration.

## API Documentation

The documentation is generated with rapidoc using the automatically generated openapi schema. This documentation will
be present on the `/docs` endpoint of the API.
