# Migration README — conner-back -> conner-back-1.2

## Purpose

This document explains which tables (and columns) will be migrated from the original conner-back database (source) to the new V2 database used by conner-back-1.2 using `migrate_db.py`.

## Migration Script Overview

The migration script (`migrate_db.py`) includes:
- **Explicit table and column mappings** for handling schema changes (camelCase → snake_case renames)
- **Custom transformation functions** for complex data conversions
- **Automatic table creation** for new destination tables (e.g., `products_family`)
- **UPSERT support** for products table to handle existing records
- **Comprehensive error logging** with CSV output for failed/skipped records

## Table-Level Mapping

### 1. departments → departments
**Source columns:** `code` (INTEGER, pk), `description` (TEXT)  
**Destination columns:** `code` (INTEGER, pk), `description` (TEXT)  
**Migration:** Direct mapping; column names match exactly.

### 2. products → products
**Source columns:** `code`, `description`, `saleType`, `cost`, `salePrice`, `department`, `wholesalePrice`, `priority`, `inventory`, `modifiedAt`, `profitMargin`, `parentCode`, `familyCode`

**Destination columns:** `code`, `description`, `sale_type`, `cost`, `sale_price`, `department`, `wholesale_price`, `priority`, `inventory`, `modified_at`, `profit_margin`, `parent_code`

**Changes handled by migration script:**
- ✅ Column renames: `saleType` → `sale_type`, `salePrice` → `sale_price`, `wholesalePrice` → `wholesale_price`, `modifiedAt` → `modified_at`, `profitMargin` → `profit_margin`, `parentCode` → `parent_code`
- ✅ Inventory normalization: Values < 1 are set to NULL (indicating no inventory tracking)
- ✅ UPSERT logic: Existing products are updated rather than skipped
- ⚠️ `familyCode` has no direct destination column (legacy field, not migrated)

### 3. productsFamily → products_family
**Source:** `productsFamily` (`code` INTEGER pk, `description` TEXT)  
**Destination:** `products_family` (auto-created by migration script)  
**Migration:** The script automatically creates the `products_family` table if it doesn't exist.

### 4. tickets → tickets
**Source columns:** `ID`, `createdAt`, `subTotal`, `total`, `profit`, `articleCount`, `notes`, `discount`

**Destination columns:** `id`, `created_at`, `modified_at`, `sub_total`, `total`, `profit`, `products_count`, `notes`, `user_id`, `ipv4_sender`, `discount`

**Changes handled by migration script:**
- ✅ Column renames: `ID` → `id`, `createdAt` → `created_at`, `subTotal` → `sub_total`, `articleCount` → `products_count`
- ✅ Default values: `user_id` = 1 (admin), `ipv4_sender` = '127.0.0.1', `modified_at` = NULL

### 5. ticketsProducts → product_in_ticket
**Source columns:** `ID`, `ticketId`, `code`, `description`, `cantity`, `profit`, `paidAt`, `isWholesale`, `usedPrice`

**Destination columns:** `id`, `ticket_id`, `code`, `description`, `cantity`, `profit`, `wholesale_price`, `sale_price`

**Changes handled by migration script:**
- ✅ Column renames: `ID` → `id`, `ticketId` → `ticket_id`
- ✅ Price logic: If `isWholesale` is true, both `wholesale_price` and `sale_price` are set to `usedPrice`; otherwise only `sale_price` is set
- ⚠️ `paidAt` field is not migrated (no equivalent in destination)

## Destination-Only Tables

The following tables exist in the destination database but have no source equivalent. They will remain empty after migration:
- `associates_codes`
- `cash_flow`
- `drawer_logs`
- `inventory_log`
- `products_changes`
- `ticket_font_configs`
- `ticket_text`
- `users`

## Running the Migration

### Prerequisites
1. **Backup both databases** before running migration
2. Ensure Python 3.8+ is installed
3. Install required dependencies (if any)

### Basic Usage

```bash
# From the conner-back-1.2 directory
python migrate_db.py --src "/path/to/source/database.db" --dst "/path/to/destination/conner.db" --failed-csv "migration_failed_records.csv"
```

### Command-Line Options

- `--src`: Path to source database file or directory containing the database
- `--dst`: Path to destination database file or directory
- `--failed-csv`: Path for CSV file containing failed/skipped records (default: `migration_failed_records.csv`)
- `--record-skipped`: Include skipped records (due to existing primary keys) in the CSV output
- `--disable-fk`: Temporarily disable foreign key enforcement during migration (use with caution)

### Example with All Options

```bash
python migrate_db.py \
  --src "/path/to/old/conner-back/db" \
  --dst "/path/to/new/conner-back-1.2/db" \
  --failed-csv "migration_results.csv" \
  --record-skipped
```

### Example Output

```
2026-07-06 16:47:08,559 INFO: Found 5 tables in source and 14 in destination
2026-07-06 16:47:08,562 INFO: Table departments stats: total=20, migrated=20, skipped_existing=0, failed=0
2026-07-06 16:47:08,626 INFO: Table products stats: total=2659, migrated=2659, skipped_existing=0, failed=0
2026-07-06 16:47:09,466 INFO: Table tickets stats: total=55255, migrated=55252, skipped_existing=3, failed=0
2026-07-06 16:47:12,773 INFO: Table ticketsProducts stats: total=249380, migrated=249375, skipped_existing=5, failed=0

=== MIGRATION SUMMARY ===
Tables processed: 5
Total rows: 307314
Migrated: 307306
Skipped (existing): 8
Failed: 0
Success rate: 100.00%
```

## Post-Migration Verification

After running the migration, verify the results:

1. **Check migration summary** in console output for success rate
2. **Review failed records CSV** for any issues
3. **Run verification scripts:**
   ```bash
   python db_inspect.py          # Inspect database structure and counts
   python verify_migration.py    # Verify data integrity
   python check_family_codes.py  # Check product relationships
   ```

4. **Test the application** with migrated data

## Important Notes

- The migration script uses **UPSERT** for products, so running it multiple times will update existing records
- For other tables, duplicate primary keys will be **skipped** (not overwritten)
- The script handles **camelCase → snake_case** conversions automatically
- **Foreign key constraints** are respected by default (use `--disable-fk` only if necessary)
- The `products_family` table is **auto-created** if it doesn't exist
- **Inventory values < 1** are normalized to NULL (indicating no tracking)

## Troubleshooting

### Migration fails with "table not found"
- Verify both database paths are correct
- Ensure destination database has been initialized with the correct schema

### High number of skipped records
- This is normal if re-running migration on a database that already has data
- Use `--record-skipped` to see which records were skipped

### Foreign key constraint errors
- Ensure related tables are migrated in the correct order (the script handles this automatically)
- Consider using `--disable-fk` temporarily if issues persist

### Performance issues with large databases
- The script processes records in batches
- For very large databases (>1M records), consider running in background
- Monitor disk space and memory usage

## Schema Differences Summary

| Aspect | Source (v1) | Destination (v2) |
|--------|-------------|------------------|
| Naming Convention | camelCase | snake_case |
| Products Family | Separate table | Integrated (auto-created) |
| Ticket User Tracking | Not present | Added (user_id, ipv4_sender) |
| Inventory Tracking | Numeric values | NULL for untracked items |
| Price Fields | Single usedPrice | Separate wholesale_price, sale_price |

## Author

- [@adriandDev](https://www.github.com/adritruji6051)
