# Copyright 2023
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class AccountMoveEdifactListener(Component):
    _name = "account.move.event.listener.edifact"
    _inherit = "base.event.listener"
    _apply_on = ["account.move"]

    def on_post_account_move(self, move):
        edifact_backend = self.env.ref("edi_edifact_oca.edi_backend_type_edifact")
        if (
            not move.partner_id
            or not move.partner_id.edi_account_move_exchange_type_id
            or not move.partner_id.edi_account_move_exchange_type_id.direction
            == "output"
            or not move.partner_id.edi_account_move_exchange_type_id.backend_type_id
            == edifact_backend
        ):
            return None
        exchange_type = move.partner_id.edi_account_move_exchange_type_id
        record = exchange_type.backend_id.create_record(
            exchange_type.code, self._storage_new_exchange_record_vals()
        )
        # Set related record
        record._set_related_record(move)
        _logger.info(
            "Exchange record for customer invoice %s was created: %s",
            move.name,
            record.identifier,
        )

    def _storage_new_exchange_record_vals(self):
        return {"edi_exchange_state": "new"}
