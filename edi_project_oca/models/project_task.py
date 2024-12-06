# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "edi.exchange.consumer.mixin"]

    edi_disable_auto = fields.Boolean()

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task, vals in zip(tasks, vals_list, strict=True):
            task._event("on_task_create").notify(task, vals)
        return tasks

    def write(self, vals):
        res = super().write(vals)
        for task in self:
            task._event("on_task_write").notify(task, vals)
        return res

    def unlink(self):
        for task in self:
            task._event("on_task_unlink").notify(task)
        return super().unlink()
