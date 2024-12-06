# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo.addons.component.core import Component

from .common import TestEdiProjectOcaCommon

_logger = logging.getLogger(__name__)


class TestProjectTaskListener(TestEdiProjectOcaCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        class ProjectTaskEventListenerTest(Component):
            _name = "project.task.event.listener.test"
            _inherit = "base.event.listener"
            _apply_on = ["project.task"]

            def on_record_create(self, record, fields=None):
                _logger.info(f"Created task {record.id} with fields {fields}")

            def on_record_write(self, record, fields=None):
                _logger.info(f"Updated task {record.id} with fields {fields}")

            def on_record_unlink(self, record):
                _logger.info(f"Deleting task {record.id}")

        cls._build_and_add_component(ProjectTaskEventListenerTest)
        cls.project = cls.env["project.project"].create({"name": "Project"})

    def test_01_project_create(self):
        with self.assertLogs() as log_capturer:
            task = self.env["project.task"].create(
                {"name": "Task", "project_id": self.project.id}
            )
        self._check_msg_in_log_output(
            r"^INFO:odoo.addons.edi_project_oca.tests.test_project_task_listener:"
            rf"Created task {task.id} with fields\s+",
            log_capturer.output,
        )

    def test_02_project_write(self):
        task = self.env["project.task"].create(
            {"name": "Task", "project_id": self.project.id}
        )
        with self.assertLogs() as log_capturer:
            task.name = "Task Test"
        self._check_msg_in_log_output(
            r"^INFO:odoo.addons.edi_project_oca.tests.test_project_task_listener:"
            rf"Updated task {task.id} with fields\s+",
            log_capturer.output,
        )

    def test_03_project_unlink(self):
        task = self.env["project.task"].create(
            {"name": "Task", "project_id": self.project.id}
        )
        with self.assertLogs() as log_capturer:
            task.unlink()
        self._check_msg_in_log_output(
            r"^INFO:odoo.addons.edi_project_oca.tests.test_project_task_listener:"
            f"Deleting task {task.id}",
            log_capturer.output,
        )
