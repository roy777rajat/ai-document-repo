FROM python:3.10-slim

WORKDIR /app

# Install apt deps for common libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app

# Install python deps
RUN pip install --upgrade pip && pip install -r requirements.txt

ENV PORT=8000

# Run Uvicorn using shell so environment variable $PORT is expanded by the shell
# Use a default of 8000 if PORT is not provided by the environment
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
