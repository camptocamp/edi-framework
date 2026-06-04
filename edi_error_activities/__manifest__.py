# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "EDI Error Activities",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "license": "AGPL-3",
    "summary": "Generic configurable EDI error activity handling",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/edi-framework",
    "depends": [
        "edi_core_oca",
        "mail",
    ],
    "data": [
        "views/edi_configuration_views.xml",
    ],
    "installable": True,
}
