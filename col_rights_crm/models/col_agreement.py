from odoo import fields, models


class ColAgreement(models.Model):
    _inherit = "col.agreement"

    crm_lead_id = fields.Many2one("crm.lead", string="Originating opportunity", index=True)
