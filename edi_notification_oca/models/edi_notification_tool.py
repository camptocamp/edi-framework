# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class EDINotificationTool(models.AbstractModel):
    _name = "edi.notification.tool"
    _description = "EDI Notification Tool"

    def on_edi_exchange_error(self, exchange_record):
        exchange_record.ensure_one()
        exc_type = exchange_record.type_id
        activity_type = exc_type.notify_on_process_error_activity_type_id
        groups = exc_type.notify_on_process_error_groups_ids
        group_users_field = "users" if "users" in groups._fields else "user_ids"
        users = (
            groups.mapped(group_users_field)
            | exc_type.notify_on_process_error_users_ids
        )
        for user in users:
            exchange_record.activity_schedule(
                activity_type_id=activity_type.id,
                summary=self.env._(
                    "EDI: Process error on record '%(identifier)s'.",
                    identifier=exchange_record.identifier,
                ),
                note=exchange_record.exchange_error,
                user_id=user.id,
                automated=True,
            )
        return True
