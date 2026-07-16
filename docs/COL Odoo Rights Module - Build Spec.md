# `col_rights` — Odoo Module Build Specification
### Content Rights & Availability (Avails) Management for COL Group International / FlareFlow

**Version:** 1.0 (draft for developer quoting)
**Target platform:** Odoo 17/18 Community or Enterprise
**Prepared for:** COL Group International — BD team (content licensing, distribution, telco integration)
**Status:** Build brief. The data model, conflict logic, and acceptance tests below are implementation-ready; field names and view layout are recommendations a developer can refine.

---

## 1. Purpose & scope

COL licenses microdrama titles (239 consolidated, growing toward 3,000+) across territories, platforms, languages and time windows, to many partners simultaneously. Today this lives in scattered spreadsheets with no way to answer two questions reliably:

1. **Avails:** *"What can we sell in {territory}, on {platform}, in {window}?"*
2. **Conflicts:** *"Does this new deal clash with an existing exclusive grant?"* (e.g. the live **AIS-vs-TRUE Thailand telco** exclusivity conflict.)

This module adds a **Rights Grant** model (one title → many grants) plus an **availability/conflict engine**. It is the one piece Odoo has no native equivalent for.

**In scope:** titles catalogue, licensees, agreements, rights grants, avails query, conflict detection, status/windowing automation, import from the existing consolidated workbook, dashboards.
**Out of scope (phase 2+):** royalty/rev-share calculation engine, automated invoicing per grant, subtitle/asset (SRT) management, CRM pipeline migration (uses standard `crm`).

---

## 2. Module metadata

```python
# __manifest__.py
{
    "name": "COL Content Rights & Avails",
    "version": "17.0.1.0.0",
    "summary": "Rights grants, availability calculation and conflict detection for content licensing",
    "category": "Sales/Content",
    "author": "COL Group International",
    "depends": ["base", "mail", "contacts", "sale_management"],
    "data": [
        "security/col_rights_groups.xml",
        "security/ir.model.access.csv",
        "data/col_media_data.xml",
        "data/col_language_data.xml",
        "data/ir_cron_data.xml",
        "views/col_title_views.xml",
        "views/col_rights_grant_views.xml",
        "views/col_agreement_views.xml",
        "views/col_avails_wizard_views.xml",
        "views/col_rights_menus.xml",
    ],
    "application": True,
    "license": "LGPL-3",
}
```

`mail` is depended on so grants get chatter + activities (e.g. "expiring in 30 days"). `sale_management` so agreements can later link to quotations/invoices.

---

## 3. Data model

### Entities & relationships

```
res.partner (Licensee)  ──1..n──►  col.agreement  ──1..n──►  col.rights.grant  ◄──n..1──  col.title
                                                                   │  │  │
                                          territory (m2m country + m2m country.group + worldwide bool)
                                          media_ids (m2m col.media)
                                          language_ids (m2m col.language)
```

### 3.1 `col.title` — the catalogue (dimension)

> Option A (recommended): a dedicated `col.title` model, optionally linked to `product.product` for invoicing.
> Option B: extend `product.template`. Use B only if every title must be an invoiceable product from day one.

```python
class ColTitle(models.Model):
    _name = "col.title"
    _description = "Content Title"
    _inherit = ["mail.thread"]
    _order = "name"

    name = fields.Char("Title (EN)", required=True, tracking=True)
    name_cn = fields.Char("Title (CN)")
    code = fields.Char("Title ID", copy=False, index=True)  # e.g. FF-0042 ; auto-sequence
    genre_id = fields.Many2one("col.genre", string="Genre")  # controlled picklist
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
    grant_ids = fields.One2many("col.rights.grant", "title_id", string="Rights grants")
    grant_count = fields.Integer(compute="_compute_grant_count")
    product_id = fields.Many2one("product.product", string="Linked product (invoicing)")
```

Supporting picklists keep data clean (the genre-sprawl problem we found — `Modern Romance` vs `Modern\nRomance`):

