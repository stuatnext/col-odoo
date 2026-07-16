from odoo import _, api, fields, models


class ColAgreement(models.Model):
    _inherit = "col.agreement"

    delivery_project_ids = fields.One2many(
        "project.project", "agreement_id", string="Delivery projects")
    delivery_project_count = fields.Integer(compute="_compute_delivery_project_count")

    @api.depends("delivery_project_ids")
    def _compute_delivery_project_count(self):
        for agreement in self:
            agreement.delivery_project_count = len(agreement.delivery_project_ids)

    def action_view_delivery_projects(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Delivery Projects"),
            "res_model": "project.project",
            "view_mode": "kanban,tree,form",
            "domain": [("agreement_id", "=", self.id)],
            "context": {"default_agreement_id": self.id,
                        "default_crm_lead_id": self.crm_lead_id.id,
                        "default_partner_id": self.partner_id.id},
        }

    def action_create_delivery_project(self):
        self.ensure_one()
        if self.delivery_project_ids:
            return self.action_view_delivery_projects()
        lead = self.crm_lead_id
        project = self.env["project.project"].create({
            "name": _("Delivery: %s") % self.name,
            "partner_id": self.partner_id.id,
            "crm_lead_id": lead.id,
            "agreement_id": self.id,
            "col_deal_type": lead.col_deal_type if lead else False,
            "col_title_ids": [(6, 0, lead.col_title_ids.ids)] if lead else [],
            "col_country_ids": [(6, 0, lead.col_country_ids.ids)] if lead else [],
            "col_media_ids": [(6, 0, lead.col_media_ids.ids)] if lead else [],
            "col_commercial_model": lead.col_commercial_model if lead else False,
        })
        project._create_col_delivery_tasks()
        return {
            "type": "ir.actions.act_window",
            "name": _("Delivery Project"),
            "res_model": "project.project",
            "view_mode": "form",
            "res_id": project.id,
        }
