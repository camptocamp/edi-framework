# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class QueueJob(models.Model):
    _inherit = "queue.job"

    def write(self, vals):
        result = super().write(vals)
        if vals.get("state") == "failed":
            self._mark_related_edi_exchanges_failed()
        return result

    def _mark_related_edi_exchanges_failed(self):
        """Propagate terminal EDI job failures to their exchange records."""
        supported_methods = {
            "action_exchange_process",
            "action_exchange_receive",
            "action_exchange_send",
        }
        jobs = self.filtered(
            lambda job: job.model_name == "edi.exchange.record"
            and job.method_name in supported_methods
        )
        for job in jobs:
            job.records.sudo()._mark_failed_from_queue_job(job)
