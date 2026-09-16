# Getting Started

This guide explains how to set up and run the AFRI-EDGE project locally.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional, for containerized deployment)

## Running with Docker (Recommended)

The easiest way to run the project is with Docker Compose:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Running Locally

### 1. Create a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Start the server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## Running Tests

Install test dependencies and run pytest:

```bash
pip install -e ".[test]"
pytest
```

## API Endpoints

Once running, visit `http://localhost:8000/docs` for the interactive Swagger UI documentation.

The primary routing endpoint:

```
POST /route
```

This endpoint accepts a workload profile, evaluates infrastructure state, and returns a routing decision.
