from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    col_delivery_stream = fields.Selection([
        ("commercial", "Commercial"),
        ("legal", "Legal and rights"),
        ("assets", "Content assets"),
        ("localisation", "Localisation"),
        ("integration", "Integration"),
        ("launch", "Launch"),
        ("reporting", "Reporting"),
    ], string="Workstream", default="commercial", tracking=True)
    col_is_milestone = fields.Boolean("Milestone")
    col_is_blocked = fields.Boolean("Blocked", tracking=True)
    col_blocker_note = fields.Text("Blocker / decision needed")
    agreement_id = fields.Many2one(related="project_id.agreement_id", string="Rights agreement", readonly=True)
