# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.edi_sale_oca.tests.common import OrderMixin
from odoo.addons.edi_sale_order_split_strategy.hooks import post_init_hook


class TestSaleOrderSplitStrategy(BaseCommon, OrderMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        backend_type = cls.env["edi.backend.type"].create(
            {"name": "Test backend type", "code": "test_split_backend_type"}
        )
        cls.backend = cls.env["edi.backend"].create(
            {"name": "Test backend", "backend_type_id": backend_type.id}
        )
        cls.exc_type_in = cls.env["edi.exchange.type"].create(
            {
                "name": "Test order in",
                "code": "test_split_order_in",
                "backend_type_id": backend_type.id,
                "direction": "input",
                "exchange_file_ext": "xml",
            }
        )
        cls.exc_record_in = cls.backend.create_record(
            cls.exc_type_in.code, {"edi_exchange_state": "input_received"}
        )
        cls.exc_record_in_2 = cls.backend.create_record(
            cls.exc_type_in.code, {"edi_exchange_state": "input_received"}
        )
        cls.product_b = cls.env.ref("product.product_product_4b")
        line_filter = cls.env["ir.filters"].create(
            {
                "name": "Test split product B",
                "domain": repr([("product_id", "=", cls.product_b.id)]),
                "model_id": "sale.order.line",
            }
        )
        cls.split_strategy = cls.env["sale.order.split.strategy"].create(
            {"name": "Test split strategy", "line_filter_id": line_filter.id}
        )

    def _create_order(self):
        return self._setup_order(
            origin_exchange_record_id=self.exc_record_in.id,
            line_defaults=dict(origin_exchange_record_id=self.exc_record_in.id),
            split_strategy_id=self.split_strategy.id,
        )

    def test_split_keeps_edi_origin(self):
        order = self._create_order()
        self.assertEqual(order.origin_exchange_record_id, self.exc_record_in)
        new_order = order.action_split()
        self.assertTrue(new_order)
        self.assertNotEqual(new_order, order)
        # The new order keeps the same EDI origin as the order it was split from
        self.assertEqual(new_order.origin_exchange_record_id, self.exc_record_in)
        self.assertEqual(new_order.origin_exchange_type_id, self.exc_type_in)
        # The moved line kept its own origin all along
        moved_line = new_order.order_line.filtered(
            lambda x: x.product_id == self.product_b
        )
        self.assertEqual(moved_line.origin_exchange_record_id, self.exc_record_in)
        # And the original exchange record can find the new order too
        related = self.env["edi.exchange.related.record"].search(
            [
                ("exchange_record_id", "=", self.exc_record_in.id),
                ("model", "=", "sale.order"),
                ("res_id", "=", new_order.id),
            ]
        )
        self.assertTrue(related)

    def _create_broken_order(self, line_origins):
        """An order w/ no EDI origin whose lines have the given origins.

        Simulates the pre-fix state: as if (some of) its lines had been
        moved there by a split performed before this module existed.
        """
        order = self._setup_order()
        for line, origin in zip(order.order_line, line_origins, strict=True):
            line.origin_exchange_record_id = origin.id if origin else False
        return order

    def test_post_init_hook_backfills_broken_order(self):
        order = self._create_broken_order(
            [self.exc_record_in, self.exc_record_in, self.exc_record_in]
        )
        self.assertFalse(order.origin_exchange_record_id)
        post_init_hook(self.env)
        self.assertEqual(order.origin_exchange_record_id, self.exc_record_in)
        related = self.env["edi.exchange.related.record"].search(
            [
                ("exchange_record_id", "=", self.exc_record_in.id),
                ("model", "=", "sale.order"),
                ("res_id", "=", order.id),
            ]
        )
        self.assertTrue(related)

    def test_post_init_hook_skips_ambiguous_origins(self):
        order = self._create_broken_order(
            [self.exc_record_in, self.exc_record_in_2, self.env["edi.exchange.record"]]
        )
        post_init_hook(self.env)
        # Lines disagree on their origin: nothing safe to backfill.
        self.assertFalse(order.origin_exchange_record_id)
