# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import unittest

from odoo.tests.common import HttpCase

from .common import CommonEDIEndpoint


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EDIEndpointHttpCase skipped")
class EDIEndpointHttpCase(HttpCase, CommonEDIEndpoint):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # force sync for demo records
        cls.env["edi.endpoint"].search([])._handle_registry_sync()

    def tearDown(self):
        # Clear routing cache so each test starts clean
        self.env.registry.clear_cache("routing")
        super().tearDown()

    def _make_request(self, route, headers=None):
        headers = dict(headers or {})
        return self.url_open(route, headers=headers, timeout=60)

    def test_call1(self):
        endpoint = "/edi/demo/try"
        response = self._make_request(endpoint)
        self.assertEqual(response.status_code, 401)
        # Let's login now
        self.authenticate("admin", "admin")
        response = self._make_request(endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Created record:", response.content.decode())
