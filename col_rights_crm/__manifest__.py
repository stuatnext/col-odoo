{
    "name": "COL Content Rights - CRM Bridge",
    "version": "17.0.1.0.0",
    "summary": "Links rights agreements to CRM opportunities",
    "description": """
Optional glue module. Adds the originating CRM opportunity to a rights
agreement, and a smart button on the opportunity showing its agreements.

Kept separate so `col_rights` installs without requiring `crm`.
""",
    "category": "Sales/Content",
    "author": "COL Group International",
    "depends": ["col_rights", "crm"],
    "data": [
        "views/col_rights_crm_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
