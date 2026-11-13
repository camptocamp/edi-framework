This module is meant for developers. Inherit the mixin on the model whose
records are exported:

``` python
class ProductProduct(models.Model):
    _inherit = ["product.product", "edi.payload.consumer.mixin"]
```

Then, in the handlers of the exchange:

- `record.get_exported_payload()` returns the payload stored for the record,
  or an empty dict if nothing was exported yet;
- `record.set_exported_payload(payload)` replaces the stored payload.

To keep everything ever sent, merge the sent payload into the stored one:

``` python
from odoo.addons.edi_payload_tracking_oca.utils import data_merge

stored = record.get_exported_payload()
record.set_exported_payload(data_merge(stored.copy(), sent_payload))
```

When two transactions export the same record for the first time
concurrently, the second one fails on the unique constraint. With
`edi_queue_oca`, `edi_payload_tracking_queue_oca` is installed automatically
and turns this into a retry of the job, which then merges its payload on top
of the first one.
