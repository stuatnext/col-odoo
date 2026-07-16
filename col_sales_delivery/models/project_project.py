from odoo import _, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    crm_lead_id = fields.Many2one("crm.lead", string="Sales opportunity", index=True)
    agreement_id = fields.Many2one("col.agreement", string="Rights agreement", index=True)
    col_deal_type = fields.Selection([
        ("content_license", "Content licence"),
        ("telco", "Telco / carrier"),
        ("distribution", "Distribution representation"),
        ("platform", "Platform / CTV / FAST"),
        ("acquisition", "Content acquisition"),
        ("co_pro", "Co-production"),
    ], string="Deal type")
    col_title_ids = fields.Many2many(
        "col.title", "col_project_title_rel", "project_id", "title_id",
        string="Titles in scope")
    col_country_ids = fields.Many2many(
        "res.country", "col_project_country_rel", "project_id", "country_id",
        string="Territories")
    col_media_ids = fields.Many2many(
        "col.media", "col_project_media_rel", "project_id", "media_id",
        string="Platform rights")
    col_commercial_model = fields.Selection([
        ("minimum_guarantee", "Minimum guarantee"),
        ("flat_fee", "Flat fee"),
        ("revenue_share", "Revenue share"),
        ("hybrid", "Hybrid"),
        ("tbc", "To be agreed"),
    ], string="Commercial model", default="tbc")
    col_health = fields.Selection([
        ("on_track", "On track"),
        ("watch", "Needs attention"),
        ("blocked", "Blocked"),
    ], string="Delivery health", default="on_track", tracking=True)
    col_next_milestone = fields.Char("Next milestone")
    col_launch_date = fields.Date("Target launch")

    def _create_col_delivery_tasks(self):
        """Create a repeatable launch checklist once a commercial deal is live."""
        stage_ready = self.env.ref("col_sales_delivery.col_task_stage_ready")
        task_specs = [
            (_("Confirm commercial scope and title list"), "commercial"),
            (_("Execute agreement and set up rights grants"), "legal"),
            (_("Receive and quality-check content assets"), "assets"),
            (_("Prepare metadata, subtitles and localisation"), "localisation"),
            (_("Complete platform or telco integration"), "integration"),
            (_("Complete partner acceptance testing"), "integration"),
            (_("Approve and launch"), "launch"),
            (_("Set reporting cadence and commercial review"), "reporting"),
        ]
        Task = self.env["project.task"]
        for project in self:
            for task_name, stream in task_specs:
                Task.create({
                    "name": task_name,
                    "project_id": project.id,
                    "partner_id": project.partner_id.id,
                    "stage_id": stage_ready.id,
                    "col_delivery_stream": stream,
                    "col_is_milestone": stream in ("launch", "reporting"),
                })
