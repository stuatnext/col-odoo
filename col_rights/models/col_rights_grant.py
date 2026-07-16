from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

FAR_FUTURE = date(2999, 12, 31)
# Statuses that represent a real commitment capable of blocking other grants.
COMMITTED = ("optioned", "licensed")


class ColRightsGrant(models.Model):
    _name = "col.rights.grant"
    _description = "Rights Grant / Avail"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "title_id, date_start"

    name = fields.Char(compute="_compute_name", store=True)
    title_id = fields.Many2one("col.title", required=True, ondelete="cascade", index=True)
    agreement_id = fields.Many2one("col.agreement", index=True, ondelete="set null")
    partner_id = fields.Many2one(related="agreement_id.partner_id", store=True, string="Licensee")

    # --- Territory: worldwide OR a set of countries / regions ---
    worldwide = fields.Boolean("Worldwide", default=False)
    country_ids = fields.Many2many("res.country", "col_grant_country_rel",
                                   "grant_id", "country_id", string="Countries")
    country_group_ids = fields.Many2many("res.country.group", "col_grant_cgroup_rel",
                                         "grant_id", "group_id", string="Regions")

    # --- Rights dimensions ---
    media_ids = fields.Many2many("col.media", "col_grant_media_rel",
                                 "grant_id", "media_id", string="Media / Platform", required=True)
    language_ids = fields.Many2many("col.language", "col_grant_lang_rel",
                                    "grant_id", "lang_id", string="Languages")
    exclusivity = fields.Selection([
        ("exclusive", "Exclusive"),
        ("non_exclusive", "Non-exclusive"),
        ("holdback", "Holdback (reserved)"),
    ], default="non_exclusive", required=True, tracking=True)

    # --- Window ---
    date_start = fields.Date("Term start")
    date_end = fields.Date("Term end")  # blank = perpetual / open

    # --- Lifecycle ---
    status = fields.Selection([
        ("available", "Available"),
        ("optioned", "Optioned"),
        ("licensed", "Licensed"),
        ("expired", "Expired"),
    ], compute="_compute_status", store=True, tracking=True, index=True)

    # --- Conflict surfacing (soft flag, see _compute_conflicts) ---
    conflict_ids = fields.Many2many("col.rights.grant", compute="_compute_conflicts",
                                    string="Conflicting grants")
    has_conflict = fields.Boolean(compute="_compute_conflicts", store=True, index=True)

    note = fields.Text()

    # ------------------------------------------------------------------
    # Display name
    # ------------------------------------------------------------------
    @api.depends("title_id.name", "partner_id.name")
    def _compute_name(self):
        for g in self:
            parts = [g.title_id.name or _("New")]
            if g.partner_id:
                parts.append(g.partner_id.name)
            g.name = " - ".join(parts)

    # ------------------------------------------------------------------
    # Overlap helpers (pure logic, easily unit-tested)
    # ------------------------------------------------------------------
    def _expanded_countries(self):
        """Set of country ids covered. Return None as a sentinel for worldwide."""
        self.ensure_one()
        if self.worldwide:
            return None
        ids = set(self.country_ids.ids)
        for grp in self.country_group_ids:
            ids |= set(grp.country_ids.ids)
        return ids

    @staticmethod
    def _ranges_overlap(s1, e1, s2, e2):
        s1 = s1 or date.min
        e1 = e1 or FAR_FUTURE
        s2 = s2 or date.min
        e2 = e2 or FAR_FUTURE
        return s1 <= e2 and s2 <= e1

    def _territory_overlaps(self, other):
        a = self._expanded_countries()
        b = other._expanded_countries()
        if a is None or b is None:        # either side worldwide
            return True
        return bool(a & b)

    def _media_overlaps(self, other):
        return bool(set(self.media_ids.ids) & set(other.media_ids.ids))

    def _conflicts_with(self, other):
        """Two grants on the SAME title conflict when territory, media and window
        all overlap AND at least one grant is exclusive or a holdback."""
        self.ensure_one()
        if not other or self.id == other.id or self.title_id.id != other.title_id.id:
            return False
        exclusive_involved = (
            "exclusive" in (self.exclusivity, other.exclusivity)
            or "holdback" in (self.exclusivity, other.exclusivity)
        )
        if not exclusive_involved:
            return False
        return (
            self._territory_overlaps(other)
            and self._media_overlaps(other)
            and self._ranges_overlap(self.date_start, self.date_end,
                                     other.date_start, other.date_end)
        )

    # ------------------------------------------------------------------
    # Conflict computation (soft flag, non-blocking by default)
    # ------------------------------------------------------------------
    @api.depends("title_id", "worldwide", "country_ids", "country_group_ids",
                 "media_ids", "exclusivity", "date_start", "date_end", "status")
    def _compute_conflicts(self):
        for grant in self:
            if not grant.id or isinstance(grant.id, models.NewId) or not grant.title_id:
                grant.conflict_ids = [(5, 0, 0)]
                grant.has_conflict = False
                continue
            others = self.search([
                ("title_id", "=", grant.title_id.id),
                ("id", "!=", grant.id),
                ("status", "in", list(COMMITTED)),
            ])
            hits = others.filtered(lambda o: grant._conflicts_with(o))
            grant.conflict_ids = [(6, 0, hits.ids)]
            grant.has_conflict = bool(hits)

    def _recompute_conflicts_for_titles(self):
        """Recompute conflicts across ALL grants of the affected titles, because a
        change to one grant can change a sibling's conflict state."""
        titles = self.mapped("title_id")
        if not titles:
            return
        siblings = self.search([("title_id", "in", titles.ids)])
        siblings.invalidate_recordset(["conflict_ids", "has_conflict"])
        siblings._compute_conflicts()
        siblings._notify_new_conflicts()

    def _notify_new_conflicts(self):
        """Raise a (deduplicated) warning activity for grants that are in conflict."""
        todo = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        for grant in self.filtered("has_conflict"):
            existing = grant.activity_ids.filtered(
                lambda a: a.summary and a.summary.startswith("Rights conflict"))
            if existing:
                continue
            grant.activity_schedule(
                act_type_xmlid=todo and "mail.mail_activity_data_todo" or False,
                summary=_("Rights conflict on %s") % grant.title_id.name,
                note=_("Overlaps committed grant(s): %s") % (
                    ", ".join(grant.conflict_ids.mapped("partner_id.name")) or _("see grant")),
            )

    # ------------------------------------------------------------------
    # Status / windowing
    # ------------------------------------------------------------------
    @api.depends("date_start", "date_end", "agreement_id.state")
    def _compute_status(self):
        today = fields.Date.today()
        for g in self:
            if g.date_end and g.date_end < today:
                g.status = "expired"
            elif g.agreement_id.state == "signed":
                g.status = "licensed"
            elif g.agreement_id.state in ("negotiation", "sent"):
                g.status = "optioned"
            else:
                g.status = "available"

    def _recompute_status(self):
        self.invalidate_recordset(["status"])
        self._compute_status()
        # status change can flip what blocks what -> refresh conflicts too
        self._recompute_conflicts_for_titles()

    @api.model
    def _cron_recompute(self):
        """Daily: re-evaluate time-based expiry (windowing) and conflicts."""
        grants = self.search([])
        grants._recompute_status()

    # ------------------------------------------------------------------
    # Optional hard guard (disabled by default - flag only).
    # Enable by setting the system parameter col_rights.block_exclusive = '1'.
    # ------------------------------------------------------------------
    @api.constrains("worldwide", "country_ids", "country_group_ids", "media_ids",
                    "exclusivity", "date_start", "date_end", "status")
    def _check_hard_exclusive(self):
        if self.env["ir.config_parameter"].sudo().get_param(
                "col_rights.block_exclusive") != "1":
            return
        for grant in self:
            if grant.exclusivity != "exclusive" or grant.status != "licensed":
                continue
            for other in grant.conflict_ids:
                if other.exclusivity == "exclusive" and other.status == "licensed":
                    raise ValidationError(_(
                        "Cannot save: '%s' would double-book an EXCLUSIVE licensed "
                        "grant already held by %s for an overlapping "
                        "territory/media/window.") % (grant.title_id.name,
                                                       other.partner_id.name))

    # ------------------------------------------------------------------
    # CRUD overrides to keep cross-record conflicts accurate
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        grants = super().create(vals_list)
        grants._recompute_conflicts_for_titles()
        return grants

    def write(self, vals):
        res = super().write(vals)
        fields_affecting = {"title_id", "worldwide", "country_ids", "country_group_ids",
                            "media_ids", "exclusivity", "date_start", "date_end",
                            "agreement_id", "status"}
        if fields_affecting & set(vals):
            self._recompute_conflicts_for_titles()
        return res

    def unlink(self):
        titles = self.mapped("title_id")
        res = super().unlink()
        remaining = self.search([("title_id", "in", titles.ids)])
        remaining._recompute_conflicts_for_titles()
        return res
