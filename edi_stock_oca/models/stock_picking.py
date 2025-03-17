# Copyright 2022 OCA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "edi.exchange.consumer.mixin"]

    edi_disable_auto = fields.Boolean(
        compute="_compute_edi_disable_auto", store=True, readonly=True
    )

    @api.depends("state")
    def _compute_edi_disable_auto(self):
        for record in self:
            record.edi_disable_auto = record.state in [
                "draft",
                "waiting",
                "confirmed",
                "assigned",
            ]

    def action_confirm(self):
        result = super().action_confirm()
        if self:
            self._event("on_confirm_picking").notify(self)
        return result

    def _action_done(self):
        result = super()._action_done()
        if self:
            self._event("on_validate_picking").notify(self)
        return result

    def action_cancel(self):
        result = super().action_cancel()
        if self:
            self._event("on_cancel_picking").notify(self)
        return result
