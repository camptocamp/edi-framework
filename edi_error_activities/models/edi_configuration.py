# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EDIConfiguration(models.Model):
    _inherit = "edi.configuration"

    error_activity_enabled = fields.Boolean(
        string="Create Activity on EDI Error",
        default=False,
        help=(
            "Enable automatic activity creation when an EDI exchange ends in one of "
            "the configured error states."
        ),
    )
    error_activity_target_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Error Activity Target Model",
        domain=[("is_mail_activity", "=", True)],
        help=(
            "Optional. Only create activities when the exchange is linked to records "
            "of this model. Leave empty to allow any related model. The target "
            "model must support activities (mail.activity.mixin)."
        ),
    )
    error_activity_user_strategy = fields.Selection(
        selection=[
            ("business_record_creator", "Creator of Related Business Record"),
            ("triggering_user", "User Who Triggered the EDI Event"),
            ("configured_user", "Specific User Configured Below"),
        ],
        string="Error Activity Assignee Strategy",
        default="business_record_creator",
        required=True,
        help=(
            "Choose who receives the activity: record creator, user who triggered "
            "the event, or a specific configured user."
        ),
    )
    error_activity_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Error Activity User",
        help=(
            "Used when assignee strategy is 'Specific User Configured Below'. "
            "Ignored for other strategies."
        ),
    )
    error_activity_type_id = fields.Many2one(
        comodel_name="mail.activity.type",
        string="Error Activity Type",
        help="Activity type to create. Defaults to TODO when left empty.",
    )
    error_activity_dedup_key_template = fields.Char(
        default="[exchange:{exchange.id}]",
        help=(
            "Template used to avoid duplicate activities for the same exchange. "
            "Available placeholders: {exchange}, {record}, {conf}."
        ),
    )
    error_activity_states = fields.Char(
        string="Error States",
        default="output_error_on_send,output_sent_and_error",
        help=(
            "Comma-separated exchange states that trigger activity creation. "
            "Example: output_error_on_send,output_sent_and_error"
        ),
    )

    @api.constrains("error_activity_user_strategy", "error_activity_user_id")
    def _check_error_activity_user_strategy(self):
        for conf in self:
            if (
                conf.error_activity_user_strategy == "configured_user"
                and not conf.error_activity_user_id
            ):
                raise ValidationError(
                    self.env._(
                        "Error Activity User is required when assignee strategy is "
                        "'%(strategy)s'.",
                        strategy="Specific User Configured Below",
                    )
                )

    @api.constrains("error_activity_states")
    def _check_error_activity_states(self):
        exchange_model = self.env["edi.exchange.record"]
        state_field = exchange_model._fields.get("edi_exchange_state")
        if not state_field:
            return

        selection = (
            state_field.selection(exchange_model)
            if callable(state_field.selection)
            else state_field.selection
        )
        allowed_states = {state for state, _label in selection}

        for conf in self:
            states = {
                state.strip()
                for state in (conf.error_activity_states or "").split(",")
                if state.strip()
            }
            invalid_states = sorted(states - allowed_states)
            if invalid_states:
                raise ValidationError(
                    self.env._(
                        "Unknown EDI exchange state(s): %(states)s",
                        states=", ".join(invalid_states),
                    )
                )
