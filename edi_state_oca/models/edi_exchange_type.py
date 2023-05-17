# Copyright 2023 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EDIExchangeType(models.Model):

    _inherit = "edi.exchange.type"

    state_workflow_ids = fields.Many2many(
        string="Enabled state workflows",
        comodel_name="edi.state.workflow",
        help="Allowed workflows that can be used by this type of exchanges.",
    )
