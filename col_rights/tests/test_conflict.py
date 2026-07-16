from datetime import date, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "col_rights")
class TestRightsConflict(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Grant = cls.env["col.rights.grant"]
        cls.Agreement = cls.env["col.agreement"]
        cls.Title = cls.env["col.title"]

        cls.title = cls.Title.create({"name": "Empress From the Future"})
        cls.title2 = cls.Title.create({"name": "Oh Shit Im the Empress Now"})

        cls.thailand = cls.env.ref("base.th")
        cls.korea = cls.env.ref("base.kr")
        cls.japan = cls.env.ref("base.jp")

        cls.media_telco = cls.env.ref("col_rights.media_telco")
        cls.media_svod = cls.env.ref("col_rights.media_svod")

        cls.true = cls.env["res.partner"].create({"name": "TRUE"})
        cls.ais = cls.env["res.partner"].create({"name": "AIS"})
        cls.gp = cls.env["res.partner"].create({"name": "Green Pixel"})

    def _agreement(self, partner, state="signed", atype="telco"):
        return self.Agreement.create({
            "name": "AGR %s" % partner.name, "partner_id": partner.id,
            "agreement_type": atype, "state": state,
        })

    def test_01_ais_true_conflict(self):
        """The real case: TRUE holds Thailand/Telco/Exclusive; AIS Thailand/Telco clashes."""
        self.Grant.create({
            "title_id": self.title.id,
            "agreement_id": self._agreement(self.true).id,
            "country_ids": [(6, 0, self.thailand.ids)],
            "media_ids": [(6, 0, self.media_telco.ids)],
            "exclusivity": "exclusive",
            "date_start": date(2026, 1, 1),
        })
        ais_grant = self.Grant.create({
            "title_id": self.title.id,
            "agreement_id": self._agreement(self.ais, state="negotiation").id,
            "country_ids": [(6, 0, self.thailand.ids)],
            "media_ids": [(6, 0, self.media_telco.ids)],
            "exclusivity": "non_exclusive",
            "date_start": date(2026, 6, 1),
        })
        self.assertTrue(ais_grant.has_conflict,
                        "AIS grant must flag a conflict with TRUE's exclusive grant")

    def test_02_non_exclusive_stacking(self):
        """Two non-exclusive grants on same territory/media -> no conflict."""
        agr1 = self._agreement(self.gp)
        agr2 = self._agreement(self.ais)
        g1 = self.Grant.create({
            "title_id": self.title.id, "agreement_id": agr1.id,
            "country_ids": [(6, 0, self.korea.ids)],
            "media_ids": [(6, 0, self.media_telco.ids)],
            "exclusivity": "non_exclusive",
        })
        g2 = self.Grant.create({
            "title_id": self.title.id, "agreement_id": agr2.id,
            "country_ids": [(6, 0, self.korea.ids)],
            "media_ids": [(6, 0, self.media_telco.ids)],
            "exclusivity": "non_exclusive",
        })
        self.assertFalse(g1.has_conflict)
        self.assertFalse(g2.has_conflict)

    def test_03_worldwide_blocks_exclusive(self):
        """Worldwide non-exclusive + a new worldwide exclusive -> conflict."""
        self.Grant.create({
            "title_id": self.title.id, "agreement_id": self._agreement(self.gp).id,
            "worldwide": True, "media_ids": [(6, 0, self.media_svod.ids)],
            "exclusivity": "non_exclusive",
        })
        excl = self.Grant.create({
            "title_id": self.title.id, "agreement_id": self._agreement(self.ais).id,
            "worldwide": True, "media_ids": [(6, 0, self.media_svod.ids)],
            "exclusivity": "exclusive",
        })
        self.assertTrue(excl.has_conflict)

    def test_04_different_territory_no_conflict(self):
        """Exclusive grants in different territories never conflict."""
        self.Grant.create({
            "title_id": self.title.id, "agreement_id": self._agreement(self.true).id,
            "country_ids": [(6, 0, self.thailand.ids)],
            "media_ids": [(6, 0, self.media_telco.ids)], "exclusivity": "exclusive",
        })
        g = self.Grant.create({
            "title_id": self.title.id, "agreement_id": self._agreement(self.ais).id,
            "country_ids": [(6, 0, self.korea.ids)],
            "media_ids": [(6, 0, self.media_telco.ids)], "exclusivity": "exclusive",
        })
        self.assertFalse(g.has_conflict)

    def test_05_expiry_windowing(self):
        """A grant whose term has ended flips to 'expired' after recompute."""
        g = self.Grant.create({
            "title_id": self.title.id, "agreement_id": self._agreement(self.gp).id,
            "country_ids": [(6, 0, self.japan.ids)],
            "media_ids": [(6, 0, self.media_svod.ids)],
            "date_start": date(2020, 1, 1), "date_end": date.today() - timedelta(days=1),
        })
        self.assertEqual(g.status, "expired")

    def test_06_avails_finder(self):
        """Avails wizard excludes titles blocked by an exclusive grant."""
        self.Grant.create({
            "title_id": self.title.id, "agreement_id": self._agreement(self.true).id,
            "country_ids": [(6, 0, self.thailand.ids)],
            "media_ids": [(6, 0, self.media_telco.ids)], "exclusivity": "exclusive",
            "date_start": date(2026, 1, 1),
        })
        wiz = self.env["col.avails.wizard"].create({
            "country_id": self.thailand.id, "media_id": self.media_telco.id,
            "date_check": date(2026, 6, 1),
        })
        action = wiz.action_find()
        available_ids = action["domain"][0][2]
        self.assertNotIn(self.title.id, available_ids,
                         "Title under TRUE exclusive must NOT be available in Thailand/Telco")
        self.assertIn(self.title2.id, available_ids,
                      "Unencumbered title must be available")
