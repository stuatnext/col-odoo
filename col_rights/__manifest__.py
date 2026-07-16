{
    "name": "COL Content Rights & Avails",
    "version": "17.0.1.0.0",
    "summary": "Rights grants, availability calculation and conflict detection for content licensing",
    "description": """
COL Group International / FlareFlow - Content Rights & Avails management.

Adds a Rights Grant model (one title -> many grants) plus an availability /
conflict engine:
  * Avails: what can we sell in {territory} on {platform} in {window}?
  * Conflicts: does a new deal clash with an existing exclusive grant?
    (e.g. the live AIS-vs-TRUE Thailand telco exclusivity conflict)
""",
    "category": "Sales/Content",
    "author": "COL Group International",
    "website": "https://col-distribution.com",
    "depends": ["base", "mail", "contacts", "sale_management"],
    "data": [
        "security/col_rights_groups.xml",
        "security/ir.model.access.csv",
        "data/col_rights_data.xml",
        "views/col_rights_views.xml",
    ],
    "application": True,
    "installable": True,
    "license": "LGPL-3",
    "post_init_hook": "post_init_hook",
}