```python
class ColGenre(models.Model):
    _name = "col.genre"; _description = "Genre"
    name = fields.Char(required=True)

class ColLanguage(models.Model):
    _name = "col.language"; _description = "Content Language"
    name = fields.Char(required=True)       # English, Chinese, Korean, Thai, Bahasa Indonesia...
    code = fields.Char()                    # EN, CN, KO, TH, ID

class ColMedia(models.Model):
    _name = "col.media"; _description = "Media / Platform Type"
    name = fields.Char(required=True)       # SVOD, AVOD, Telco/Carrier, FAST, CTV, Theatrical
    code = fields.Char()
```

### 3.2 `col.agreement` — contract header

```python
class ColAgreement(models.Model):
    _name = "col.agreement"
    _description = "Licensing / Distribution Agreement"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Reference", required=True)        # "COL x Green Pixel Licensing 2026"
    partner_id = fields.Many2one("res.partner", "Counterparty", required=True, tracking=True)
    agreement_type = fields.Selection([
        ("license_out", "Content Licence (out)"),
        ("representation", "Representation"),
        ("telco", "Telco / Carrier"),
        ("payment", "Payment / Billing"),
        ("ctv_fast", "CTV / FAST"),
        ("co_pro", "Co-production"),
    ], required=True, default="license_out")
    state = fields.Selection([
        ("prospect", "Prospect"), ("negotiation", "In Negotiation"),
        ("sent", "Sent for Signature"), ("signed", "Signed / Active"),
        ("expired", "Expired"), ("terminated", "Terminated")],
        default="prospect", tracking=True)
    signed_date = fields.Date(tracking=True)
    document_ids = fields.Many2many("ir.attachment", string="Signed documents")
    commercial_terms = fields.Text("Commercial model")   # rev-share %, CPAS, flat fee
    grant_ids = fields.One2many("col.rights.grant", "agreement_id", string="Rights granted")
    crm_lead_id = fields.Many2one("crm.lead", "Originating opportunity")
```

### 3.3 `col.rights.grant` — **the core**

```python
class ColRightsGrant(models.Model):
    _name = "col.rights.grant"
    _description = "Rights Grant / Avail"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "title_id, date_start"

    name = fields.Char(compute="_compute_name", store=True)
    title_id = fields.Many2one("col.title", required=True, ondelete="cascade", index=True)
    agreement_id = fields.Many2one("col.agreement", index=True)
    partner_id = fields.Many2one(related="agreement_id.partner_id", store=True, string="Licensee")

    # --- Territory (worldwide OR countries/groups) ---
    worldwide = fields.Boolean("Worldwide", default=False)
    country_ids = fields.Many2many("res.country", string="Countries")
    country_group_ids = fields.Many2many("res.country.group", string="Regions")

    # --- Rights dimensions ---
    media_ids = fields.Many2many("col.media", string="Media / Platform", required=True)
    language_ids = fields.Many2many("col.language", string="Languages")
    exclusivity = fields.Selection([
        ("exclusive", "Exclusive"),
        ("non_exclusive", "Non-exclusive"),
        ("holdback", "Holdback (reserved)")], default="non_exclusive", required=True, tracking=True)

    # --- Window ---
    date_start = fields.Date("Term start")
    date_end = fields.Date("Term end")          # blank = perpetual / open

    # --- Lifecycle ---
    status = fields.Selection([
        ("available", "Available"), ("optioned", "Optioned"),
        ("licensed", "Licensed"), ("expired", "Expired")],
        compute="_compute_status", store=True, tracking=True)

    # --- Conflict surfacing (soft, non-blocking) ---
    conflict_ids = fields.Many2many("col.rights.grant", compute="_compute_conflicts",
                                    string="Conflicting grants")
    has_conflict = fields.Boolean(compute="_compute_conflicts", store=True, index=True)
    note = fields.Text()
```

