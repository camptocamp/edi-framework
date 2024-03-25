# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import base64

from odoo.addons.edi_oca.tests.common import EDIBackendCommonComponentRegistryTestCase
from odoo.addons.edi_oca.tests.fake_components import FakeInputProcess


class TestEDINotification(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_env()
        cls._build_components(
            cls,
            FakeInputProcess,
        )
        cls._load_module_components(cls, "edi_notification_oca")
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "exchange_file": base64.b64encode(b"1234"),
        }
        cls.record = cls.backend.create_record("test_csv_input", vals)
        cls.group_sale = cls.env.ref("sales_team.group_sale_salesman")
        cls.user_a = cls._create_user(cls, "A")
        cls.user_b = cls._create_user(cls, "B")
        cls.user_c = cls._create_user(cls, "C")

    def setUp(self):
        super().setUp()
        FakeInputProcess.reset_faked()

    def _create_user(self, letter):
        return self.env["res.users"].create(
            {
                "name": "User %s" % letter,
                "login": "user_%s" % letter,
                "groups_id": [(6, 0, [self.group_sale.id])],
            }
        )

    def test_dont_send_notification_on_error(self):
        self.exchange_type_in.send_notification_on_error = False
        self.record.write({"edi_exchange_state": "input_received"})
        self.record._set_file_content("TEST %d" % self.record.id)
        self.record.with_context(
            test_break_process="OOPS! Something went wrong :("
        ).action_exchange_process()
        self.assertRecordValues(
            self.record,
            [
                {
                    "edi_exchange_state": "input_processed_error",
                }
            ],
        )
        self.assertIn("OOPS! Something went wrong :(", self.record.exchange_error)
        # We don't expect any notification
        activity_notification = self.env["mail.activity"].search(
            [("res_model", "=", "edi.exchange.record"), ("res_id", "=", self.record.id)]
        )
        self.assertEqual(len(activity_notification), 0)

    def test_send_notification_on_error_to_group(self):
        self.exchange_type_in.write(
            {
                "send_notification_on_error": True,
                "notification_groups_ids": [(6, 0, [self.group_sale.id])],
            }
        )
        # Remove group on user C to test
        self.user_c.groups_id = None
        self.record.write({"edi_exchange_state": "input_received"})
        self.record._set_file_content("TEST %d" % self.record.id)
        self.record.with_context(
            test_break_process="OOPS! Something went wrong :("
        ).action_exchange_process()
        # Send notification to all users in defined groups when error
        a_noti = self.env["mail.activity"].search(
            [
                ("res_model", "=", "edi.exchange.record"),
                ("res_id", "=", self.record.id),
                ("user_id", "=", self.user_a.id),
            ]
        )
        self.assertEqual(len(a_noti), 1)
        self.assertEqual(
            a_noti.summary,
            f"Error on process of record '{self.record.identifier}'.",
        )
        self.assertIn(
            "OOPS! Something went wrong :(",
            a_noti.note,
        )
        b_noti = self.env["mail.activity"].search(
            [
                ("res_model", "=", "edi.exchange.record"),
                ("res_id", "=", self.record.id),
                ("user_id", "=", self.user_b.id),
            ]
        )
        self.assertEqual(len(b_noti), 1)
        self.assertEqual(
            b_noti.summary,
            f"Error on process of record '{self.record.identifier}'.",
        )
        self.assertIn(
            "OOPS! Something went wrong :(",
            b_noti.note,
        )
        # We don't send notification to user C
        # because C is not belonging to the group_sale_salesman
        c_noti = self.env["mail.activity"].search(
            [
                ("res_model", "=", "edi.exchange.record"),
                ("res_id", "=", self.record.id),
                ("user_id", "=", self.user_c.id),
            ]
        )
        self.assertEqual(len(c_noti), 0)

    def test_send_notification_on_error_to_users(self):
        self.exchange_type_in.write(
            {
                "send_notification_on_error": True,
                "notification_users_ids": [(6, 0, [self.user_c.id])],
            }
        )
        self.record.write({"edi_exchange_state": "input_received"})
        self.record._set_file_content("TEST %d" % self.record.id)
        self.record.with_context(
            test_break_process="OOPS! Something went wrong :("
        ).action_exchange_process()
        # Send notification to all users in defined groups when error
        a_b_noti = self.env["mail.activity"].search(
            [
                ("res_model", "=", "edi.exchange.record"),
                ("res_id", "=", self.record.id),
                "|",
                ("user_id", "=", self.user_a.id),
                ("user_id", "=", self.user_b.id),
            ]
        )
        self.assertEqual(len(a_b_noti), 0)
        c_noti = self.env["mail.activity"].search(
            [
                ("res_model", "=", "edi.exchange.record"),
                ("res_id", "=", self.record.id),
                ("user_id", "=", self.user_c.id),
            ]
        )
        self.assertEqual(len(c_noti), 1)
        self.assertEqual(
            c_noti.summary,
            f"Error on process of record '{self.record.identifier}'.",
        )
        self.assertIn(
            "OOPS! Something went wrong :(",
            c_noti.note,
        )

    def test_send_notification_on_error_to_groups_and_users(self):
        self.exchange_type_in.write(
            {
                "send_notification_on_error": True,
                "notification_groups_ids": [(6, 0, [self.group_sale.id])],
                "notification_users_ids": [(6, 0, [self.user_c.id])],
            }
        )
        # Remove group on user C to test
        self.user_c.groups_id = None
        self.record.write({"edi_exchange_state": "input_received"})
        self.record._set_file_content("TEST %d" % self.record.id)
        self.record.with_context(
            test_break_process="OOPS! Something went wrong :("
        ).action_exchange_process()
        # Send notification to all users in defined groups when error
        a_b_noti = self.env["mail.activity"].search(
            [
                ("res_model", "=", "edi.exchange.record"),
                ("res_id", "=", self.record.id),
                "|",
                ("user_id", "=", self.user_a.id),
                ("user_id", "=", self.user_b.id),
            ]
        )
        self.assertEqual(len(a_b_noti), 2)
        # also send notification to user C
        c_noti = self.env["mail.activity"].search(
            [
                ("res_model", "=", "edi.exchange.record"),
                ("res_id", "=", self.record.id),
                ("user_id", "=", self.user_c.id),
            ]
        )
        self.assertEqual(len(c_noti), 1)
