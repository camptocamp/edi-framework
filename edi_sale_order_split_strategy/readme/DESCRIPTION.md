Glue module between `edi_sale_oca` and `sale_order_split_strategy`.

When a sale order is split, the newly created order is a copy of the
original one, and `origin_exchange_record_id` is not copied by default
(it's meant to track the EDI exchange record that originated the record
it's set on). Without this module, the split-off order ends up with no
EDI origin at all, even though the lines moved onto it (they are moved,
not copied) keep their own origin: this breaks EDI state computation on
the new order and makes it impossible to distinguish it from a regular,
non-EDI order.

This module makes sure that, on split:

- the new order keeps the same `origin_exchange_record_id` (and, as a
  consequence, the same `origin_exchange_type_id`) as the order it was
  split from;
- the new order is also linked to that same EDI exchange record as a
  related record, so it can be found from the exchange record's
  "Exchange records" smart button, same as the original order.
