{
    "name": "COL Sales & Delivery",
    "version": "17.0.1.0.0",
    "summary": "Content sales pipeline and delivery projects for COL / FlareFlow",
    "description": """
Adds COL-specific commercial context to CRM opportunities and converts won
opportunities or signed agreements into cross-functional delivery projects.

The module keeps CRM, Project and Sales as native Odoo applications while
linking them directly to COL titles, rights agreements, territories and
platform types.
""",
    "category": "Sales/Content",
    "author": "COL Group International",
    "depends": ["col_rights_crm", "project"],
    "data": [
        "data/col_sales_delivery_data.xml",
        "views/col_sales_delivery_views.xml",
    ],
    "application": True,
    "installable": True,
    "license": "LGPL-3",
}
