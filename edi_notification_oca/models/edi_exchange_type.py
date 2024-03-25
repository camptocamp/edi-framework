# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EDIExchangeType(models.Model):
    _inherit = "edi.exchange.type"

    send_notification_on_error = fields.Boolean(
        help="If an error happens on process, a notification will be sent to all"
        " selected users. If active, please select the specific groups and"
        " specific users in the 'Notifications' page.",
        default=False,
    )
    notification_groups_ids = fields.Many2many(
        comodel_name="res.groups", string="Notification Groups"
    )
    notification_users_ids = fields.Many2many(
        comodel_name="res.users",
        string="Notification Users",
        help="Select users to send notifications to. If 'Notification Groups' "
        "have been selected, notifications will also be sent to users selected in here.",
    )

    @api.onchange("send_notification_on_error")
    def _onchange_send_notification_on_error(self):
        if not self.send_notification_on_error:
            self.notification_groups_ids = None
            self.notification_users_ids = None

    @api.constrains(
        "send_notification_on_error",
        "notification_groups_ids",
        "notification_users_ids",
    )
    def _check_notification_on_error_groups_users(self):
        for rec in self:
            if not rec.send_notification_on_error:
                if rec.notification_groups_ids or rec.notification_users_ids:
                    raise ValidationError(
                        _(
                            "'Send Notification On Error' must be enabled before selecting "
                            "specific groups or specific users to send."
                        )
                    )
