# Copyright 2023 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
import json
from functools import singledispatch

from odoo import fields


@singledispatch
def convert(obj):
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


@convert.register(datetime.date)
def convert_date(obj):
    return fields.Date.to_string(obj)


@convert.register(datetime.datetime)
def convert_datetime(obj):
    return fields.Datetime.to_string(obj)


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        return convert(obj)
