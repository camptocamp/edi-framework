This module integrates EDI exchange records with
[Queue Job](https://github.com/OCA/queue), so that the four core exchange
actions — **generate**, **send**, **receive**, and **process** — are dispatched
as background jobs instead of running synchronously.

## Features

### Automatic job dispatch

All `action_exchange_*` methods on `edi.exchange.record` are patched at startup
to run via `queue.job`. No per-record configuration is required; the integration
is active for every exchange type as soon as the module is installed.

### Per-type job configuration

Each **Exchange Type** gains a *Queue* tab with three optional settings:

| Field | Purpose |
|---|---|
| **Job channel** | Route jobs to a specific channel (e.g. `root.edi.high`). |
| **Job priority** | Integer priority passed to the queue job (lower = higher priority). |
| **Execute at** | Daily time at which jobs should be scheduled (see below). |

### Timezone-aware daily scheduling (`Execute at`)

The **Execute at** field (`eta_time`) accepts a decimal hour in the range
`[0, 24)` expressed in the **current user's timezone**:

- `22.0` → 22:00 local time
- `22.5` → 22:30 local time
- `6.25` → 06:15 local time

At runtime the value is converted to the next matching UTC datetime and used as
the queue job ETA. If the target time has already passed today, the job is
scheduled for the same time tomorrow. Leave the field at `0` to disable
scheduled execution (jobs run as soon as possible).

Values outside `[0, 24)` are rejected with a validation error.

### Duplicate-job prevention

An identity key (`exchange_record_job_identity_exact`) is attached to every
queued job, so re-triggering an action for a record that already has a pending
job does not enqueue a duplicate.
