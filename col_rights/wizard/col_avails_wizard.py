from odoo import api, fields, models, _


class ColAvailsWizard(models.TransientModel):
    _name = "col.avails.wizard"
    _description = "Availability finder"

    country_id = fields.Many2one("res.country", required=True)
    media_id = fields.Many2one("col.media", required=True)
    language_id = fields.Many2one("col.language")
    date_check = fields.Date(default=fields.Date.context_today, required=True)
    want_exclusive = fields.Boolean("Need exclusive?")

    def action_find(self):
        self.ensure_one()
        Grant = self.env["col.rights.grant"]
        blocking = Grant.search([
            ("status", "in", ["optioned", "licensed"]),
            ("media_ids", "in", self.media_id.id),
        ])
        blocked_titles = set()
        for g in blocking:
            cc = g._expanded_countries()
            terr_hit = (cc is None) or (self.country_id.id in cc)
            window_hit = g._ranges_overlap(g.date_start, g.date_end,
                                           self.date_check, self.date_check)
            blocks = g.exclusivity in ("exclusive", "holdback") or self.want_exclusive
            if self.language_id:
                # if asking for a specific language, only a grant covering it blocks
                if g.language_ids and self.language_id not in g.language_ids:
                    continue
            if terr_hit and window_hit and blocks:
                blocked_titles.add(g.title_id.id)

        domain = [("id", "not in", list(blocked_titles))]
        if self.language_id:
            domain.append(("available_language_ids", "in", self.language_id.id))
        available = self.env["col.title"].search(domain)
        return {
            "type": "ir.actions.act_window",
            "name": _("Available titles - %s / %s") % (self.country_id.name, self.media_id.name),
            "res_model": "col.title",
            "view_mode": "tree,form",
            "domain": [("id", "in", available.ids)],
            "context": {"create": False},
        }
