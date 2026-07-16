from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    agreement_ids = fields.One2many("col.agreement", "crm_lead_id", string="Rights agreements")
    agreement_count = fields.Integer(compute="_compute_agreement_count")

    @api.depends("agreement_ids")
    def _compute_agreement_count(self):
        for lead in self:
            lead.agreement_count = len(lead.agreement_ids)

    def action_view_agreements(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Rights Agreements",
            "res_model": "col.agreement",
            "view_mode": "tree,form",
            "domain": [("crm_lead_id", "=", self.id)],
            "context": {"default_crm_lead_id": self.id,
                        "default_partner_id": self.partner_id.id},
        }
