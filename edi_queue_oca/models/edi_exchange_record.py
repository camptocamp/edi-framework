# Copyright 2021 Camptocamp SA
# Copyright 2025 Dixmit
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import functools
from ast import literal_eval
from datetime import timedelta

import pytz

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

    def _eta_float_to_utc(self, eta_time):
        """Convert a decimal-hour ETA to the next occurrence as a naive UTC datetime.

        ``eta_time`` is a float in [0, 24) where the fractional part represents
        minutes (e.g. 22.5 → 22:30). The target is expressed in the current
        user's timezone and rolled forward by one day when the time has already
        passed today.

        Returns a naive UTC datetime suitable for ``queue.job`` ``eta`` param.
        """
        hours, minutes = divmod(round(eta_time * 60), 60)
        user_tz = pytz.timezone(self.env.user.tz or "UTC")
        utc_tz = pytz.UTC
        now_utc = fields.Datetime.now().replace(tzinfo=utc_tz)
        now_user = now_utc.astimezone(user_tz)
        target_user = now_user.replace(
            hour=hours, minute=minutes, second=0, microsecond=0
        )
        if target_user <= now_user:
            target_user += timedelta(days=1)
        return target_user.astimezone(utc_tz).replace(tzinfo=None)

    def _job_delay_params(self):
        params = {}
        exchange_type = self.type_id.sudo()
        channel = exchange_type.job_channel_id
        if channel:
            params["channel"] = channel.complete_name
        priority = exchange_type.job_priority
        if priority:
            params["priority"] = priority
        eta_time = exchange_type.eta_time
        if eta_time:
            params["eta"] = self._eta_float_to_utc(eta_time)
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
