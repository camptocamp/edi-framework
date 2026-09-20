# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Backfill the EDI origin of sale orders split before this module existed.

    Before this glue module, splitting a sale order dropped
    `origin_exchange_record_id` on the new order (it's `copy=False`),
    even though the lines moved onto it (they are moved, not copied) kept
    their own. Fix pre-existing orders in that state whenever their lines
    agree on a single origin.
    """
    orders = env["sale.order"].search(
        [
            ("origin_exchange_record_id", "=", False),
            ("order_line.origin_exchange_record_id", "!=", False),
        ]
    )
    fixed = env["sale.order"]
    skipped = env["sale.order"]
    for order in orders:
        origins = order.order_line.mapped("origin_exchange_record_id")
        if len(origins) != 1:
            # Lines disagree on their origin (or this isn't actually a split
            # order): nothing safe to backfill automatically here.
            skipped |= order
            continue
        order.origin_exchange_record_id = origins.id
        related_record_exists = env["edi.exchange.related.record"].search_count(
            [
                ("exchange_record_id", "=", origins.id),
                ("model", "=", "sale.order"),
                ("res_id", "=", order.id),
            ]
        )
        if not related_record_exists:
            origins._set_related_record(order)
        fixed |= order
    if fixed:
        _logger.info(
            "edi_sale_order_split_strategy: backfilled EDI origin on %d sale "
            "order(s): %s",
            len(fixed),
            fixed.ids,
        )
    if skipped:
        _logger.warning(
            "edi_sale_order_split_strategy: %d sale order(s) have lines "
            "pointing to more than one EDI origin, could not backfill "
            "automatically, manual review needed: %s",
            len(skipped),
            skipped.ids,
        )
