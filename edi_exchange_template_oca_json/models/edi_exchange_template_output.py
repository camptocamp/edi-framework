# Copyright 2025 Camptocamp SA
# @author Italo LOPES <italo.lopes@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class EDIExchangeOutputTemplate(models.Model):
    _inherit = "edi.exchange.template.output"

    generator = fields.Selection(
        selection_add=[("json", "JSON")],
        ondelete={"json": "set default"},
    )

    def _generate_json(self, exchange_record, **kw):
        """Generate JSON output."""
        result = self._render_json_values(exchange_record, **kw)
        return result

    def _post_process_output(self, output):
        result = super()._post_process_output(output)
        if self.generator == "json":
            result = self._post_process_json_output(result)
        return result

    def _render_json_values(self, exchange_record, **kw):
        """Render JSON values."""
        parser = self._get_json_parser(exchange_record)
        result = exchange_record.record.jsonify(parser=parser)
        return result

    def _get_json_parser(self, exchange_record):
        """Retrieve parser to use for JSON generation."""
        json_parser = self._evaluate_code_snippet()
        if not json_parser:
            json_parser = ["display_name"]
        return json_parser

    def _post_process_json_output(self, output):
        """Post-process JSON output."""
        return str(output)
