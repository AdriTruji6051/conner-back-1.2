Migration README — conner-back -> conner-back-1.2

Purpose

This document explains which tables (and columns) will be migrated from the original conner-back database (source)
located at C:\Users\SrPap\Documents\GitHub\conner-back\db\data_base.db to the new V2 database used by
conner.1.2 at C:\Users\SrPap\Documents\GitHub\conner.1.2\conner-back-1.2\db\conner.db using migrate_db.py.

Note about the current migration script

- The provided script copies rows only for columns that have identical names in source and destination tables (intersection of column names).
- Columns that were renamed (camelCase -> snake_case, or different names) will NOT be migrated unless the destination uses the same column name.
- If a source table has no matching table in the destination, all rows from that table are recorded as failed (reason: table_missing) and written to the failed CSV.

Table-level mapping (what will be moved and what will be lost or needs manual mapping)

1) departments -> departments
- Source columns: code (INTEGER, pk), description (TEXT)
- Destination columns: code (INTEGER, pk), description (TEXT)
- Migration: Direct; column names match. Expected to migrate without change.

2) products -> products
- Source columns: code, description, saleType, cost, salePrice, department, wholesalePrice, priority, inventory, modifiedAt, profitMargin, parentCode, familyCode
- Destination columns: code, description, sale_type, cost, sale_price, department, wholesale_price, priority, inventory, modified_at, profit_margin, parent_code
- Notes / changes:
  - Several column names were renamed from camelCase (saleType, salePrice, wholesalePrice, modifiedAt, profitMargin, parentCode) to snake_case in destination (sale_type, sale_price, wholesale_price, modified_at, profit_margin, parent_code). The current script will NOT move these renamed columns because it only copies identically-named columns. Only columns with exact name matches (code, description, cost, department, priority, inventory) will be migrated.
  - familyCode has no direct column in destination; the productsFamily table in the source has no direct equivalent in destination. familyCode and productsFamily data will NOT be migrated by the script; consider adding a destination table or mapping familyCode into an existing field before running migration.

3) productsFamily -> (no equivalent)
- Source: productsFamily (code INTEGER pk, description TEXT)
- Destination: no matching table found.
- Action: Records from this table are treated as failures (table_missing). If you need this data in V2, add a destination table (e.g., products_family) or export/import as a separate CSV and re-create in the new schema.

4) tickets -> tickets
- Source columns: ID (INTEGER pk), createdAt, subTotal, total, profit, articleCount, notes, discount
- Destination columns: id (INTEGER pk), created_at, modified_at, sub_total, total, profit, products_count, notes, user_id, ipv4_sender, discount
- Notes / changes:
  - Several renamed columns: ID -> id, createdAt -> created_at, subTotal -> sub_total, articleCount -> products_count. The current script will NOT move renamed columns unless names match.
  - Destination has additional columns (modified_at, user_id, ipv4_sender) which are not present in source; those will remain NULL or default.

5) ticketsProducts -> product_in_ticket
- Source columns: ID (pk), ticketId, code, description, cantity, profit, paidAt, isWholesale, usedPrice
- Destination columns: id (pk), ticket_id, code, description, cantity, profit, wholesale_price, sale_price
- Notes / changes:
  - Column renames: ticketId -> ticket_id, usedPrice -> sale_price. paidAt and isWholesale do not have direct equivalents; wholesale_price exists in destination but mapping from isWholesale may require custom logic (boolean -> price or flag) and thus is not automatically migrated.
  - The current script will only copy columns with identical names (code, description, cantity, profit) and will skip renamed columns unless the script is extended with explicit column mappings.

Tables present in destination but not in source (no-op for migration)

- associates_codes, cash_flow, drawer_logs, inventory_log, products_changes, product_in_ticket (target for ticketsProducts), ticket_font_configs, ticket_text, users, and others.
- These destination-only tables will be left unchanged; some (product_in_ticket) will receive migrated rows (where column names match or after mapping adjustments).

Recommendations / next steps

- Update the migration script to include a mapping dictionary for known renamed columns (camelCase -> snake_case). Example mapping for products:
  {"saleType": "sale_type", "salePrice": "sale_price", "wholesalePrice": "wholesale_price", "modifiedAt": "modified_at", "profitMargin": "profit_margin", "parentCode": "parent_code"}
- Add a mapping for the tickets/ticketsProducts renames as well (ID->id, createdAt->created_at, subTotal->sub_total, articleCount->products_count, ticketId->ticket_id, usedPrice->sale_price).
- Decide how to handle productsFamily -> new schema (create a products_family table or map familyCode to an existing column).
- Backup both source and destination DBs before running any migration and test on a copy first.
- Use the migration script flags:
  - --record-skipped to also record rows skipped due to existing primary/unique keys
  - --disable-fk to temporarily disable foreign key enforcement on the destination while running the migration (use with caution)

Running the current script

Example (from project root):
  python conner-back-1.2\migrate_db.py --src "C:\\Users\\SrPap\\Documents\\GitHub\\conner-back\\db" --dst "C:\\Users\\SrPap\\Documents\\GitHub\\conner.1.2\\conner-back-1.2\\db" --failed-csv migration_failed_records.csv --record-skipped

This will write migration_failed_records.csv containing failed rows (default) and, with --record-skipped, also rows that were skipped because they already existed in the destination.

If you want, I can update migrate_db.py now to implement the recommended column-name mappings and to auto-create a small products_family table in the destination (or export productsFamily to a separate CSV). Which behavior should I implement?