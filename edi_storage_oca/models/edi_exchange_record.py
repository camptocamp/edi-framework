# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EDIExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    move_file_after_processing = fields.Boolean(
        string="Move file after processing", default=True
    )
