# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo.addons.component.core import Component

from .common import TestEdiProjectOcaCommon

_logger = logging.getLogger(__name__)


class TestProjectListener(TestEdiProjectOcaCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        class ProjectEventListenerTest(Component):
            _name = "project.project.event.listener.test"
            _inherit = "base.event.listener"
            _apply_on = ["project.project"]

            def on_record_create(self, record, fields=None):
                _logger.info(f"Created project {record.id} with fields {fields}")

            def on_record_write(self, record, fields=None):
                _logger.info(f"Updated project {record.id} with fields {fields}")

            def on_record_unlink(self, record):
                _logger.info(f"Deleting project {record.id}")

        cls._build_and_add_component(ProjectEventListenerTest)

    def test_01_project_create(self):
        with self.assertLogs() as log_capturer:
            project = self.env["project.project"].create({"name": "Project"})
        self._check_msg_in_log_output(
            r"^INFO:odoo.addons.edi_project_oca.tests.test_project_listener:"
            rf"Created project {project.id} with fields\s+",
            log_capturer.output,
        )

    def test_02_project_write(self):
        project = self.env["project.project"].create({"name": "Project"})
        with self.assertLogs() as log_capturer:
            project.name = "Project Test"
        self._check_msg_in_log_output(
            r"^INFO:odoo.addons.edi_project_oca.tests.test_project_listener:"
            rf"Updated project {project.id} with fields\s+",
            log_capturer.output,
        )

    def test_03_project_unlink(self):
        project = self.env["project.project"].create({"name": "Project"})
        with self.assertLogs() as log_capturer:
            project.unlink()
        self._check_msg_in_log_output(
            r"^INFO:odoo.addons.edi_project_oca.tests.test_project_listener:"
            rf"Deleting project {project.id}",
            log_capturer.output,
        )
