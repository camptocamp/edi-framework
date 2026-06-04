# Usage

## Functional flow

1. An EDI exchange reaches an error state.
2. The module evaluates whether the state is configured to trigger activities.
3. Optional model filtering is applied.
4. Assignee and deduplication marker are computed.
5. If no existing activity matches the deduplication marker, a new activity is created.
6. A message is posted with a link to the exchange record.

## Typical usage pattern in integration modules

- Reuse the helper methods provided on `edi.exchange.record` from your exchange processing code.
- Add integration-specific XML data and presets in the corresponding integration module.