**Design note — why M2M for media and territory, not single fields:** a single grant frequently spans several countries and several platforms. Overlap detection (§4) is set-intersection, which only works if these are collections. This is exactly why "a few properties on the title" is insufficient.

---

## 4. The availability & conflict engine (the crown jewel)

### 4.1 Overlap helpers

```python
from datetime import date
FAR_FUTURE = date(2999, 12, 31)

class ColRightsGrant(models.Model):
    _inherit = "col.rights.grant"

    def _expanded_countries(self):
        """Return the set of country IDs this grant covers (None = worldwide)."""
        self.ensure_one()
        if self.worldwide:
            return None  # sentinel: everything
        ids = set(self.country_ids.ids)
        for grp in self.country_group_ids:
            ids |= set(grp.country_ids.ids)
        return ids

    @staticmethod
    def _ranges_overlap(s1, e1, s2, e2):
        s1 = s1 or date.min; e1 = e1 or FAR_FUTURE
        s2 = s2 or date.min; e2 = e2 or FAR_FUTURE
        return s1 <= e2 and s2 <= e1

    def _territory_overlaps(self, other):
        a = self._expanded_countries(); b = other._expanded_countries()
        if a is None or b is None:      # either worldwide
            return True
        return bool(a & b)

    def _media_overlaps(self, other):
        return bool(set(self.media_ids.ids) & set(other.media_ids.ids))

    def _conflicts_with(self, other):
        """Two grants on the SAME title conflict when territory, media and window
        all overlap AND at least one grant is exclusive or a holdback."""
        if self.id == other.id or self.title_id != other.title_id:
            return False
        exclusive_involved = "exclusive" in (self.exclusivity, other.exclusivity) \
            or "holdback" in (self.exclusivity, other.exclusivity)
        if not exclusive_involved:
            return False
        return (self._territory_overlaps(other)
                and self._media_overlaps(other)
                and self._ranges_overlap(self.date_start, self.date_end,
                                         other.date_start, other.date_end))
```

### 4.2 Conflict surfacing — **soft flag, not a hard block**

Business reality: COL *wants to record* the AIS deal even though TRUE conflicts, so they can work to resolve it. So conflicts are **flagged and raised as an activity**, not prevented:

```python
    @api.depends("title_id", "worldwide", "country_ids", "country_group_ids",
                 "media_ids", "exclusivity", "date_start", "date_end")
    def _compute_conflicts(self):
        for grant in self:
            others = self.search([("title_id", "=", grant.title_id.id),
                                   ("id", "!=", grant.id),
                                   ("status", "in", ["optioned", "licensed"])])
            hits = others.filtered(lambda o: grant._conflicts_with(o))
            grant.conflict_ids = hits
            grant.has_conflict = bool(hits)
```

```python
    def write(self, vals):
        res = super().write(vals)
        for grant in self.filtered("has_conflict"):
            grant.activity_schedule(
                "mail.mail_activity_data_warning",
                summary=_("Rights conflict on %s") % grant.title_id.name,
                note=_("Overlaps exclusive grant(s): %s")
                     % ", ".join(grant.conflict_ids.mapped("partner_id.name")))
        return res
```

> **Optional hard guard:** if COL wants to *prevent* signing a second exclusive over a committed exclusive, add an `@api.constrains` that raises `ValidationError` only when **both** grants are `exclusive` and `status == "licensed"`. Recommended OFF initially (flag-only) so negotiations can be logged.

### 4.3 Computed status & windowing (time-based)

```python
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
```

Because `_compute_status` reads "today", a **daily cron** recomputes so grants flip to *expired* automatically and rights **revert to available** (windowing):

```xml
<!-- data/ir_cron_data.xml -->
<record id="cron_recompute_grant_status" model="ir.cron">
    <field name="name">COL: recompute rights grant status</field>
    <field name="model_id" ref="model_col_rights_grant"/>
    <field name="state">code</field>
    <field name="code">model.search([])._compute_status()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
</record>
```

### 4.4 Avails query — wizard

