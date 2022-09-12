FROM --platform=linux/amd64 python:3.10-slim

# Set pip to have no saved cache
ENV PIP_NO_CACHE_DIR=false \
    POETRY_VIRTUALENVS_CREATE=false \
    MAX_WORKERS=10

# Install poetry
RUN pip install --upgrade pip
RUN pip install -U poetry

# Create the working directory
WORKDIR /amcef_api

# Install project dependencies from poetry.lock
COPY pyproject.toml poetry.lock ./
RUN poetry install

# Copy the source code in last to optimize rebuilding the image
COPY . .

EXPOSE 80

# Run the 'run' task, starting the API server using uvicorn
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "80", "src.__init__:app"]
