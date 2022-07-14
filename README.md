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
# URL for the external API to fetch and verify data against. Value below is default
API_BASE_URL="https://jsonplaceholder.typicode.com"
# When set to a truthy value, log level will be set to debug
DEBUG=1
# When set, a log file will be generated with given name. Note that if docker is used,
# this log file will be generated within the container
LOG_FILE="output.log"
# Used in combination with LOG_FILE. If set, the log file content will be getting rotated
# up to given file size in bytes.
LOG_MAX_FILE_SIZE=1000000
```

## API Documentation

The documentation is generated with rapidoc using the automatically generated openapi schema. This documentation will
be present on the `/docs` endpoint of the API.
