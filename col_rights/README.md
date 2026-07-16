# `col_rights` — Build & Install Guide

Content Rights & Avails management for COL Group International / FlareFlow.
Target: **Odoo 17.0** (notes for 18.0 at the bottom). Tested logic, reference implementation.

---

## 0. What you're building

| Model | Purpose |
|---|---|
| `col.title` | The catalogue (one row per title, auto-coded `FF-0001`) |
| `col.genre` / `col.media` / `col.language` / `col.tag` | Controlled picklists (kills genre free-text sprawl) |
| `col.agreement` | Contract header (counterparty, state, signed docs) |
| `col.rights.grant` | **The core** — one title → many grants (territory × media × language × window × exclusivity) |
| `col.avails.wizard` | "What's sellable in {country}/{media}/{date}?" |

The engine lives in `models/col_rights_grant.py`: `_conflicts_with()` + `_compute_conflicts()` (soft flag) and `_compute_status()` + the daily cron (windowing).

---

## 1. Prerequisites

- Odoo 17.0 (source checkout, Odoo.sh, or Docker). **Custom modules are NOT allowed on Odoo Online (SaaS)** — use Odoo.sh or self-host.
- Python 3.10+ and PostgreSQL 12+ (bundled if you use Docker/Odoo.sh).
- Module depends on `base, mail, contacts, sale_management` — all standard.

---

## 2. Install the module

### Option A — source / self-host

```bash
# 1. Put the module on your addons path
cp -r "col_rights" /path/to/odoo/custom-addons/

# 2. Make sure that path is in your conf
#    odoo.conf ->  addons_path = /path/to/odoo/addons,/path/to/odoo/custom-addons

# 3. Start Odoo, update the apps list, install
./odoo-bin -c odoo.conf -d coldb -u base --stop-after-init      # refresh registry
./odoo-bin -c odoo.conf -d coldb -i col_rights --stop-after-init

# 4. Run normally and log in; the "Rights" app appears in the menu
./odoo-bin -c odoo.conf -d coldb
```

During development use live reload + asset rebuild:

```bash
./odoo-bin -c odoo.conf -d coldb -u col_rights --dev=all
```

### Option B — Odoo.sh

1. Push `col_rights/` into your repo (e.g. under `/` or `/addons`).
2. Odoo.sh auto-detects and installs on the branch build.
3. Install via **Apps → search "COL Content Rights" → Activate** on the build's database.

### Option C — Docker (quick local trial)

```bash
docker run -d --name odoo17-db -e POSTGRES_PASSWORD=odoo -e POSTGRES_USER=odoo -e POSTGRES_DB=postgres postgres:15
docker run -d --name odoo17 -p 8069:8069 --link odoo17-db:db \
  -v "$PWD/col_rights:/mnt/extra-addons/col_rights" odoo:17
# Apps -> Update Apps List -> install "COL Content Rights & Avails"
```

---

## 3. Run the test suite

The six acceptance scenarios (incl. the **AIS-vs-TRUE** case) live in `tests/test_conflict.py`:

```bash
./odoo-bin -c odoo.conf -d coldb_test -i col_rights \
    --test-enable --test-tags col_rights --stop-after-init --log-level=test
```

Expect all of `test_01_ais_true_conflict` … `test_06_avails_finder` to pass.

---

## 4. Load the real data (from the workbooks already built)

Two source files in the parent folder:
`COL Master Catalog (consolidated).csv` and `COL Rights & Avails Model.xlsx`.

### 4a. Titles — via UI import
**Rights → Titles → ⚙ Favorites → Import records**, map:

| CSV column | Odoo field |
|---|---|
| Title (EN) | `name` |
| Title (CN) | `name_cn` |
| Genre (normalised) | `genre_id` (by name — create genres first or let import match) |
| Episodes | `episode_count` |
| Languages | `available_language_ids` (comma-separated, by name) |

Leave **Title ID** unmapped — the sequence fills `code` automatically. (Or map your `FF-xxxx` to `code` to preserve IDs.)

### 4b. Agreements + grants — small enough to enter by hand or import
From tab **"3. Rights & Avails"** create one `col.agreement` per licensee, then the grants. On save, the **AIS grant auto-flags `has_conflict = True`** against TRUE — your live proof the engine works.

### 4c. Programmatic seed (optional)
For repeatable demos, add a `post_init_hook` in `__manifest__.py` and create the 9 seed grants in code (mirror `tests/test_conflict.py`).

---

## 5. Configuration switches

- **Hard-block exclusive double-booking** (default OFF — flag only):
  `Settings → Technical → System Parameters` → add `col_rights.block_exclusive = 1`.
  When on, saving a second *licensed exclusive* over an overlapping one raises a `ValidationError` (see `_check_hard_exclusive`).
- **Daily recompute cron**: `Settings → Technical → Scheduled Actions → "COL: recompute rights grant status & conflicts"`. Run it manually once after import to settle statuses.

---

## 6. How the engine works (orientation for maintenance)

- **Conflict rule** (`_conflicts_with`): same title AND territory∩ AND media∩ AND window∩ AND (either grant exclusive/holdback).
- **Cross-record accuracy**: editing grant B can change grant A's flag, so `create/write/unlink` call `_recompute_conflicts_for_titles()` to refresh every grant of the affected title(s). The daily cron does a full sweep for time-based changes.
- **Status** is a *stored computed* field; because it depends on "today", the cron invalidates + recomputes so expired windows flip and rights **revert to available**.
- **Avails wizard** inverts the rule: gather committed blocking grants for the territory/media/window, subtract those titles.

---

## 7. Extending (phase 2 roadmap)

1. **Royalty / rev-share** — add `col.rights.grant.revenue_model` + `account.move` generation; analytic accounts per grant.
2. **Title packages** — `col.title.package` grouping so a grant can target "50 GP titles".
3. **CRM linkage** — surface `col.agreement.crm_lead_id` on the opportunity form.
4. **Dashboards** — spreadsheet/`board` views: pipeline by territory, expiring-in-90-days, conflicts open.

---

## 8. Odoo 18 migration notes

- `<tree>` → `<list>` in view arch (and the action `view_mode` `tree` → `list`).
- Confirm `web_ribbon` `bg_color` token (`text-bg-danger`) — unchanged in 18, but verify.
- Everything else (new-style `invisible="..."` attributes — no `attrs`/`states`) is already 17/18-compatible.
```
