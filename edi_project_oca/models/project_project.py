# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProjectProject(models.Model):
    _name = "project.project"
    _inherit = ["project.project", "edi.exchange.consumer.mixin"]

    edi_disable_auto = fields.Boolean()

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        for project, vals in zip(projects, vals_list, strict=True):
            project._event("on_project_create").notify(project, vals)
        return projects

    def write(self, vals):
        res = super().write(vals)
        for project in self:
            project._event("on_project_write").notify(project, vals)
        return res

    def unlink(self):
        for project in self:
            project._event("on_project_unlink").notify(project)
        return super().unlink()
