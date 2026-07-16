from odoo import api, fields, models


class ColTitle(models.Model):
    _name = "col.title"
    _description = "Content Title"
    _inherit = ["mail.thread"]
    _order = "name"
    _rec_name = "name"

    name = fields.Char("Title (EN)", required=True, tracking=True)
    name_cn = fields.Char("Title (CN)")
    code = fields.Char("Title ID", copy=False, index=True, readonly=True,
                       default=lambda self: ("New"))
    active = fields.Boolean(default=True)

    genre_id = fields.Many2one("col.genre", string="Genre")
    sub_genre_ids = fields.Many2many("col.tag", string="Tags / Sub-genre")
    episode_count = fields.Integer("Episodes")
    duration = fields.Char("Episode length")
    paywall_episode = fields.Integer("Paywall starts at episode")
    available_language_ids = fields.Many2many(
        "col.language", "col_title_lang_rel", "title_id", "lang_id",
        string="Languages available (sub/dub)")
    synopsis = fields.Text("Synopsis")
    series_rating = fields.Float("Series rating")
    screener_url = fields.Char("Screener / link")

    product_id = fields.Many2one("product.product", string="Linked product (invoicing)")

    grant_ids = fields.One2many("col.rights.grant", "title_id", string="Rights grants")
    grant_count = fields.Integer(compute="_compute_grant_count")
    conflict_count = fields.Integer(compute="_compute_grant_count")

    @api.depends("grant_ids", "grant_ids.has_conflict")
    def _compute_grant_count(self):
        for title in self:
            title.grant_count = len(title.grant_ids)
            title.conflict_count = len(title.grant_ids.filtered("has_conflict"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code") or vals["code"] == "New":
                seq = self.env["ir.sequence"].next_by_code("col.title") or "FF-0000"
                vals["code"] = seq
        return super().create(vals_list)

    def action_view_grants(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Rights Grants",
            "res_model": "col.rights.grant",
            "view_mode": "tree,form",
            "domain": [("title_id", "=", self.id)],
            "context": {"default_title_id": self.id},
        }
