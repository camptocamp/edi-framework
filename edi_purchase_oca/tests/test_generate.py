# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.tests.common import TransactionComponentRegistryCase
from odoo.addons.edi_component_oca.tests.fake_components import (
    FakeOutputGenerator,
    FakeOutputSender,
)

from .common import OrderMixin, PurchaseEDIBackendTestMixin


class Generator(FakeOutputGenerator):
    _backend_type = "purchase_demo"
    _exchange_type = "demo_PurchaseOrder_out"


class Sender(FakeOutputSender):
    _backend_type = "purchase_demo"
    _exchange_type = "demo_PurchaseOrder_out"


class TestProcessComponent(
    TransactionComponentRegistryCase, PurchaseEDIBackendTestMixin, OrderMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registry(cls)
        cls._setup_env()
        cls._setup_records()
        cls.exc_type = cls._create_exchange_type(
            name="Demo Purchase Order out",
            code="demo_PurchaseOrder_out",
            direction="output",
            exchange_filename_pattern="{record_name}-{type.code}-{dt}",
            exchange_file_ext="xml",
        )
        model = cls.env.ref("edi_component_oca.model_edi_oca_component_handler")
        cls.exc_type.generate_model_id = model
        cls.exc_type.send_model_id = model
        cls.exc_type.process_model_id = model
        cls.exc_type.receive_model_id = model
        cls.edi_conf_confirmed = cls.env["edi.configuration"].create(
            {
                "name": "Demo Purchase Order - order confirmed",
                "type_id": cls.exc_type.id,
                "backend_id": cls.backend.id,
                "model_id": cls.env["ir.model"]._get_id("purchase.order"),
                "trigger_id": cls.env.ref(
                    "edi_purchase_oca.edi_conf_trigger_purchase_order_state_change"
                ).id,
                "snippet_do": (
                    "if record.state == 'purchase':\n"
                    "  record._edi_send_via_edi(conf.type_id)"
                ),
            }
        )
        cls.edi_conf_cancelled = cls.env["edi.configuration"].create(
            {
                "name": "Demo Purchase Order - order cancelled",
                "type_id": cls.exc_type.id,
                "backend_id": cls.backend.id,
                "model_id": cls.env["ir.model"]._get_id("purchase.order"),
                "trigger_id": cls.env.ref(
                    "edi_purchase_oca.edi_conf_trigger_purchase_order_state_change"
                ).id,
                "snippet_do": (
                    "if record.state == 'cancel':\n"
                    "  record._edi_send_via_edi(conf.type_id)"
                ),
            }
        )
        cls._setup_order()
        cls._load_module_components(cls, "edi_core_oca")
        cls._load_module_components(cls, "edi_purchase_oca")
        cls._build_components(
            cls,
            Generator,
            Sender,
        )

    def setUp(self):
        super().setUp()
        Generator.reset_faked()
        Sender.reset_faked()

    def test_lookup(self):
        record = self.backend.create_record(self.exc_type.code, {})
        comp = self.backend._get_component(record, "generate")
        self.assertEqual(comp._name, Generator._name)
        comp = self.backend._get_component(record, "send")
        self.assertEqual(comp._name, Sender._name)

    def test_new_order_no_conf_no_output(self):
        order = self._create_purchase_order()
        order.button_confirm()
        self.assertFalse(order.exchange_record_ids)

    def test_new_order_1conf_output(self):
        self.vendor.edi_purchase_conf_ids = self.edi_conf_confirmed
        order = self._create_purchase_order()
        self.assertFalse(order.exchange_record_ids)
        order.with_context(fake_output="ORDER CONFIRM").button_confirm()
        self.assertEqual(len(order.exchange_record_ids), 1)
        record = order.exchange_record_ids[0]
        self.assertEqual(record._get_file_content(), "ORDER CONFIRM")
        self.assertEqual(record.type_id, self.exc_type)

    def test_new_order_2conf_output(self):
        self.vendor.edi_purchase_conf_ids = (
            self.edi_conf_confirmed | self.edi_conf_cancelled
        )
        order = self._create_purchase_order()
        self.assertFalse(order.exchange_record_ids)
        order.with_context(fake_output="ORDER CONFIRM").button_confirm()
        self.assertEqual(len(order.exchange_record_ids), 1)
        record = order.exchange_record_ids[0]
        self.assertEqual(record._get_file_content(), "ORDER CONFIRM")
        self.assertEqual(record.type_id, self.exc_type)
        order.with_context(fake_output="ORDER CANCEL").button_cancel()
        record1, record2 = order.exchange_record_ids
        self.assertEqual(record1.type_id, self.exc_type)
        self.assertEqual(record1._get_file_content(), "ORDER CONFIRM")
        self.assertEqual(record2.type_id, self.exc_type)
        self.assertEqual(record2._get_file_content(), "ORDER CANCEL")
