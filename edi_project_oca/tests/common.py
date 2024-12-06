# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

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

    def _check_msg_in_log_output(self, msg: str, output: Iterable):
        # We use ``assertIn`` because of possible overrides of the methods we're logging
        # in these tests
        # EG: we want to log both creation and update of ``project.task`` via events,
        # but when creating a task, the ``create()`` method is overridden to trigger the
        # ``write()`` method, which in turn triggers its logging event *before* the
        # ``create()`` triggers its own logging event => we end up having 2 messages in
        # the logger output, and the ``create()`` log message which we're trying to
        # track is the second one, not the first one.
        self.assertIn(msg, output)
