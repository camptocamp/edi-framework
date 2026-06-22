This module integrates EDI exchange records with
[Queue Job](https://github.com/OCA/queue), so that the four core exchange
actions — **generate**, **send**, **receive**, and **process** — are dispatched
as background jobs instead of running synchronously.

No need of doing a configuration on it, however, we can specify eta, priority and channel in exchange type.