```python
class ColAvailsWizard(models.TransientModel):
    _name = "col.avails.wizard"
    _description = "Availability finder"

    country_id = fields.Many2one("res.country", required=True)
    media_id = fields.Many2one("col.media", required=True)
    language_id = fields.Many2one("col.language")
    date_check = fields.Date(default=fields.Date.today)
    want_exclusive = fields.Boolean("Need exclusive?")

    def action_find(self):
        self.ensure_one()
        blocking = self.env["col.rights.grant"].search([
            ("status", "in", ["optioned", "licensed"]),
            ("media_ids", "in", self.media_id.id),
        ])
        # titles blocked for this territory+window (exclusive, or any if we need exclusive)
        blocked_titles = set()
        for g in blocking:
            cc = g._expanded_countries()
            terr_hit = (cc is None) or (self.country_id.id in cc)
            window_hit = g._ranges_overlap(g.date_start, g.date_end, self.date_check, self.date_check)
            if terr_hit and window_hit and (g.exclusivity in ("exclusive", "holdback") or self.want_exclusive):
                blocked_titles.add(g.title_id.id)
        available = self.env["col.title"].search([("id", "not in", list(blocked_titles))])
        return {
            "type": "ir.actions.act_window", "name": _("Available titles"),
            "res_model": "col.title", "view_mode": "tree,form",
            "domain": [("id", "in", available.ids)],
        }
```

This is the engine that answers *"Sellable in Japan SVOD now? → 239 titles"* and *"Thailand telco exclusive? → blocked by TRUE"* — the two questions the spreadsheets can't.

---

## 5. Views (representative)

```xml
<!-- views/col_rights_grant_views.xml -->
<record id="view_col_rights_grant_tree" model="ir.ui.view">
  <field name="name">col.rights.grant.tree</field>
  <field name="model">col.rights.grant</field>
  <field name="arch" type="xml">
    <tree decoration-danger="has_conflict==True" decoration-muted="status=='expired'">
      <field name="title_id"/><field name="partner_id"/>
      <field name="country_ids" widget="many2many_tags" optional="show"/>
      <field name="media_ids" widget="many2many_tags"/>
      <field name="exclusivity"/><field name="date_start"/><field name="date_end"/>
      <field name="status" widget="badge"/>
      <field name="has_conflict" widget="boolean_toggle"/>
    </tree>
  </field>
</record>
```

The form view shows a red **conflict ribbon** when `has_conflict` is true, listing `conflict_ids`. Search view ships with filters: **Available / Licensed / Expired**, **Has conflict**, group-by **Territory**, **Media**, **Licensee**. Menus under a top-level **Rights** app: *Titles · Rights Grants · Agreements · Avails Finder · Reporting*.

**Reporting:** pivot + graph views on `col.rights.grant` (grants by status × territory; expiring-soon list) and on `col.agreement` (pipeline value by stage) — this is the "use data to make decisions" layer, native once the model exists.

---

## 6. Security

```csv
# security/ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_title_user,col.title.user,model_col_title,col_rights.group_user,1,1,1,0
access_grant_user,col.grant.user,model_col_rights_grant,col_rights.group_user,1,1,1,0
access_grant_mgr,col.grant.mgr,model_col_rights_grant,col_rights.group_manager,1,1,1,1
access_agreement_user,col.agr.user,model_col_agreement,col_rights.group_user,1,1,1,0
```

Two groups: **Rights User** (BD team — create/edit grants), **Rights Manager** (delete, configure picklists, override conflicts). Optional record rules if acquisition (Jason) and sales (Eileen) should see only their own agreements.

---

## 7. Data migration (from the workbook we built)

Source: **`COL Rights & Avails Model.xlsx`** (already produced).
- **Tab "2. Titles"** → `col.title` (239 rows). Map Title_ID→`code`, EN→`name`, CN→`name_cn`, Genre→`genre_id` (create `col.genre` records from the controlled list), Episodes→`episode_count`, Languages→`available_language_ids`.
- **Tab "3. Rights & Avails"** → `col.agreement` (one per licensee) + `col.rights.grant` (the 9 seeded grants, incl. AIS/TRUE). Territory text → `country_ids`/`worldwide`; Media text → `media_ids`; Exclusivity text → `exclusivity`; dates → `date_start`/`date_end`.

