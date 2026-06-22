## Automatic job dispatch

All `action_exchange_*` methods on `edi.exchange.record` are patched at startup
to run via `queue.job`. No per-record configuration is required; the integration
is active for every exchange type as soon as the module is installed.

## Per-type job configuration

Each **Exchange Type** gains a *Queue* tab with three optional settings:

| Field | Purpose |
|---|---|
| **Job channel** | Route jobs to a specific channel (e.g. `root.edi.high`). |
| **Job priority** | Integer priority passed to the queue job (lower = higher priority). |
| **Enable ETA Scheduling** (`eta_enabled`) | Toggle to activate daily job accumulation (see below). |
| **Execute at** (`eta_time`) | Daily time at which accumulated jobs are released (visible only when `eta_enabled`). |

## Accumulating jobs until a fixed daily time

Enabling **ETA Scheduling** on an exchange type causes every job created for
that type to be **held in the queue** until the configured time of day, rather
than being processed immediately. All jobs that arrive during the day accumulate
and are released together at that moment.

**Typical use cases:**

- A trading partner's receiving system only processes incoming files at a
  specific nightly window (e.g. 22:00).
- Resource-intensive EDI operations (large exports, heavy transformations) should
  be deferred to off-peak hours to avoid competing with daytime workloads.
- Operational preference to review and send a batch of documents at a predictable
  daily time instead of dispatching them one by one in real time.

The **Execute at** field accepts a decimal hour in `[0, 24[` in the **current
user's timezone**:

| Value | Meaning |
|---|---|
| `0.0` | 00:00 midnight |
| `6.25` | 06:15 |
| `22.0` | 22:00 |
| `22.5` | 22:30 |

At runtime the value is converted to the next matching UTC datetime and set as
the queue job ETA. If the target time has already passed today, the job is
automatically scheduled for the same time tomorrow. Values outside `[0, 24[` are
rejected with a validation error.

When **Enable ETA Scheduling** is off, jobs are dispatched immediately as
usual.

## Duplicate-job prevention

An identity key (`exchange_record_job_identity_exact`) is attached to every
queued job, so re-triggering an action for a record that already has a pending
job does not enqueue a duplicate.
