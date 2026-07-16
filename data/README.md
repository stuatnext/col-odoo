# Data boundary

The public repository deliberately excludes COL's working catalogue exports,
deal trackers, contract documents and rights workbooks.

For a local or hosted deployment, place approved import files in
`odoo/import/`. The folder is mounted in the Odoo container at `/mnt/import`.

Before importing production data:

1. Confirm that every title has a stable title ID and English display title.
2. Import the catalogue into **Rights > Titles**.
3. Create or validate genres, languages and platform types.
4. Import agreements and title-level rights grants only after business review.
5. Re-run the Avails Finder and review any conflict flags.

Do not commit partner contracts, invoices, personally identifiable contact
data, commercial terms or rights data to this public repository.
