{
    "name": "EDI Sale Order Split Strategy",
    "summary": "Preserve the EDI origin of a sale order across a split",
    "version": "18.0.1.0.0",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "website": "https://github.com/OCA/edi-framework",
    "license": "AGPL-3",
    "development_status": "Alpha",
    "depends": ["edi_sale_oca", "sale_order_split_strategy"],
    "auto_install": True,
    "post_init_hook": "post_init_hook",
}
