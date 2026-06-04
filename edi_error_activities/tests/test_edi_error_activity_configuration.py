# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo.addons.edi_core_oca.tests.common import EDIBackendCommonTestCase


class TestEdiErrorActivityConfiguration(EDIBackendCommonTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, edi__skip_quick_exec=True))
        cls.config_trigger = cls.env["edi.configuration.trigger"].search(
            [("code", "=", "test_edi_error_activities_trigger")],
            limit=1,
        ) or cls.env["edi.configuration.trigger"].create(
            {
                "name": "Test Config Trigger",
                "code": "test_edi_error_activities_trigger",
            }
        )
        cls.activity_type = cls.env.ref("mail.mail_activity_data_todo")
        cls.user = cls.env.ref("base.user_admin")
        cls.ir_model_users = cls.env["ir.model"].search(
            [("model", "=", "res.users")],
            limit=1,
        )

    def _base_vals(self, **overrides):
        vals = {
            "name": "Test Config",
            "trigger_id": self.config_trigger.id,
            "type_id": False,
            "backend_id": False,
            "model_id": False,
            "error_activity_enabled": True,
            "error_activity_type_id": self.activity_type.id,
            "error_activity_user_strategy": "configured_user",
            "error_activity_user_id": self.user.id,
        }
        vals.update(overrides)
        return vals

    def test_requires_user_for_configured_user_assignee(self):
        with self.assertRaises(ValidationError):
            self.env["edi.configuration"].create(
                self._base_vals(error_activity_user_id=False)
            )

    def test_invalid_error_activity_state_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["edi.configuration"].create(
                self._base_vals(error_activity_states="to_send,invalid")
            )

    def _make_conf(self, **overrides):
        vals = {
            "name": "Error activity config",
            "trigger_id": self.config_trigger.id,
            "type_id": False,
            "backend_id": False,
            "model_id": False,
            "error_activity_enabled": True,
            "error_activity_type_id": False,
            "error_activity_user_strategy": "configured_user",
            "error_activity_user_id": self.user.id,
            "error_activity_states": "output_error_on_send",
            "error_activity_target_model_id": False,
            "error_activity_dedup_key_template": "[exchange:{exchange.id}]",
        }
        vals.update(overrides)
        return self.env["edi.configuration"].create(vals)

    def _make_exchange(self, **overrides):
        partner = self.env["res.partner"].create(
            {"name": "Error Activity Target Partner"}
        )
        vals = {
            "model": partner._name,
            "res_id": partner.id,
            "edi_exchange_state": "output_error_on_send",
            "exchange_error": "Boom <tag>",
        }
        vals.update(overrides)
        return self.backend.create_record(self.exchange_type_out.code, vals)

    def test_helpers_default_states_and_activity_type(self):
        conf = self._make_conf(error_activity_states="", error_activity_type_id=False)
        exchange_model = self.env["edi.exchange.record"]

        self.assertEqual(
            exchange_model._edi_error_activity_states(conf),
            set(exchange_model._DEFAULT_ERROR_STATES),
        )
        self.assertEqual(
            exchange_model._edi_error_activity_type(conf),
            self.activity_type,
        )

    def test_helpers_marker_fallback_and_assignee(self):
        exchange = self._make_exchange()
        related_record = exchange.record

        conf_bad_template = self._make_conf(
            error_activity_dedup_key_template="{bad",
            error_activity_user_strategy="triggering_user",
            error_activity_user_id=False,
        )
        marker = exchange._edi_error_activity_marker(
            conf_bad_template,
            exchange,
            related_record,
        )
        self.assertEqual(marker, f"[exchange:{exchange.id}]")
        self.assertEqual(
            exchange._edi_error_activity_assignee(
                conf_bad_template, related_record, self.user
            ),
            self.user,
        )

        conf_creator = self._make_conf(
            error_activity_user_strategy="business_record_creator",
            error_activity_user_id=False,
        )
        self.assertEqual(
            exchange._edi_error_activity_assignee(conf_creator, related_record, False),
            related_record.create_uid,
        )

    def test_schedule_activity_is_created_and_deduplicated(self):
        conf = self._make_conf()
        exchange = self._make_exchange()
        related_record = exchange.record

        exchange._edi_schedule_error_activity_from_conf(conf, user=self.user)
        activity_domain = [
            ("res_model", "=", related_record._name),
            ("res_id", "=", related_record.id),
            ("activity_type_id", "=", self.activity_type.id),
        ]
        activities = self.env["mail.activity"].search(activity_domain)
        self.assertEqual(len(activities), 1)
        self.assertIn("&lt;tag&gt;", activities.note)

        exchange._edi_schedule_error_activity_from_conf(conf, user=self.user)
        activities = self.env["mail.activity"].search(activity_domain)
        self.assertEqual(len(activities), 1)

    def test_schedule_skips_on_state_and_model_guards(self):
        exchange = self._make_exchange()

        conf_wrong_state = self._make_conf(error_activity_states="output_sent")
        exchange._edi_schedule_error_activity_from_conf(
            conf_wrong_state, user=self.user
        )

        related_record = exchange.record
        activity_domain = [
            ("res_model", "=", related_record._name),
            ("res_id", "=", related_record.id),
        ]
        self.assertFalse(self.env["mail.activity"].search_count(activity_domain))

        conf_wrong_model = self._make_conf(
            error_activity_target_model_id=self.ir_model_users.id,
        )
        exchange._edi_schedule_error_activity_from_conf(
            conf_wrong_model, user=self.user
        )
        self.assertFalse(self.env["mail.activity"].search_count(activity_domain))

    def test_schedule_skips_when_related_record_has_no_activity_schedule(self):
        ir_model = self.env["ir.model"].search([], limit=1)
        exchange = self._make_exchange(model="ir.model", res_id=ir_model.id)
        conf = self._make_conf()

        exchange._edi_schedule_error_activity_from_conf(conf, user=self.user)

        self.assertFalse(
            self.env["mail.activity"].search_count(
                [
                    ("res_model", "=", "ir.model"),
                    ("res_id", "=", ir_model.id),
                ]
            )
        )
