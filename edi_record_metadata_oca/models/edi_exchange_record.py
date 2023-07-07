# Copyright 2023 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
import json
from functools import singledispatch

from odoo import api, fields, models

from odoo.addons.base_sparse_field.models.fields import Serialized


@singledispatch
def sanitize(value):
    return value


@sanitize.register(datetime.date)
def sanitize_date(value):
    return fields.Date.to_string(value)


@sanitize.register(datetime.datetime)
def sanitize_datetime(value):
    return fields.Datetime.to_string(value)


class EDIExchangeRecord(models.Model):

    _inherit = "edi.exchange.record"

    metadata = Serialized(
        help="JSON-like metadata used for technical purposes.",
        default={},
    )
    metadata_display = fields.Text(
        compute="_compute_metadata_display",
        help="Enable debug mode to be able to inspect data.",
    )

    @api.depends("metadata")
    def _compute_metadata_display(self):
        for rec in self:
            rec.metadata_display = json.dumps(rec.metadata, sort_keys=True, indent=4)

    def set_metadata(self, data):
        self._sanitize_metadata(data)
        self.metadata = data

    # TODO: add tests
    def _sanitize_metadata(self, data):
        # ATM there's no control over the encoder of Serialized field.
        # Hence, we must make sure all values are json ready (eg: no datetime obj)
        for k, v in data.items():
            data[k] = sanitize(v)

    def get_metadata(self):
        return self.metadata
