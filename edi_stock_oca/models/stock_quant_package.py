# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockQuantPackageg(models.Model):
    _name = "stock.quant.package"
    _inherit = ["stock.quant.package", "edi.exchange.consumer.mixin"]
