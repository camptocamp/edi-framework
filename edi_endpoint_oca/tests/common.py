# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase


def _setup_backend_type(env):
    """Create demo EDI backend type for tests."""
    return env["edi.backend.type"].create(
        {
            "name": "Demo backend type",
            "code": "demo_backend",
        }
    )


def _setup_edi_backend(env, backend_type):
    """Create demo EDI backend for tests."""
    return env["edi.backend"].create(
        {
            "name": "EDI backend with endpoints DEMO",
            "backend_type_id": backend_type.id,
        }
    )


def _setup_exchange_type(env, backend, backend_type):
    """Create demo EDI exchange type for tests."""
    return env["edi.exchange.type"].create(
        {
            "name": "EDI exchange demo",
            "code": "demo_endpoint",
            "backend_type_id": backend_type.id,
            "direction": "input",
        }
    )


def _setup_edi_endpoint(env, backend, exchange_type, backend_type):
    """Create demo EDI endpoint for tests."""
    return env["edi.endpoint"].create(
        {
            "name": "EDI Demo Endpoint 1",
            "backend_id": backend.id,
            "backend_type_id": backend_type.id,
            "exchange_type_id": exchange_type.id,
            "route": "/demo/try",
            "request_method": "GET",
            "exec_mode": "code",
            "code_snippet": (
                "record = endpoint.create_exchange_record()\n"
                'result = {"response": Response("'
                'Created record: %s" % record.identifier)}'
            ),
        }
    )


class CommonEDIEndpoint(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_env()
        cls._setup_records()

    @classmethod
    def _setup_env(cls):
        cls.env = cls.env(context=cls._setup_context())

    @classmethod
    def _setup_context(cls):
        return dict(
            cls.env.context,
            tracking_disable=True,
        )

    @classmethod
    def _setup_records(cls):
        cls.backend_type = _setup_backend_type(cls.env)
        cls.backend = _setup_edi_backend(cls.env, cls.backend_type)
        cls.exchange_type = _setup_exchange_type(cls.env, cls.backend, cls.backend_type)
        cls.endpoint = _setup_edi_endpoint(
            cls.env, cls.backend, cls.exchange_type, cls.backend_type
        )
