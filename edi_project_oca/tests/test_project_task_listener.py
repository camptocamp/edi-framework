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

            def on_task_create(self, task, vals: dict):
                _logger.info(f"Created task {task.id} with values {vals}")

            def on_task_write(self, task, vals: dict):
                _logger.info(f"Updated task {task.id} with values {vals}")

            def on_task_unlink(self, task):
                _logger.info(f"Deleting task {task.id}")

        cls._build_and_add_component(ProjectTaskEventListenerTest)
        cls.project = cls.env["project.project"].create({"name": "Project"})

    def test_01_project_create(self):
        vals = {"name": "Task", "project_id": self.project.id}
        with self.assertLogs() as log_capturer:
            task = self.env["project.task"].create(vals)
        self._check_msg_in_log_output(
            f"INFO:odoo.addons.edi_project_oca.tests.test_project_task_listener:"
            f"Created task {task.id} with values {vals}",
            log_capturer.output,
        )

    def test_02_project_write(self):
        task = self.env["project.task"].create(
            {"name": "Task", "project_id": self.project.id}
        )
        vals = {"name": "Task Test"}
        with self.assertLogs() as log_capturer:
            task.write(vals)
        self._check_msg_in_log_output(
            f"INFO:odoo.addons.edi_project_oca.tests.test_project_task_listener:"
            f"Updated task {task.id} with values {vals}",
            log_capturer.output,
        )

    def test_03_project_unlink(self):
        task = self.env["project.task"].create(
            {"name": "Task", "project_id": self.project.id}
        )
        with self.assertLogs() as log_capturer:
            task.unlink()
        self._check_msg_in_log_output(
            f"INFO:odoo.addons.edi_project_oca.tests.test_project_task_listener:"
            f"Deleting task {task.id}",
            log_capturer.output,
        )
