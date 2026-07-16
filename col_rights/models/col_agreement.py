from odoo import api, fields, models


class ColAgreement(models.Model):
    _name = "col.agreement"
    _description = "Licensing / Distribution Agreement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "signed_date desc, id desc"

    name = fields.Char("Reference", required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", "Counterparty", required=True, tracking=True)
    agreement_type = fields.Selection([
        ("license_out", "Content Licence (out)"),
        ("representation", "Representation"),
        ("telco", "Telco / Carrier"),
        ("payment", "Payment / Billing"),
        ("ctv_fast", "CTV / FAST"),
        ("co_pro", "Co-production"),
    ], required=True, default="license_out", tracking=True)
    state = fields.Selection([
        ("prospect", "Prospect"),
        ("negotiation", "In Negotiation"),
        ("sent", "Sent for Signature"),
        ("signed", "Signed / Active"),
        ("expired", "Expired"),
        ("terminated", "Terminated"),
    ], default="prospect", tracking=True, index=True)
    signed_date = fields.Date(tracking=True)
    document_ids = fields.Many2many("ir.attachment", string="Signed documents")
    commercial_terms = fields.Text("Commercial model")
    # NOTE: CRM linkage (crm_lead_id) is provided by the optional bridge module
    # `col_rights_crm`, so the core module installs without depending on `crm`.

    grant_ids = fields.One2many("col.rights.grant", "agreement_id", string="Rights granted")
    grant_count = fields.Integer(compute="_compute_grant_count")

    @api.depends("grant_ids")
    def _compute_grant_count(self):
        for agr in self:
            agr.grant_count = len(agr.grant_ids)

    def write(self, vals):
        res = super().write(vals)
        # Agreement state drives grant status -> recompute affected grants
        if "state" in vals:
            self.mapped("grant_ids")._recompute_status()
        return res

    def action_view_grants(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Rights Grants",
            "res_model": "col.rights.grant",
            "view_mode": "tree,form",
            "domain": [("agreement_id", "=", self.id)],
            "context": {"default_agreement_id": self.id},
        }
