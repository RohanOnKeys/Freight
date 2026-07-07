# Freight Database Model Workflow

## Overview

Everything starts with a GitHub push.

The webhook receives the payload and creates a new pipeline. The pipeline parser reads the `.freight.yml` file and creates all the jobs for that pipeline. The scheduler checks which jobs have no dependencies and pushes only those jobs into Redis.

A runner picks up a queued job, updates its status, runs it inside Docker, uploads any artifacts, reports the result, and then the scheduler checks if more jobs can now be released.

This repeats until every job finishes. Once every job is complete, the pipeline is marked as completed.

---

# Database Models

## Pipeline

Represents one complete CI/CD execution.

One GitHub push creates one pipeline.

### Fields

| Field | Type |
|--------|------|
| id | Primary Key |
| repo | String |
| commit_sha | String |
| branch | String |
| status | String |
| created_at | Timestamp |

### Relationships

One Pipeline has many Jobs.

---

## Job

Represents one stage in the pipeline.

Examples include Build, Test, Lint, Package or Deploy.

Every job belongs to exactly one pipeline.

### Fields

| Field | Type |
|--------|------|
| id | Primary Key |
| pipeline_id | Foreign Key |
| runner_id | Foreign Key |
| name | String |
| stage | String |
| needs | JSON |
| image | String |
| script | JSON |
| status | String |
| retries | Integer |
| exit_code | Integer |
| started_at | Timestamp |
| finished_at | Timestamp |

### Relationships

Belongs to one Pipeline.

Can be executed by one Runner.

Can produce multiple Artifacts.

---

## Runner

Represents a worker machine.

The runner continuously waits for work from Redis.

### Fields

| Field | Type |
|--------|------|
| id | Primary Key |
| hostname | String |
| status | String |
| last_heartbeat | Timestamp |

### Relationships

One Runner executes many Jobs over time.

---

## Artifact

Represents files generated after a job finishes.

Examples include binaries, logs and zip files.

### Fields

| Field | Type |
|--------|------|
| id | Primary Key |
| job_id | Foreign Key |
| path | String |
| size | Integer |
| created_at | Timestamp |

### Relationships

Belongs to one Job.

---

## Secret

Stores encrypted credentials.

Secrets are never stored in plaintext.

They are decrypted only in memory before the Docker container starts.

### Fields

| Field | Type |
|--------|------|
| id | Primary Key |
| name | String |
| encrypted_value | String |
| scope | String |

---

# Database Relationships

```text
Pipeline (1)
    │
    │
    ▼
Jobs (Many)
    │
    ├──────────────► Runner
    │
    └──────────────► Artifacts

Secrets are fetched separately when a job starts.
```

---

# Workflow

```text
GitHub Push

        │

        ▼

Webhook

        │

        ▼

Create Pipeline

        │

        ▼

Parse .freight.yml

        │

        ▼

Create Job Records

        │

        ▼

Scheduler

        │

        ▼

Redis Queue

        │

        ▼

Runner Claims Job

        │

        ▼

Docker Executes Job

        │

        ├────► Load Secrets

        ├────► Generate Logs

        └────► Generate Artifacts

        │

        ▼

Update Job Status

        │

        ▼

Scheduler Checks Remaining Jobs

        │

        ├────► More jobs ready

        │           │

        │           ▼

        │      Push to Redis

        │

        ▼

All Jobs Finished

        │

        ▼

Pipeline Completed
```

---

# Model Interaction

```text
GitHub Push
      │
      ▼
Pipeline
      │
      ▼
Jobs
      │
      ▼
Redis Queue
      │
      ▼
Runner
      │
      ▼
Docker
      │
      ├── Uses Secrets
      ├── Produces Artifacts
      └── Updates Job
      │
      ▼
Scheduler
      │
      ▼
Next Jobs
      │
      ▼
Pipeline Complete
```

---

# Flow Summary

One webhook creates one pipeline.

One pipeline creates multiple jobs.

The scheduler decides which jobs can run.

Ready jobs go into Redis.

A runner claims a job and runs it inside Docker.

The runner uploads artifacts and reports the result.

The scheduler checks whether dependent jobs can now start.

The cycle continues until every job finishes.

The pipeline is then marked as completed.