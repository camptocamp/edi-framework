# Copyright 2021 Camptocamp SA
# Copyright 2025 Dixmit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EdiExchangeType(models.Model):
    _inherit = "edi.exchange.type"

    job_channel_id = fields.Many2one(
        comodel_name="queue.job.channel",
    )
    job_priority = fields.Integer()
    eta_time = fields.Float(
        string="Execute at (timezone aware)",
        help="Daily time (HH:MM) at which jobs for this type should be scheduled, "
        "in your local timezone. Leave empty to disable.",
    )
