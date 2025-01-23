# Copyright 2025 Camptocamp SA
# @author Italo LOPES <italo.lopes@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

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
        values = {
            "exchange_record": exchange_record,
            "record": exchange_record.record,
            "backend": exchange_record.backend_id,
            "template": self,
            "render_edi_template": self._render_template,
            "get_info_provider": self._get_info_provider,
            "info": {},
        }
        values.update(kw)
        values.update(self._time_utils())
        return self._evaluate_code_snippet(**values)

    def _post_process_json_output(self, output):
        """Post-process JSON output."""
        return json.dumps(output)
