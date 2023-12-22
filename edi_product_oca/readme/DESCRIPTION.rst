This module intends to create a base to be extended by local edi rules
for product.

In order to add a new integration, you need to create a listener:

.. code-block:: python

    class MyEventListener(Component):
        _name = "product.order.event.listener.demo"
        _inherit = "base.event.listener"
        _apply_on = ["product.template", "product.product"]

        def on_create_product(self, product):
            """Add your code here"""

        def on_write_product(self, product):
            """Add your code here"""

        def on_unlink_product(self, product):
            """Add your code here"""
