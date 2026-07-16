import logging
from datetime import date

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Seed demo data drawn from the real COL deals so a fresh install comes up
    with a working catalogue, agreements and the live AIS-vs-TRUE conflict.

    Idempotent: skips if any agreement already exists.
    """
    if env["col.agreement"].search_count([]):
        _logger.info("col_rights: agreements already present, skipping seed.")
        return

    ref = env.ref
    media = lambda code: ref("col_rights.media_%s" % code)
    lang = lambda code: ref("col_rights.lang_%s" % code)
    genre = lambda code: ref("col_rights.genre_%s" % code)

    Title = env["col.title"]
    Partner = env["res.partner"]
    Agreement = env["col.agreement"]
    Grant = env["col.rights.grant"]

    # --- Titles (3 representative, real titles from the catalogue) ---
    t1 = Title.create({"name": "Empress From the Future", "name_cn": "穿到古代当女帝",
                       "genre_id": genre("fantasy").id, "episode_count": 80,
                       "available_language_ids": [(6, 0, [lang("en").id, lang("cn").id])]})
    t2 = Title.create({"name": "Oh Shit! I'm the Empress Now", "name_cn": "糟糕！我成娘娘了",
                       "genre_id": genre("historical").id, "episode_count": 76,
                       "available_language_ids": [(6, 0, [lang("en").id, lang("cn").id])]})
    t3 = Title.create({"name": "Doomed to Love You Again", "name_cn": "无限轮回里的爱",
                       "genre_id": genre("romance").id, "episode_count": 90,
                       "available_language_ids": [(6, 0, [lang("en").id])]})

    # --- Counterparties ---
    def partner(name):
        return Partner.create({"name": name, "is_company": True})

    gp = partner("Green Pixel Ltd")
    true = partner("TRUE (Thailand)")
    ais = partner("AIS (Thailand)")
    nowtv = partner("HKT / NowTV")
    dv = partner("Digital Virgo")
    hisense = partner("Hisense / VIDAA")
    tubi = partner("Tubi")

    # --- Countries ---
    th = ref("base.th"); hk = ref("base.hk"); fr = ref("base.fr")
    de = ref("base.de"); uk = ref("base.uk"); ch = ref("base.ch")
    us = ref("base.us")

    def agr(name, partner, atype, state, terms=""):
        return Agreement.create({"name": name, "partner_id": partner.id,
                                 "agreement_type": atype, "state": state,
                                 "commercial_terms": terms})

    # R-001 Green Pixel: worldwide SVOD, English, non-exclusive (SIGNED)
    a_gp = agr("COL x Green Pixel Licensing 2026", gp, "license_out", "signed",
               "Per-title licence fee (inv. US$65,000 + Mar 2026)")
    for t in (t1, t2, t3):
        Grant.create({"title_id": t.id, "agreement_id": a_gp.id, "worldwide": True,
                      "media_ids": [(6, 0, media("svod").ids)],
                      "language_ids": [(6, 0, [lang("en").id])],
                      "exclusivity": "non_exclusive", "date_start": date(2026, 2, 3)})

    # R-003 TRUE: Thailand Telco EXCLUSIVE (incumbent, SIGNED) -> will block AIS
    a_true = agr("TRUE Thailand Telco (incumbent)", true, "telco", "signed",
                 "Assumed Thailand telco exclusivity")
    Grant.create({"title_id": t1.id, "agreement_id": a_true.id,
                  "country_ids": [(6, 0, th.ids)], "media_ids": [(6, 0, media("telco").ids)],
                  "exclusivity": "exclusive", "date_start": date(2026, 1, 1)})

    # R-002 AIS via Rock: Thailand Telco (IN NEGOTIATION) -> CONFLICTS with TRUE
    a_ais = agr("AIS Thailand (via Rock) - CPAS", ais, "telco", "negotiation",
                "CPAS $0.50 then $0.25 / active user; RS 50:50")
    Grant.create({"title_id": t1.id, "agreement_id": a_ais.id,
                  "country_ids": [(6, 0, th.ids)], "media_ids": [(6, 0, media("telco").ids)],
                  "language_ids": [(6, 0, [lang("th").id])],
                  "exclusivity": "non_exclusive", "date_start": date(2026, 6, 1),
                  "note": "Exclusivity conflict with TRUE - resolve before signing."})

    # R-004 NowTV: Hong Kong Telco (SENT)
    a_now = agr("HKT / NowTV - SSO/OTT bundle", nowtv, "telco", "sent",
                "Weekly HKD18 / Monthly HKD38; RS 55% NowTV / 45% FF")
    Grant.create({"title_id": t2.id, "agreement_id": a_now.id,
                  "country_ids": [(6, 0, hk.ids)], "media_ids": [(6, 0, media("telco").ids)],
                  "exclusivity": "non_exclusive", "date_start": date(2026, 5, 1)})

    # R-005 Digital Virgo: FR/DE/UK/CH carrier billing (NEGOTIATION)
    a_dv = agr("Digital Virgo - Carrier Billing", dv, "payment", "negotiation",
               "RS 22% to FF; DV >EUR 10M marketing over 3 yrs")
    Grant.create({"title_id": t3.id, "agreement_id": a_dv.id,
                  "country_ids": [(6, 0, [fr.id, de.id, uk.id, ch.id])],
                  "media_ids": [(6, 0, media("telco").ids)],
                  "exclusivity": "non_exclusive"})

    # R-006 Hisense/VIDAA: worldwide CTV/FAST (NEGOTIATION)
    a_his = agr("Hisense / VIDAA - CTV/FAST", hisense, "ctv_fast", "negotiation",
                "RPH + 30% tech fee on gross")
    Grant.create({"title_id": t1.id, "agreement_id": a_his.id, "worldwide": True,
                  "media_ids": [(6, 0, [media("ctv").id, media("fast").id])],
                  "exclusivity": "non_exclusive"})

    # R-009 Tubi: USA AVOD (PROSPECT)
    a_tubi = agr("Tubi - FF Originals (prospect)", tubi, "license_out", "prospect")
    Grant.create({"title_id": t2.id, "agreement_id": a_tubi.id,
                  "country_ids": [(6, 0, us.ids)], "media_ids": [(6, 0, media("avod").ids)],
                  "language_ids": [(6, 0, [lang("en").id])], "exclusivity": "non_exclusive"})

    conflicts = Grant.search([("has_conflict", "=", True)])
    _logger.info("col_rights: seeded %s titles, %s agreements, %s grants (%s in conflict).",
                 Title.search_count([]), Agreement.search_count([]),
                 Grant.search_count([]), len(conflicts))
