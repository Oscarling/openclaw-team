# Argus Deployment Contract

This document defines the real deployment assumptions for the Phase 6 stabilized runtime.
It is intentionally concrete and operations-oriented.

## Runtime Topology

- `manager` is the only long-running service entrypoint in normal mode.
- workers run as one-shot containers created by `skills/delegate_task.py`.
- one-shot lifecycle is: start -> execute -> write `output.json` -> exit -> cleanup.

## /app Mount Model

The manager container must provide a consistent `/app` view of project state.

Required writable mounts:

- `/app/workspaces`
- `/app/artifacts`
- `/app/tasks`

Required read/write contract/runtime mounts:

- `/app/contracts`
- `/app/dispatcher`
- `/app/agents`

Optional but recommended:

- `/app/scripts`
- `/app/containers`

If mount discovery from manager is used, these destinations are validated before worker start.

## Shared Directory Rules

### /app/workspaces

- worker private execution state lives under `workspaces/<worker>/<task_id>/`.
- required files per task:
  - `task.json`
  - `output.json`
  - `runtime.log`
- retry attempts may generate `runtime.attempt-<n>.log`.

### /app/artifacts

- only final artifacts are written here.
- all contract-facing paths must remain relative (`artifacts/...`).

### /app/tasks

- manager task record path is `/app/tasks/<task_id>.json`.
- task record tracks current status plus attempt history.

## Secrets Contract (/run/secrets)

At least one of each pair must be available:

- API key:
  - `/run/secrets/openai_api_key` or env `OPENAI_API_KEY` / `API_KEY`
- API base:
  - `/run/secrets/openai_api_base` or env `OPENAI_API_BASE` / `API_BASE`
- model name:
  - `/run/secrets/openai_model_name` or env `OPENAI_MODEL_NAME` / `MODEL_NAME` / compatible aliases

One-shot workers receive these values via environment injection from manager context.

## Environment Overrides

Supported manager environment overrides:

- `ARGUS_WORKER_IMAGE`
  - default worker image tag (default `argus-worker:latest`)
- `ARGUS_WORKER_BUILD_CONTEXT`
  - docker build context used when worker image is missing
- `ARGUS_WORKER_DOCKERFILE`
  - worker Dockerfile path relative to build context
- `ARGUS_MANAGER_CONTAINER_NAME`
  - manager container name used for mount discovery
- `ARGUS_APP_HOST_PATH`
  - optional direct host path mapped to `/app` for one-shot workers
- `ARGUS_SECRETS_HOST_PATH`
  - optional direct host path mapped to `/run/secrets` for one-shot workers

Test-only (default off):

- `ARGUS_TEST_MODE`
- `ARGUS_TEST_SCENARIO`
- `ARGUS_TEST_LLM_RESPONSE_FILE`

These only affect runtime when explicitly set and are intended for controlled deployment validation.

## Worker Image Strategy

- canonical worker image: `argus-worker:latest`.
- one-shot startup first checks image existence; if absent, it builds from:
  - `ARGUS_WORKER_BUILD_CONTEXT`
  - `ARGUS_WORKER_DOCKERFILE`
- worker image must include runtime dependencies required by `dispatcher/worker_runtime.py`.

## One-shot Cleanup Expectations

- every task should end with no residual `argus-*` execution container.
- cleanup is attempted in all paths (success/failed/timeout/start error).
- operations validation should include `docker ps -a` check for `argus-` leftovers.

## Real Deployment Acceptance Checklist (Minimum)

1. Docker CLI and daemon are reachable.
2. manager can access Docker socket.
3. worker image exists or can be built.
4. one-shot success/failed/partial plus automation and critic tasks run end-to-end.
5. each task has `task.json`, `output.json`, `runtime.log`.
6. `output.json` validates against `contracts/output.schema.json`.
7. task status equals `output.json.status`.
8. no leftover one-shot containers after runs.
