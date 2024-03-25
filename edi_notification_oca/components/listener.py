# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _

from odoo.addons.component.core import Component


class EdiNotificationListener(Component):
    _name = "edi.notification.component.listener"
    _inherit = "base.event.listener"

    def on_edi_exchange_error(self, record):
        exc_type = record.type_id
        send_notification_on_error = exc_type.send_notification_on_error
        if not send_notification_on_error:
            return True
        if not exc_type.notification_groups_ids and not exc_type.notification_users_ids:
            return True
        users = self.env["res.users"]
        if exc_type.notification_groups_ids:
            for group in exc_type.notification_groups_ids:
                users |= group.users
        if exc_type.notification_users_ids:
            users |= exc_type.notification_users_ids
        # Send notification to defined users
        for user in users:
            record.activity_schedule(
                "edi_notification_oca.mail_activity_failed_exchange_record_warning",
                summary=_("Error on process of record '%s'.", record.identifier),
                note=record.exchange_error,
                user_id=user.id,
            )
        return True
