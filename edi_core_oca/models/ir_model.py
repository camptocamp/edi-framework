# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrModel(models.Model):
    _inherit = "ir.model"

    is_edi_generator = fields.Boolean()
    is_edi_input_validator = fields.Boolean()
    is_edi_output_validator = fields.Boolean()
    is_edi_sender = fields.Boolean()
    is_edi_receiver = fields.Boolean()
    is_edi_processor = fields.Boolean()
    is_edi_checker = fields.Boolean()

    def _reflect_model_params(self, model):
        vals = super()._reflect_model_params(model)
        vals["is_edi_generator"] = (
            model._name != "edi.oca.handler.generate"
            and isinstance(model, self.pool["edi.oca.handler.generate"])
        )
        vals["is_edi_input_validator"] = (
            model._name != "edi.oca.handler.input.validate"
            and isinstance(model, self.pool["edi.oca.handler.input.validate"])
        )
        vals["is_edi_output_validator"] = (
            model._name != "edi.oca.handler.output.validate"
            and isinstance(model, self.pool["edi.oca.handler.output.validate"])
        )
        vals["is_edi_sender"] = model._name != "edi.oca.handler.send" and isinstance(
            model, self.pool["edi.oca.handler.send"]
        )
        vals["is_edi_receiver"] = (
            model._name != "edi.oca.handler.receive"
            and isinstance(model, self.pool["edi.oca.handler.receive"])
        )
        vals["is_edi_processor"] = (
            model._name != "edi.oca.handler.process"
            and isinstance(model, self.pool["edi.oca.handler.process"])
        )
        vals["is_edi_checker"] = model._name != "edi.oca.handler.check" and isinstance(
            model, self.pool["edi.oca.handler.check"]
        )
        return vals
