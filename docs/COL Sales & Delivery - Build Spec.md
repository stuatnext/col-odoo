# COL Sales & Delivery - Build Spec

## Purpose

`col_sales_delivery` is the operational layer that connects commercial work to
post-signature delivery. It relies on standard Odoo CRM and Project; it does
not replace either application.

## Commercial opportunity

Model: `crm.lead`

The module adds the fields below to every CRM opportunity.

| Field | Odoo technical name | Purpose |
|---|---|---|
| Deal type | `col_deal_type` | Licence, telco, distribution, platform, acquisition or co-production |
| Titles in scope | `col_title_ids` | Links the opportunity to catalogue titles |
| Territories | `col_country_ids` | Countries being negotiated |
| Platform rights | `col_media_ids` | SVOD, AVOD, telco, FAST, CTV etc. |
| Commercial model | `col_commercial_model` | MG, flat fee, revenue share, hybrid or TBC |
| Scope and next steps | `col_scope_note` | Negotiation context and decisions |

Continue to use Odoo CRM's existing stage, sales owner, expected revenue,
close date, activity and quotation features. Those are already the correct
commercial controls and should not be recreated in a custom model.

## Sales process

1. Create an opportunity in the standard CRM pipeline.
2. Complete the **Content Deal** tab and use the rights availability finder.
3. Send proposal / term sheet / contract using normal CRM activities and
   attachments.
4. Create the `col.agreement` once commercial terms are agreed, then configure
   the individual title-level rights grants.
5. Create a delivery project from the opportunity or agreement.

The opportunity's existing `expected_revenue` is the forecast field. Odoo
Sales quotations and invoices are the financial documents of record.

## Delivery project

Model: `project.project`

Each delivery project holds the counterparty, originating sales opportunity,
rights agreement, content scope, territories, platform rights, target launch,
next milestone and delivery health.

Delivery health must be updated in weekly project review:

- **On track**: no decision or delivery risk outside normal monitoring.
- **Needs attention**: an owner needs to act before the next milestone.
- **Blocked**: external decision, asset or agreement issue is stopping work.

## Default launch checklist

Creating a delivery project adds these standard tasks:

1. Confirm commercial scope and title list
2. Execute agreement and set up rights grants
3. Receive and quality-check content assets
4. Prepare metadata, subtitles and localisation
5. Complete platform or telco integration
6. Complete partner acceptance testing
7. Approve and launch
8. Set reporting cadence and commercial review

Task workstreams let the team filter and assign the checklist to Commercial,
Legal and Rights, Content Assets, Localisation, Integration, Launch or
Reporting. Individual tasks include a blocked flag and blocker note.

## Installation order

1. Odoo CRM
2. Odoo Project
3. COL Content Rights & Avails (`col_rights`)
4. COL Content Rights - CRM Bridge (`col_rights_crm`)
5. COL Sales & Delivery (`col_sales_delivery`)

## Follow-on configuration

- Configure CRM stages to match COL's commercial cadence. Suggested stages:
  New, Qualified, Proposal, Term Sheet, Contracting, Won, Lost.
- Set CRM sales teams by channel or region once ownership is agreed.
- Use Odoo Sales for quotation templates and Odoo Invoicing for invoice and
  collection status.
- Assign named owners and deadlines to generated delivery tasks immediately
  after the project is created.
