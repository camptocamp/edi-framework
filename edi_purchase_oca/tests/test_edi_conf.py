# Copyright 2024 CamptoCamp SA
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


class TestsPurchaseEDIConfiguration(
    TransactionComponentRegistryCase, PurchaseEDIBackendTestMixin, OrderMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registry(cls)
        cls._setup_env()
        cls._setup_records()
        cls.purchase_order = cls.env["purchase.order"]
        cls.exc_type_out = cls._create_exchange_type(
            name="Demo Purchase Order out",
            code="demo_PurchaseOrder_out",
            direction="output",
            exchange_filename_pattern="{record_name}-{type.code}-{dt}",
            exchange_file_ext="xml",
        )
        model = cls.env.ref("edi_component_oca.model_edi_oca_component_handler")
        cls.exc_type_out.generate_model_id = model
        cls.exc_type_out.send_model_id = model
        cls.exc_type_out.process_model_id = model
        cls.exc_type_out.receive_model_id = model
        cls.edi_conf = cls.env["edi.configuration"].create(
            {
                "name": "Demo Purchase Order - order confirmed",
                "type_id": cls.exc_type_out.id,
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
        cls.order_vals = cls._setup_order()
        cls.vendor.edi_purchase_conf_ids = cls.edi_conf
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

    def test_order_confirm(self):
        order = self._create_purchase_order(**self.order_vals)
        self.assertEqual(order.state, "draft")
        self.assertEqual(len(order.exchange_record_ids), 0)
        order.with_context(fake_output="TEST PO OUT").button_confirm()
        self.assertEqual(order.state, "purchase")
        self.assertEqual(len(order.exchange_record_ids), 1)
        self.assertEqual(order.exchange_record_ids[0].type_id, self.exc_type_out)
        self.assertEqual(
            order.exchange_record_ids[0]._get_file_content(), "TEST PO OUT"
        )
