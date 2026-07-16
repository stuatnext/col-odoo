# COL Odoo Import Folder

This folder is mounted into the Odoo container at:

```text
/mnt/import
```

Use it for import-ready files such as:

- `COL Master Catalog (consolidated).csv`
- `COL Rights & Avails Model.xlsx`

In Odoo, install the COL modules first, then use the standard import flow:

1. Open **Content Rights > Catalogue > Titles**.
2. Choose **Import records**.
3. Upload the catalogue CSV from this folder.
4. Map the title fields into `col.title`.
