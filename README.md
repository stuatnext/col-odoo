# COL Odoo Platform

Odoo 17 platform for COL Group International / FlareFlow content licensing.
It combines three operational layers:

- **Content Rights & Avails**: catalogue, title-level rights grants,
  availability searches and exclusivity conflict detection.
- **Sales Pipeline**: Odoo CRM opportunities linked to titles, territory,
  platform rights and commercial model.
- **Delivery Projects**: a cross-functional launch tracker linked to the
  opportunity and rights agreement.

## Repository layout

| Path | Purpose |
|---|---|
| `col_rights/` | Core catalogue, rights and avails add-on |
| `col_rights_crm/` | CRM-to-agreement bridge |
| `col_sales_delivery/` | COL sales pipeline and delivery tracker |
| `odoo/` | Local Odoo configuration and import mount point |
| `docs/` | Build specifications and team operating guide |
| `data/` | Local-only data import guidance; commercial data is excluded |

## Local launch

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Run `Launch COL Odoo.bat` on Windows, or run `docker compose up -d`.
3. Open `http://localhost:8069` and create a database.
4. In **Apps**, update the apps list and install in this order:
   **CRM**, **Project**, **COL Content Rights & Avails**, **COL Content Rights
   - CRM Bridge**, **COL Sales & Delivery**.

The local development master password in `odoo/config/odoo.conf` is a
placeholder. Change it before any shared, hosted or production deployment.

## Operating flow

1. Create a commercial opportunity and complete its **Content Deal** tab.
2. Check availability before offering titles.
3. Record the agreement and rights grants when commercial terms are agreed.
4. Create the linked delivery project and assign the generated launch tasks.
5. Use Odoo Sales and Invoicing for formal quotations, invoicing and
   collections.

See the [team operating guide](docs/COL%20Team%20Operating%20Guide.md) and
[sales and delivery build spec](docs/COL%20Sales%20%26%20Delivery%20-%20Build%20Spec.md).
For a browser-ready team presentation, open the
[COL Team Walkthrough](docs/COL%20Team%20Walkthrough.html).
For a clickable visual product mock-up, open the
[COL Odoo Mock-up](docs/COL%20Odoo%20Mockup.html).

## Validation status

The platform includes Odoo test scaffolding but has not yet been run on a live
Odoo 17 installation. The first engineering milestone is to install all three
modules, run the rights conflict tests and then run the sales-delivery tests.
