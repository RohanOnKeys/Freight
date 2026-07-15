# Freight

A distributed CI/CD platform built from scratch to understand how modern build automation systems work internally.

Freight receives GitHub events, creates pipelines, parses pipeline definitions, schedules jobs, dispatches work to independent runner agents, executes jobs inside isolated Docker containers, stores artifacts, manages encrypted secrets, monitors runner health, and provides a live view of every pipeline.

---

# What Freight Does

* Receives GitHub webhooks
* Parses `.freight.yml`
* Builds a job dependency graph
* Schedules pipeline execution
* Dispatches jobs through Redis
* Executes jobs inside Docker containers
* Streams job logs
* Preserves artifact metadata throughout the execution pipeline
* Stores build artifacts on the server
* Exposes artifact upload and retrieval APIs
* Manages encrypted secrets
* Tracks runner health
* Automatically retries failed jobs
* Reports pipeline status
* Displays live pipeline progress

---

# Architecture

```text
GitHub Push

↓

Webhook

↓

Pipeline Parser

↓

PostgreSQL
Pipeline + Job State

↓

Redis
Job Queue

↓

Freight Runners

↓

Docker Containers

↓

Artifact Upload

↓

Artifact Store

↓

Freight Dashboard
```

The Freight server coordinates the entire execution pipeline.

Runner agents execute every job independently inside isolated Docker containers.

---

# Tech Stack

| Component | Technology |
| ---------- | ---------- |
| Backend | FastAPI |
| Database | PostgreSQL |
| Queue | Redis |
| Runner | Python |
| Container Runtime | Docker |
| Dashboard | FastAPI + Jinja2 |
| Artifact Storage | Local Filesystem (MinIO planned) |

---

# Pipeline Configuration

```yaml
stages:
  - build
  - test

jobs:
  build:
    image: python:3.12

    script:
      - python build.py

    artifacts:
      - dist/*
      - reports/output.txt

  test:
    needs:
      - build

    image: python:3.12

    script:
      - pytest
```

---

# Artifact Pipeline

Freight preserves artifact metadata from the moment a pipeline is parsed until the runner uploads the generated files.

```text
.freight.yml

↓

pipeline_parser.py

↓

Job Model

↓

PostgreSQL

↓

GET /jobs/{id}

↓

Runner

↓

artifact_uploader.py

↓

POST /jobs/{id}/artifacts

↓

Artifact Storage
```

Artifact definitions travel naturally with each job, allowing runners to upload only the files declared inside `.freight.yml`.

Artifact paths stored inside the database remain relative to the configured artifact root, improving portability across environments.

Example:

```
artifacts/12/48/output.txt
```

instead of

```
C:\Users\...\artifacts\12\48\output.txt
```

---

# Project Structure

```text
freight/

server/
runner/
dashboard/
cli/
database/
artifacts/
tests/

.freight.yml
```

---

# Core Components

## Freight Server

Receives GitHub webhooks, parses pipeline configurations, builds execution graphs, schedules jobs, manages runners, tracks pipeline state, persists artifact metadata, stores uploaded artifacts, manages encrypted secrets, and serves both the REST API and dashboard.

## Freight Runner

Registers with the server, polls Redis for work, atomically claims jobs, launches Docker containers, streams logs, uploads artifacts declared by the pipeline, reports execution results, and continuously sends heartbeat updates.

## Queue

Redis distributes jobs across available runners while ensuring safe job claiming and efficient scheduling.

## Database

PostgreSQL stores pipelines, jobs, runners, artifacts, secrets, execution history, and artifact metadata used during job execution.

## Dashboard

Displays pipeline history, live job status, logs, artifacts, and runner activity.

---

# Pipeline Flow

```text
Git Push

↓

Webhook Received

↓

Pipeline Parsed

↓

Job Graph Created

↓

Jobs Stored

↓

Jobs Scheduled

↓

Runner Claims Job

↓

Docker Executes Job

↓

Logs Stream

↓

Artifacts Uploaded

↓

Artifacts Stored

↓

Pipeline Completed
```

---

# Features

* Distributed runner architecture
* Docker based isolated execution
* Job dependency scheduling
* Parallel job execution
* Atomic job claiming
* Redis backed distributed job queue
* GitHub webhook integration
* `.freight.yml` pipeline parsing
* Artifact metadata propagation
* Artifact upload API
* Artifact retrieval API
* Relative artifact path storage
* Local filesystem artifact storage
* Secure secret management with encryption
* Runner heartbeat monitoring
* Automatic job retry
* Fault recovery
* Live pipeline dashboard
* REST API
* Command Line Interface

---

# Current Status

### Completed

- GitHub webhook processing
- Pipeline parsing
- DAG validation
- PostgreSQL persistence
- Redis scheduling
- Runner registration
- Heartbeat monitoring
- Atomic job claiming
- Docker execution
- Live log streaming
- Job completion reporting
- Artifact upload API
- Artifact retrieval API
- Artifact persistence
- Filesystem artifact storage
- Artifact metadata propagation

### In Progress

- Automatic artifact uploading from runners

### Planned

- Dashboard
- CLI
- MinIO artifact backend
- Multi runner deployment
- Comprehensive integration tests
