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
        - the user has access to the file manager (see ``_has_file_manager_access()``)
        - the record contains a file
        - the record file can be updated (not "frozen")
        - the record state allows wizard use (see ``_state_allows_file_manager_use()``)
        """
        self.ensure_one()
        return (
            self._has_file_manager_access()
            and bool(self.exchange_file)
            and not self.exchange_file_frozen
            and self._state_allows_file_manager_use()
        )

    @api.model
    def _has_file_manager_access(self) -> bool:
        """Checks whether the user has operational access to the file manager model

        If method ``_has_file_manager_access_get_operations_to_check()`` returns an
        empty list of operations to check, then it is assumed that the current user has
        full access.

        Hook method, can be overridden
        """
        if operations := self._has_file_manager_access_get_operations_to_check():
            model = self.env["edi.exchange.record.file.manager"]
            return all(model.has_access(o) for o in operations)
        return True

    @api.model
    def _has_file_manager_access_get_operations_to_check(self) -> list[str]:
        """Returns the operations the user should be able to perform on the file manager

        Defaults: ["create", "read", "write"]
        We ignore "unlink" because ``TransientModel`` records are usually deleted via
        the ``@api.autovacuum()`` cron, which is executed by an admin, so it doesn't
        make sense to check it.

        If the returned list is empty, it is assumed that the current user is able to
        perform all operations (the same as if ``self.env.su == True``).

        Hook method, can be overridden
        """
        return ["create", "read", "write"]

    def _state_allows_file_manager_use(self) -> bool:
        """Checks whether the record state grants access to the file manager

        If method ``_get_file_manager_allowed_states()`` returns an empty list of
        states, then it is assumed that the current state allows it.

        Hook method, can be overridden
        """
        if states := self._get_file_manager_allowed_states():
            return self.edi_exchange_state in states
        return True

    @api.model
    def _get_file_manager_allowed_states(self) -> list[str]:
        """Returns states allowing the file manager wizard to be accessed by the user

        If the returned list is empty, it is assumed that the current state allows it.

        Defaults: "Error on validation", "Sent and Error" and "Error on Process"
        """
        return ["validate_error", "output_sent_and_error", "input_processed_error"]

    @api.depends("exchange_file_frozen", "edi_exchange_state")
    @api.depends_context("uid")
    def _compute_button_open_file_manager_invisible(self):
        """Computes whether the button to open the file manager should be invisible"""
        for rec in self:
            rec.button_open_file_manager_invisible = not rec._can_use_file_manager()

    def button_open_file_manager(self) -> dict:
        """Prepares the file manager wizard and opens it"""
        self.ensure_one()
        self._check_can_use_file_manager()
        return self._create_file_manager_wizard().open()

    def _check_can_use_file_manager(self):
        """Raise if the file of the exchange cannot be managed from the wizard."""
        self.ensure_one()
        if not self._can_use_file_manager():
            raise UserError(self.env._("The file manager cannot be used now"))

    def _create_file_manager_wizard(self):
        """Creates the file manager wizard"""
        self.ensure_one()
        wizard = self.env["edi.exchange.record.file.manager"]
        return wizard.create([self._prepare_file_manager_wizard_values()])

    def _prepare_file_manager_wizard_values(self) -> api.ValuesType:
        """Prepares the values to create the file manager wizard"""
        self.ensure_one()
        return {"exchange_record_id": self.id}
