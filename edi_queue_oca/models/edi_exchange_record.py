# Copyright 2021 Camptocamp SA
# Copyright 2025 Dixmit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import functools
from ast import literal_eval

from odoo import fields, models

from ..utils import exchange_record_job_identity_exact


class EdiExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    related_queue_jobs_count = fields.Integer(
        compute="_compute_related_queue_jobs_count"
    )

    def _register_hook(self):
        for function in [
            "action_exchange_send",
            "action_exchange_receive",
            "action_exchange_process",
            "action_exchange_generate",
        ]:
            patched = self._patch_job_auto_delay(function)
            setattr(
                type(self),
                function,
                functools.update_wrapper(
                    patched,
                    getattr(type(self), function),
                ),
            )
        return super()._register_hook()

    def action_exchange_send_job_options(self):
        return {"priority": 0}

    def _job_delay_params(self):
        params = {}
        exchange_type = self.type_id.sudo()
        channel = exchange_type.job_channel_id
        if channel:
            params["channel"] = channel.complete_name
        priority = exchange_type.job_priority
        if priority:
            params["priority"] = priority
        if exchange_type.job_eta_enabled and (eta := exchange_type._get_job_eta()):
            params["eta"] = eta
        # Avoid generating the same job for the same record if existing
        params["identity_key"] = exchange_record_job_identity_exact
        return params

    def with_delay(self, **kw):
        params = self._job_delay_params()
        params.update(kw)
        return super().with_delay(**params)

    def delayable(self, **kw):
        params = self._job_delay_params()
        params.update(kw)
        return super().delayable(**params)

    def _job_retry_params(self):
        return {}

    def _mark_failed_from_queue_job(self, job):
        """Set the EDI error matching a terminal queue job failure.

        :param job: failed ``queue.job`` record
        """
        failure_mapping = {
            "action_exchange_process": ("input_processed_error", "process_ko"),
            "action_exchange_receive": ("input_receive_error", "receive_ko"),
            "action_exchange_send": ("output_error_on_send", "send_ko"),
        }
        failure = failure_mapping.get(job.method_name)
        if not failure:
            return
        state, message_key = failure
        for record in self:
            state_changed = record.edi_exchange_state != state
            record.write(
                {
                    "edi_exchange_state": state,
                    "exchange_error": job.exc_message,
                    "exchange_error_traceback": job.exc_info,
                    "exchanged_on": fields.Datetime.now(),
                }
            )
            if state_changed:
                record._notify_error(message_key)

    def _compute_related_queue_jobs_count(self):
        for rec in self:
            # TODO: We should refactor the object field on queue_job to use jsonb field
            # so that we can search directly into it.
            rec.related_queue_jobs_count = rec.env["queue.job"].search_count(
                [("func_string", "like", str(rec))]
            )

    def action_view_related_queue_jobs(self):
        self.ensure_one()
        xmlid = "queue_job.action_queue_job"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        # Searching based on task name:
        # Ex: `edi.exchange.record(1,).action_exchange_send()`
        # TODO: We should refactor the object field on queue_job to use jsonb field
        # so that we can search directly into it.
        action["domain"] = [("func_string", "like", str(self))]
        # Purge default search filters from ctx to avoid hiding records
        ctx = action.get("context", {})
        if isinstance(ctx, str):
            ctx = literal_eval(ctx)
        # Update the current contexts
        ctx.update(self.env.context)
        action["context"] = {
            k: v for k, v in ctx.items() if not k.startswith("search_default_")
        }
        # Drop ID otherwise the context will be loaded from the action's record
        action.pop("id")
        return action

    def action_exchange_generate_send_chained(self):
        job1 = self.delayable().action_exchange_generate()
        # Chain send job.
        # Raise prio to max to send the record out as fast as possible.
        job1.on_done(self.delayable(priority=0).action_exchange_send())
        job1.delay()
