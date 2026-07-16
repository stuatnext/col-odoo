from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    col_deal_type = fields.Selection([
        ("content_license", "Content licence"),
        ("telco", "Telco / carrier"),
        ("distribution", "Distribution representation"),
        ("platform", "Platform / CTV / FAST"),
        ("acquisition", "Content acquisition"),
        ("co_pro", "Co-production"),
    ], string="Deal type", default="content_license", tracking=True)
    col_title_ids = fields.Many2many(
        "col.title", "col_crm_lead_title_rel", "lead_id", "title_id",
        string="Titles in scope")
    col_country_ids = fields.Many2many(
        "res.country", "col_crm_lead_country_rel", "lead_id", "country_id",
        string="Territories")
    col_media_ids = fields.Many2many(
        "col.media", "col_crm_lead_media_rel", "lead_id", "media_id",
        string="Platform rights")
    col_commercial_model = fields.Selection([
        ("minimum_guarantee", "Minimum guarantee"),
        ("flat_fee", "Flat fee"),
        ("revenue_share", "Revenue share"),
        ("hybrid", "Hybrid"),
        ("tbc", "To be agreed"),
    ], string="Commercial model", default="tbc", tracking=True)
    col_scope_note = fields.Text("Scope and next steps")

    delivery_project_ids = fields.One2many(
        "project.project", "crm_lead_id", string="Delivery projects")
    delivery_project_count = fields.Integer(compute="_compute_delivery_project_count")

    @api.depends("delivery_project_ids")
    def _compute_delivery_project_count(self):
        for lead in self:
            lead.delivery_project_count = len(lead.delivery_project_ids)

    def action_view_delivery_projects(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Delivery Projects"),
            "res_model": "project.project",
            "view_mode": "kanban,tree,form",
            "domain": [("crm_lead_id", "=", self.id)],
            "context": {"default_crm_lead_id": self.id,
                        "default_partner_id": self.partner_id.id},
        }

    def action_create_delivery_project(self):
        self.ensure_one()
        if self.type != "opportunity":
            raise UserError(_("Convert this lead to an opportunity before creating delivery work."))
        if self.delivery_project_ids:
            return self.action_view_delivery_projects()

        project = self.env["project.project"].create({
            "name": _("Delivery: %s") % self.name,
            "partner_id": self.partner_id.id,
            "crm_lead_id": self.id,
            "col_deal_type": self.col_deal_type,
            "col_title_ids": [(6, 0, self.col_title_ids.ids)],
            "col_country_ids": [(6, 0, self.col_country_ids.ids)],
            "col_media_ids": [(6, 0, self.col_media_ids.ids)],
            "col_commercial_model": self.col_commercial_model,
        })
        project._create_col_delivery_tasks()
        return {
            "type": "ir.actions.act_window",
            "name": _("Delivery Project"),
            "res_model": "project.project",
            "view_mode": "form",
            "res_id": project.id,
        }
