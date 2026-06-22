# Copyright 2021 Camptocamp SA
# Copyright 2025 Dixmit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EdiExchangeType(models.Model):
    _inherit = "edi.exchange.type"

    job_channel_id = fields.Many2one(
        comodel_name="queue.job.channel",
    )
    job_priority = fields.Integer()
    eta_time = fields.Float(
        string="Execute at (timezone aware)",
        help="Hour of the day (decimal) at which jobs for this type should be "
        "scheduled, in your local timezone. Use decimal fractions for minutes "
        "(e.g. 22.5 = 22:30). Must be in the range [0, 24). "
        "Leave empty (0) to disable.",
    )

    @api.constrains("eta_time")
    def _check_eta_time(self):
        for rec in self:
            if rec.eta_time and not (0 <= rec.eta_time < 24):
                raise ValidationError(
                    self.env._(
                        "'%(name)s': Execute at time %(value).2f is not a valid "
                        "24-hour value. Enter a decimal hour in the range [0, 24) "
                        "(e.g. 22.5 = 22:30).",
                        name=rec.display_name,
                        value=rec.eta_time,
                    )
                )
