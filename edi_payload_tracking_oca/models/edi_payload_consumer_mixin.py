# Copyright 2026 Camptocamp SA
# @author Akim Juillerat <akim.juillerat@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class EDIPayloadConsumerMixin(models.AbstractModel):
    """Read and write the payload exported for a record."""

    _name = "edi.payload.consumer.mixin"
    _description = "EDI exported payload consumer mixin"

    def edi_get_output_payload(self):
        """Return the payload stored for this record, or an empty dict."""
        self.ensure_one()
        return self.env["edi.payload.output"].get_payload(self)

    def edi_set_output_payload(self, payload):
        """Store `payload` for this record, replacing the previous one."""
        self.ensure_one()
        return self.env["edi.payload.output"].set_payload(self, payload)
