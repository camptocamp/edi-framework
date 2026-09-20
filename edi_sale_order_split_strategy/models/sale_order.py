# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_order_split_copy_defaults(self):
        res = super()._prepare_order_split_copy_defaults()
        # `origin_exchange_record_id` is `copy=False`: without this, the
        # split-off order would end up w/ no EDI origin at all, even though
        # the lines moved onto it (they are moved, not copied) keep theirs.
        res["origin_exchange_record_id"] = self.origin_exchange_record_id.id
        return res

    def _postprocess_split_to(self, origin_order):
        res = super()._postprocess_split_to(origin_order)
        exchange_record = self.origin_exchange_record_id
        if exchange_record:
            # Keep the new order discoverable from the original EDI exchange
            # record too (e.g. via its "Exchange records" smart button),
            # same as the order it was split from.
            exchange_record._set_related_record(self)
        return res
