# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import re
from collections.abc import Iterable

from odoo.addons.component.core import AbstractComponent, MetaComponent
from odoo.addons.component.tests.common import TransactionComponentRegistryCase


class TestEdiProjectOcaCommon(TransactionComponentRegistryCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registry(cls)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    @classmethod
    def _build_and_add_component(cls, component_cls):
        assert isinstance(component_cls, MetaComponent)
        assert issubclass(component_cls, AbstractComponent)
        component_cls._build_component(cls.comp_registry)
        cls.comp_registry._cache.clear()

    def _check_msg_in_log_output(self, msg: str, outputs: Iterable):
        # We use RegEx and check all outputs because ``create()`` and ``write()``
        # overrides may affect the output of the check in 2 ways:
        # 1. a ``create()`` override invokes a ``write()`` (or viceversa) before the
        #    correlated event is triggered and a log is created => the order of the logs
        #    may not correspond to the expected one
        # 2. an override adds/removes fields from the values passed to the method =>
        #    the fields list logged does not match the expected one
        pattern = re.compile(msg)
        self.assertTrue(any(bool(pattern.match(o)) for o in outputs))
