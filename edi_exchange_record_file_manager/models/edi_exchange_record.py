# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class EDIExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    button_open_file_manager_invisible = fields.Boolean(
        compute="_compute_button_open_file_manager_invisible"
    )

    def _can_use_file_manager(self) -> bool:
        """Returns True if the file manager can be used on ``self`` by the current user

        By default, the file manager is available if:
        - the user is allowed to create, read, and update records of the wiz model
        - the record contains a file
        - the file can be updated by the current user (not "frozen")
        - its state is "Error on validation", "Sent and Error" or "Error on Process"
        """
        self.ensure_one()
        has_access = self.env["edi.exchange.record.file.manager"].has_access
        return (
            all(has_access(op) for op in ("create", "read", "write"))
            and bool(self.exchange_file)
            and self.edi_exchange_state in self._get_file_manager_allowed_states()
            and not self.exchange_file_frozen
        )

    @api.model
    def _get_file_manager_allowed_states(self) -> list[str]:
        """Returns the states allowing the file manager wizard to be displayed

        Defaults: "Error on validation", "Sent and Error" and "Error on Process"
        """
        return ["validate_error", "output_sent_and_error", "input_processed_error"]

    @api.depends("exchange_file_frozen", "edi_exchange_state")
    @api.depends_context("uid")
    def _compute_button_open_file_manager_invisible(self):
        """Computes whether the button to open the file manager should be invisible"""
        for rec in self:
            rec.button_open_file_manager_invisible = not rec._can_use_file_manager()

    def button_open_file_manager(self):
        """Prepares the file manager wizard and opens it"""
        self.ensure_one()
        self._check_can_use_file_manager()
        wizard = self.env["edi.exchange.record.file.manager"]
        return wizard.create([{"exchange_record_id": self.id}]).open()

    def _check_can_use_file_manager(self):
        """Raise if the file of the exchange cannot be managed from the wizard."""
        self.ensure_one()
        if not self._can_use_file_manager():
            raise UserError(self.env._("The file manager cannot be used now"))

    def _prepare_file_manager_wizard_values(self) -> api.ValuesType:
        """Prepares the values to create the file manager wizard"""
        self.ensure_one()
        return {"exchange_record_id": self.id}
