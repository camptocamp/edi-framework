# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import os
import unittest

from odoo.tests.common import HttpCase, RecordCapturer

from .common import EDIEndpointTestMixin


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EDIEndpointHttpCase skipped")
class EDIEndpointHttpCase(HttpCase, EDIEndpointTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_env()
        cls._setup_records()
        # Sync only the endpoint under test to avoid re-registering unrelated
        # demo routes that may already exist in the route registry.
        cls.endpoint._handle_registry_sync()

    def tearDown(self):
        # Clear routing cache so each test starts clean
        self.env.registry.clear_cache("routing")
        super().tearDown()

    def _make_request(self, route, headers=None, data=None, method="GET"):
        headers = dict(headers or {})
        return self.url_open(
            route, headers=headers, data=data, method=method, timeout=60
        )

    def test_call1(self):
        endpoint = "/edi/demo/try"
        response = self._make_request(endpoint)
        self.assertEqual(response.status_code, 401)
        # Let's login now
        self.authenticate("admin", "admin")
        response = self._make_request(endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Created record:", response.content.decode())

    def test_create_exchange_record_mode(self):
        """The ``create_exchange_record`` exec mode receives the raw body,
        persists it as an exchange record and returns the standard ack."""
        endpoint = self.endpoint.copy(
            {
                "route": "/create_exchange_record_mode",
                "request_method": "POST",
                "request_content_type": "application/json",
                "exec_mode": "create_exchange_record",
            }
        )
        endpoint._handle_registry_sync()
        self.authenticate("admin", "admin")
        body = b'{"hello": "world"}'
        with RecordCapturer(self.env["edi.exchange.record"]) as rc:
            response = self._make_request(
                "/edi/create_exchange_record_mode",
                data=body,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
        self.assertTrue(rc.records)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "queued")
        self.assertEqual(payload["id"], rc.records.identifier)
        self.assertEqual(base64.b64decode(rc.records.exchange_file), body)
