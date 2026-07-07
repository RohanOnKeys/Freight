# API Routes

This document defines every route exposed by the Freight server.

The goal is to keep the API predictable and RESTful while separating responsibilities between routers.

---

# Route Structure

```text
/api
│
├── /health
├── /webhooks
├── /pipelines
├── /jobs
├── /runners
├── /artifacts
└── /secrets
```

---

# Health

Base Path

```text
/api/health
```

## GET /

Purpose

Returns the current status of the Freight server.

Response

```json
{
    "status": "ok"
}
```

Used by

* Docker health checks
* Reverse proxies
* Monitoring services

---

# Webhooks

Base Path

```text
/api/webhooks
```

## POST /github

Purpose

Receives GitHub webhook events.

Responsibilities

* Verify webhook signature
* Parse payload
* Create a Pipeline
* Generate Jobs
* Push jobs into Redis

Returns

```json
{
    "message": "Pipeline created",
    "pipeline_id": 1
}
```

---

# Pipelines

Base Path

```text
/api/pipelines
```

## GET /

Returns all pipelines.

---

## GET /{pipeline_id}

Returns a single pipeline.

Includes

* metadata
* jobs
* status
* timestamps

---

## GET /{pipeline_id}/jobs

Returns every job belonging to a pipeline.

---

## DELETE /{pipeline_id}

Deletes a pipeline.

Also removes

* jobs
* artifacts

---

# Jobs

Base Path

```text
/api/jobs
```

## GET /

Returns every job.

---

## GET /{job_id}

Returns one job.

---

## POST /{job_id}/retry

Retries a failed job.

Scheduler places it back into Redis.

---

## POST /{job_id}/cancel

Cancels a running job.

---

## PATCH /{job_id}/status

Used internally by runners.

Updates

* status
* exit code
* timestamps

---

# Runners

Base Path

```text
/api/runners
```

## POST /register

Registers a new runner.

Returns

Runner ID

Authentication token

---

## POST /heartbeat

Updates runner heartbeat.

Marks runner as alive.

---

## GET /

Returns every runner.

---

## GET /{runner_id}

Returns runner information.

Includes

* status
* current job
* last heartbeat

---

# Artifacts

Base Path

```text
/api/artifacts
```

## GET /{artifact_id}

Downloads an artifact.

---

## GET /job/{job_id}

Returns every artifact produced by a job.

---

## DELETE /{artifact_id}

Deletes an artifact.

Removes

* database record
* stored file

---

# Secrets

Base Path

```text
/api/secrets
```

## GET /

Returns secret metadata.

Does not expose secret values.

---

## POST /

Creates a new encrypted secret.

---

## PUT /{secret_id}

Updates an existing secret.

---

## DELETE /{secret_id}

Deletes a secret.

---

# API Flow

```text
Client

   │

   ▼

FastAPI

   │

   ▼

Router

   │

   ▼

Service

   │

   ▼

SQLAlchemy

   │

   ▼

PostgreSQL
```

---

# Request Flow

```text
HTTP Request

      │

      ▼

main.py

      │

      ▼

Router

      │

      ▼

Pydantic Validation

      │

      ▼

Service Layer

      │

      ▼

Database

      │

      ▼

Response Schema

      │

      ▼

JSON Response
```

---

# Router Layout

```text
freight/
│
├── routers/
│   ├── health.py
│   ├── webhooks.py
│   ├── pipelines.py
│   ├── jobs.py
│   ├── runners.py
│   ├── artifacts.py
│   └── secrets.py
```

---


This document represents the planned API structure. Routes will be implemented incrementally as each backend component is completed.