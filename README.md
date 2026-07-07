

# Freight

A distributed CI/CD platform built from scratch to understand how modern build automation systems work internally.

Freight receives GitHub events, creates pipelines, schedules jobs, dispatches work to independent runner agents, executes jobs inside isolated Docker containers, stores artifacts, manages secrets securely, and provides a live view of every pipeline.

---

# What Freight Does

* Receives GitHub webhooks
* Parses `.freight.yml`
* Builds a job dependency graph
* Schedules pipeline execution
* Dispatches jobs through Redis
* Executes jobs inside Docker containers
* Streams job logs
* Stores build artifacts
* Manages encrypted secrets
* Tracks runner health
* Reports pipeline status
* Displays live pipeline progress

---

# Architecture

```text
GitHub Push

↓

Webhook

↓

Freight Server

↓

PostgreSQL
Pipeline State

↓

Redis
Job Queue

↓

Freight Runners

↓

Docker Containers

↓

Artifact Store

↓

Freight Dashboard
```

The server coordinates the system.

Runner agents execute every job.

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
| Artifact Storage | Local Filesystem / MinIO |

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

  test:
    needs:
      - build

    image: python:3.12

    script:
      - pytest
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

Receives webhooks, parses pipeline configurations, builds execution graphs, schedules jobs, manages runners, tracks pipeline state, and serves the API and dashboard.

## Freight Runner

Registers with the server, polls Redis for work, claims jobs, launches Docker containers, streams logs, uploads artifacts, reports results, and sends heartbeat updates.

## Queue

Redis distributes jobs across available runners and ensures work is processed efficiently.

## Database

PostgreSQL stores pipelines, jobs, runners, artifacts, secrets, and execution history.

## Dashboard

Displays pipeline history, live job status, logs, artifacts, and runner activity.

---

# Pipeline Flow

```text
Git Push

↓

Webhook Received

↓

Pipeline Created

↓

Configuration Parsed

↓

Jobs Scheduled

↓

Runner Claims Job

↓

Docker Executes Job

↓

Logs Stream

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
* Runner heartbeat monitoring
* Automatic job retry
* Fault recovery
* Secure secret management
* Artifact storage
* Live pipeline dashboard
* GitHub webhook integration
* REST API
* Command Line Interface
