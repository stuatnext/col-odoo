from odoo.tests.common import TransactionCase


class TestSalesDelivery(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Platform"})
        cls.title = cls.env["col.title"].create({"name": "Test Launch Title"})

    def test_opportunity_creates_a_delivery_project_and_checklist(self):
        lead = self.env["crm.lead"].create({
            "name": "Test Content Licence",
            "type": "opportunity",
            "partner_id": self.partner.id,
            "col_deal_type": "content_license",
            "col_title_ids": [(6, 0, self.title.ids)],
        })

        lead.action_create_delivery_project()

        self.assertEqual(len(lead.delivery_project_ids), 1)
        project = lead.delivery_project_ids
        self.assertEqual(project.col_title_ids, self.title)
        self.assertEqual(len(project.task_ids), 8)
        self.assertEqual(
            set(project.task_ids.mapped("col_delivery_stream")),
            {"commercial", "legal", "assets", "localisation", "integration", "launch", "reporting"},
        )

    def test_agreement_creates_a_delivery_project(self):
        agreement = self.env["col.agreement"].create({
            "name": "Test Agreement",
            "partner_id": self.partner.id,
            "agreement_type": "license_out",
        })

        agreement.action_create_delivery_project()

        self.assertEqual(len(agreement.delivery_project_ids), 1)
        self.assertEqual(len(agreement.delivery_project_ids.task_ids), 8)