Use Odoo's standard **Import** (xlsx/csv) or a one-off `post_init_hook`. Acceptance: after import, the AIS grant shows `has_conflict = True` against TRUE automatically.

---

## 8. Integration points

| System | How |
|---|---|
| **CRM** (`crm`) | `col.agreement.crm_lead_id` links a grant/agreement back to the opportunity (unifies Jason's acquisition + Eileen's sales pipelines). |
| **Sign** | Attach/route signed PDFs on `col.agreement.document_ids`; trigger `state = signed`. |
| **Accounting** | Phase 2: generate `account.move` per grant for licence fees; rev-share via `account.analytic`. Multi-company handles COL Media Corp + COL Web Pte Ltd. |
| **Documents** | Store the agreement versions in one place — ends the `_final_v2_amended` filename chaos. |

---

## 9. Acceptance criteria / test scenarios

Ship with automated tests (`tests/test_conflict.py`) covering:

1. **AIS/TRUE conflict** — Given TRUE holds Thailand·Telco·Exclusive (licensed), when an AIS Thailand·Telco grant is created, then `has_conflict == True` and a warning activity is raised. *(The real-world case.)*
2. **Non-exclusive stacking** — Two non-exclusive Hong Kong·Telco grants → no conflict.
3. **Worldwide blocks exclusive** — Green Pixel worldwide non-exclusive + a proposed worldwide **exclusive** → conflict.
4. **Different territory** — Thailand grant vs Korea grant → no conflict.
5. **Window expiry/revert** — A grant with `date_end` in the past → status auto-flips to `expired` after cron; avails finder then returns the title as available again.
6. **Avails finder** — "Japan, SVOD, today" returns all 239 titles; "Thailand, Telco, exclusive" excludes titles under the TRUE grant.

---

## 10. Effort & phasing (for quoting)

| Phase | Deliverable | Indicative effort |
|---|---|---|
| 1 | Models (`col.title`, `col.media/genre/language`, `col.agreement`, `col.rights.grant`) + security + basic views | 4–6 dev-days |
| 2 | Conflict engine + computed status + cron + activities | 3–5 dev-days |
| 3 | Avails wizard + reporting (pivot/graph) + conflict ribbon UX | 3–4 dev-days |
| 4 | Data import from workbook + UAT against the 6 test scenarios | 2–3 dev-days |
| 5 | CRM/Sign/Documents wiring | 2–3 dev-days |
| | **Total (excl. royalty/invoicing phase 2 scope)** | **~14–21 dev-days** |

A competent Odoo developer/partner should quote against this directly. Royalty/rev-share automation and per-grant invoicing are a separate, larger phase.

---

## 11. Assumptions & open questions (confirm before build)

1. **TRUE scope** — is TRUE's Thailand exclusivity catalogue-wide or title-specific, and what is the exact term? (Drives whether AIS is fully blocked or partially available.)
2. **Green Pixel** — confirm exclusivity (assumed non-exclusive) and term-end date.
3. **Title vs product** — do titles need to be invoiceable `product.product` records on day one (Option B), or is a clean `col.title` model preferred (Option A, recommended)?
4. **Grant granularity** — track rights at *title* level, or also per *title-set / package* (e.g. "50 GP titles")? Spec supports per-title; packages can be a `col.title.package` grouping in phase 2.
5. **Community vs Enterprise** — Enterprise adds Sign, better dashboards, Studio. Conflict engine works on both.
6. **Hosting** — Odoo.sh, Odoo Online (SaaS — note: custom modules need Odoo.sh or self-host), or self-managed?
```

*Source data and seeded examples drawn from the COL folder: licensing agreements, the Integration Tracker, and the consolidated catalogue/rights workbooks.*
