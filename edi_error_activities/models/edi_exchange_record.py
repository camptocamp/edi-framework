# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.fields import Domain


class EDIExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    _DEFAULT_ERROR_STATES = ("output_error_on_send", "output_sent_and_error")
    _DEFAULT_DEDUP_KEY_TEMPLATE = "[exchange:{exchange.id}]"

    def _edi_error_activity_states(self, conf):
        """Return normalized state filters configured for error activities."""
        raw_states = conf.error_activity_states or ""
        states = {state.strip() for state in raw_states.split(",") if state.strip()}
        return states or set(self._DEFAULT_ERROR_STATES)

    def _edi_error_activity_marker(self, conf, exchange, record):
        """
        Build deduplication marker used to avoid duplicate activities.
        The marker identifies one exchange activity
        so repeated executions do not create duplicates.
        """
        template = (
            conf.error_activity_dedup_key_template or self._DEFAULT_DEDUP_KEY_TEMPLATE
        )
        try:
            return template.format(exchange=exchange, record=record, conf=conf)
        except Exception:
            return f"[exchange:{exchange.id}]"

    def _edi_error_activity_assignee(self, conf, record, user):
        """Resolve assignee according to configuration strategy."""
        strategy = conf.error_activity_user_strategy
        if strategy == "configured_user" and conf.error_activity_user_id:
            return conf.error_activity_user_id
        if strategy == "triggering_user" and user:
            return user
        return record.create_uid or user or self.env.user

    def _edi_error_activity_target_model(self, conf):
        return conf.error_activity_target_model_id.model or False

    def _edi_error_activity_type(self, conf):
        todo = self.env.ref("mail.mail_activity_data_todo")
        return conf.error_activity_type_id or todo

    def _edi_activity_already_exists(self, record, activity_type, marker):
        return bool(
            self.env["mail.activity"].search(
                Domain(
                    [
                        ("res_model", "=", record._name),
                        ("res_id", "=", record.id),
                        ("activity_type_id", "=", activity_type.id),
                        ("note", "ilike", marker),
                    ]
                ),
                limit=1,
            )
        )

    def _edi_error_activity_note(self, exchange, marker):
        import html

        exchange_link = (
            f"/web#id={exchange.id}&model=edi.exchange.record&view_type=form"
        )
        error = (
            html.escape(exchange.exchange_error) if exchange.exchange_error else "n/a"
        )
        note = (
            "<p>EDI transmission failed for exchange "
            f"<b>{exchange.identifier}</b>.</p>"
            f"<p>Error: {error}</p>"
            f"<p><a href='{exchange_link}'>Open exchange record</a></p>"
            f"<p>{marker}</p>"
        )
        return note, exchange_link

    def _edi_schedule_activity_for_exchange(self, exchange, conf, user, activity_type):
        target_model = self._edi_error_activity_target_model(conf)
        related_record = exchange.record
        if not related_record:
            return
        if target_model and related_record._name != target_model:
            return
        if not hasattr(related_record, "activity_schedule"):
            return

        assignee = self._edi_error_activity_assignee(conf, related_record, user)
        marker = self._edi_error_activity_marker(conf, exchange, related_record)
        if self._edi_activity_already_exists(related_record, activity_type, marker):
            return

        note, exchange_link = self._edi_error_activity_note(exchange, marker)
        related_record.activity_schedule(
            activity_type_id=activity_type.id,
            user_id=assignee.id,
            summary=self.env._("EDI transmission error"),
            note=note,
        )
        if hasattr(related_record, "message_post"):
            related_record.message_post(
                body=self.env._(
                    "EDI transmission failed for exchange %(identifier)s. "
                    "<a href='%(link)s'>Open exchange record</a>",
                    identifier=exchange.identifier,
                    link=exchange_link,
                )
            )

    def _edi_schedule_error_activity_from_conf(self, conf, user=None):
        """Schedule deduplicated activities for exchanges matching configured states."""
        if not conf or not conf.error_activity_enabled:
            return

        activity_type = self._edi_error_activity_type(conf)
        states = self._edi_error_activity_states(conf)
        exchanges = self.filtered(lambda rec: rec.edi_exchange_state in states)
        for exchange in exchanges:
            self._edi_schedule_activity_for_exchange(
                exchange,
                conf,
                user,
                activity_type,
            )
