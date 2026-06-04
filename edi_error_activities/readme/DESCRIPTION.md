# Description

This module provides generic, configurable error-activity handling for EDI exchanges.

It extends `edi.configuration` with options to control:

- whether activities are created when exchanges fail,
- which exchange states are considered errors,
- optional filtering by target model,
- assignee strategy (including optional fixed user),
- activity type,
- deduplication marker template.

It extends `edi.exchange.record` with reusable helpers that:

- evaluate whether an exchange state should trigger an activity,
- compute assignee and deduplication marker values,
- schedule deduplicated activities,
- post a message including a link to the exchange record.

This module is backend-agnostic and can be reused by any EDI integration.
Business-specific configuration records and snippets should be implemented in integration modules.
