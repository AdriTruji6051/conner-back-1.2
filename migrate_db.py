"""
Database migration helper: migrate records from an older sqlite database to the new project sqlite database.

This enhanced version contains explicit table and column mappings for the conner v1 -> v2 schema
so camelCase -> snake_case renames and table name differences are handled.

Behavior summary (high level):
- Uses an explicit table_mappings dict to map source tables -> destination tables and column renames.
- Where appropriate, transforms rows (e.g., ticketsProducts -> product_in_ticket handles usedPrice/isWholesale logic).
- If a mapping requests creation of a small destination table (products_family), the script will create it.
- Writes failed rows to CSV (default contains failed rows; --record-skipped includes skipped rows too).

"""

import argparse
import csv
import json
import os
import sqlite3
import sys
import logging
from typing import List, Dict, Any, Callable, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("migrate_db")


def get_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    return [row[0] for row in cur.fetchall()]


def get_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cur.fetchall()]


# Per-table transforms: accept source row dict and return dest row dict (dst column names)
def transform_tickets_products(row: Dict[str, Any]) -> Dict[str, Any]:
    # source columns: ID, ticketId, code, description, cantity, profit, paidAt, isWholesale, usedPrice
    # destination columns: id, ticket_id, code, description, cantity, profit, wholesale_price, sale_price
    mapped: Dict[str, Any] = {}
    mapped['id'] = row.get('ID')
    mapped['ticket_id'] = row.get('ticketId')
    mapped['code'] = row.get('code')
    mapped['description'] = row.get('description')
    mapped['cantity'] = row.get('cantity')
    mapped['profit'] = row.get('profit')

    used = row.get('usedPrice')
    is_wholesale = row.get('isWholesale')

    # sale_price is NOT NULL in destination, so always set it
    # If isWholesale is truthy (1/True), set wholesale_price and use it as sale_price too
    try:
        if is_wholesale is not None and float(is_wholesale):
            mapped['wholesale_price'] = used
            mapped['sale_price'] = used  # Set sale_price to same value to satisfy NOT NULL constraint
        else:
            mapped['wholesale_price'] = None
            mapped['sale_price'] = used
    except Exception:
        mapped['wholesale_price'] = None
        mapped['sale_price'] = used if used is not None else 0.0

    return mapped


def transform_products(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a destination-row dict using destination column names (snake_case).
    Also, set inventory to NULL when source inventory is present but < 1 to indicate "no inventory tracking".
    """
    mapped: Dict[str, Any] = {}

    # Direct mappings (dst names)
    mapped['code'] = row.get('code')
    mapped['description'] = row.get('description')
    mapped['cost'] = row.get('cost')
    mapped['department'] = row.get('department')
    mapped['priority'] = row.get('priority')

    # inventory: treat < 1 as NULL to indicate 'no inventory tracking'
    inv = row.get('inventory')
    if inv is None:
        mapped['inventory'] = None
    else:
        try:
            inv_val = float(inv)
            if inv_val < 1:
                mapped['inventory'] = None
            else:
                mapped['inventory'] = inv_val
        except Exception:
            # keep raw value if parsing fails
            mapped['inventory'] = row.get('inventory')

    # Renamed fields (camelCase -> snake_case)
    mapped['sale_type'] = row.get('saleType')
    mapped['sale_price'] = row.get('salePrice')
    mapped['wholesale_price'] = row.get('wholesalePrice')
    mapped['modified_at'] = row.get('modifiedAt')
    mapped['profit_margin'] = row.get('profitMargin')
    mapped['parent_code'] = row.get('parentCode')

    # familyCode from source has no direct mapped column in V2 by default; keep if present under 'familyCode'
    if 'familyCode' in row:
        mapped['familyCode'] = row.get('familyCode')

    return mapped


def transform_tickets(row: Dict[str, Any]) -> Dict[str, Any]:
    mapped = {}
    mapped['id'] = row.get('ID')
    mapped['created_at'] = row.get('createdAt')
    mapped['sub_total'] = row.get('subTotal')
    mapped['total'] = row.get('total')
    mapped['profit'] = row.get('profit')
    mapped['products_count'] = row.get('articleCount')
    mapped['notes'] = row.get('notes')
    mapped['discount'] = row.get('discount')
    # destination has user_id and ipv4_sender not present in source; set defaults
    mapped['user_id'] = 1  # Default to admin user
    mapped['ipv4_sender'] = '127.0.0.1'  # Default localhost
    return mapped


# Table mapping config
# key: source table name
# values: dict with dst_table, optional create_sql, optional transform function
TABLE_MAPPINGS: Dict[str, Dict[str, Any]] = {
    'departments': {'dst_table': 'departments', 'transform': None},
    'products': {'dst_table': 'products', 'transform': transform_products},
    'productsFamily': {
        'dst_table': 'products_family',
        'create_sql': 'CREATE TABLE IF NOT EXISTS products_family (code INTEGER PRIMARY KEY, description TEXT NOT NULL)',
        'transform': None,
    },
    'tickets': {'dst_table': 'tickets', 'transform': transform_tickets},
    'ticketsProducts': {'dst_table': 'product_in_ticket', 'transform': transform_tickets_products},
}


def migrate_table_with_mapping(src_conn: sqlite3.Connection, dst_conn: sqlite3.Connection, src_table: str, mapping: Dict[str, Any], failed_records: List[Dict[str, Any]], options) -> Dict[str, int]:
    dst_table = mapping.get('dst_table', src_table)
    create_sql = mapping.get('create_sql')
    transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = mapping.get('transform')

    if create_sql:
        try:
            dst_conn.execute(create_sql)
            dst_conn.commit()
            logger.info(f"Created/ensured destination table via create_sql: {dst_table}")
        except Exception as e:
            logger.error(f"Failed to create table {dst_table}: {e}")
            # fall through; if table missing migration will record failures

    src_cols = get_columns(src_conn, src_table)
    dst_tables = get_tables(dst_conn)
    dst_cols = get_columns(dst_conn, dst_table) if dst_table in dst_tables else []

    stats = {"total": 0, "migrated": 0, "skipped_existing": 0, "failed": 0, "table_missing": 0}

    if not dst_cols:
        # Destination table missing
        cur = src_conn.execute(f"SELECT * FROM '{src_table}'")
        rows = cur.fetchall()
        colnames = src_cols
        for r in rows:
            stats['total'] += 1
            failed_records.append({
                'table': src_table,
                'reason': 'table_missing',
                'data': dict(zip(colnames, r))
            })
            stats['table_missing'] += 1
            stats['failed'] += 1
        return stats

    # Prepare select of all source columns
    select_sql = f"SELECT {', '.join([f'"{c}"' for c in src_cols])} FROM '{src_table}'"
    src_cur = src_conn.execute(select_sql)
    rows = src_cur.fetchall()

    dst_cur = dst_conn.cursor()

    for r in rows:
        stats['total'] += 1
        row_dict = dict(zip(src_cols, r))

        try:
            if transform:
                mapped = transform(row_dict)
            else:
                # default mapping: keep columns with identical names
                mapped = {k: row_dict.get(k) for k in src_cols if k in dst_cols}

            # keep only columns that exist in destination table
            insert_cols = [c for c in mapped.keys() if c in dst_cols]
            if not insert_cols:
                stats['failed'] += 1
                failed_records.append({'table': src_table, 'reason': 'no_mapped_columns', 'data': row_dict})
                continue

            placeholders = ','.join('?' for _ in insert_cols)
            col_list = ','.join(f'"{c}"' for c in insert_cols)
            # Use UPSERT for products to ensure inventory and other fixes apply to existing rows.
            values = [mapped[c] for c in insert_cols]

            if dst_table == 'products' and 'code' in insert_cols:
                # Build ON CONFLICT upsert SQL using 'code' as the conflict target
                update_cols = [c for c in insert_cols if c != 'code']
                if update_cols:
                    assignments = ", ".join([f'"{c}"=excluded."{c}"' for c in update_cols])
                    upsert_sql = f"INSERT INTO '{dst_table}' ({col_list}) VALUES ({placeholders}) ON CONFLICT(code) DO UPDATE SET {assignments}"
                else:
                    # nothing to update; fall back to insert with ignore
                    upsert_sql = f"INSERT OR IGNORE INTO '{dst_table}' ({col_list}) VALUES ({placeholders})"
                try:
                    dst_cur.execute(upsert_sql, values)
                    # count as migrated whether it was an insert or update
                    stats['migrated'] += 1
                except sqlite3.IntegrityError as ie:
                    msg = str(ie)
                    if 'UNIQUE constraint failed' in msg or 'PRIMARY KEY' in msg:
                        stats['skipped_existing'] += 1
                        if options.record_skipped:
                            failed_records.append({'table': src_table, 'reason': 'skipped_existing', 'data': row_dict, 'error': msg})
                    else:
                        stats['failed'] += 1
                        failed_records.append({'table': src_table, 'reason': 'integrity_error', 'data': row_dict, 'error': msg})
                except Exception as e:
                    stats['failed'] += 1
                    failed_records.append({'table': src_table, 'reason': 'error', 'data': row_dict, 'error': str(e)})
            else:
                insert_sql = f"INSERT INTO '{dst_table}' ({col_list}) VALUES ({placeholders})"
                try:
                    dst_cur.execute(insert_sql, values)
                    stats['migrated'] += 1
                except sqlite3.IntegrityError as ie:
                    msg = str(ie)
                    if 'UNIQUE constraint failed' in msg or 'PRIMARY KEY' in msg:
                        stats['skipped_existing'] += 1
                        if options.record_skipped:
                            failed_records.append({'table': src_table, 'reason': 'skipped_existing', 'data': row_dict, 'error': msg})
                    else:
                        stats['failed'] += 1
                        failed_records.append({'table': src_table, 'reason': 'integrity_error', 'data': row_dict, 'error': msg})
                except Exception as e:
                    stats['failed'] += 1
                    failed_records.append({'table': src_table, 'reason': 'error', 'data': row_dict, 'error': str(e)})
        except sqlite3.IntegrityError as ie:
            msg = str(ie)
            if 'UNIQUE constraint failed' in msg or 'PRIMARY KEY' in msg:
                stats['skipped_existing'] += 1
                if options.record_skipped:
                    failed_records.append({'table': src_table, 'reason': 'skipped_existing', 'data': row_dict, 'error': msg})
            else:
                stats['failed'] += 1
                failed_records.append({'table': src_table, 'reason': 'integrity_error', 'data': row_dict, 'error': msg})
        except Exception as e:
            stats['failed'] += 1
            failed_records.append({'table': src_table, 'reason': 'error', 'data': row_dict, 'error': str(e)})

    dst_conn.commit()
    return stats


def write_failed_csv(path: str, failed_records: List[Dict[str, Any]]):
    if not failed_records:
        logger.info('No failed records to write to CSV.')
        return

    fieldnames = ['table', 'reason', 'data_json', 'error']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in failed_records:
            writer.writerow({
                'table': rec.get('table'),
                'reason': rec.get('reason'),
                'data_json': json.dumps(rec.get('data', {}), default=str, ensure_ascii=False),
                'error': rec.get('error', '')
            })

    logger.info(f'Wrote failed records CSV to: {path}')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Migrate sqlite records from a source DB to destination DB')
    parser.add_argument('--src', default=r'C:\\Users\\SrPap\\Documents\\GitHub\\conner-back\\db',
                        help='Source sqlite database file or directory containing sqlite files')
    parser.add_argument('--dst', default=r'C:\\Users\\SrPap\\Documents\\GitHub\\conner.1.2\\conner-back-1.2\\db',
                        help='Destination sqlite database file or directory (can be a file path or directory)')
    parser.add_argument('--failed-csv', default='migration_failed_records.csv', help='CSV path to write failed records')
    parser.add_argument('--record-skipped', action='store_true', dest='record_skipped',
                        help='Also record skipped_existing rows into the failed CSV (they are counted separately in summary)')
    parser.add_argument('--disable-fk', action='store_true', dest='disable_fk',
                        help='Disable foreign key enforcement in destination during migration (use with caution)')

    options = parser.parse_args(argv)

    def resolve_db_path(p: str) -> str:
        if os.path.isdir(p):
            for candidate in ['data_base.db', 'database.db', 'db.sqlite', 'db.sqlite3', 'db', 'conner.db']:
                c = os.path.join(p, candidate)
                if os.path.isfile(c):
                    return c
            db_files = [os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith('.db')]
            if len(db_files) == 1:
                return db_files[0]
            raise SystemExit(f'Directory {p} contains multiple or no .db files; please provide a file path.')
        return p

    src_db = resolve_db_path(options.src)
    dst_db = resolve_db_path(options.dst)

    logger.info(f'Source DB: {src_db}')
    logger.info(f'Destination DB: {dst_db}')

    if not os.path.isfile(src_db):
        logger.error(f'Source DB file not found: {src_db}')
        sys.exit(2)
    if not os.path.isfile(dst_db):
        logger.error(f'Destination DB file not found: {dst_db}')
        sys.exit(2)

    src_conn = sqlite3.connect(src_db)
    dst_conn = sqlite3.connect(dst_db)

    try:
        if options.disable_fk:
            dst_conn.execute('PRAGMA foreign_keys = OFF')
            logger.info('Foreign key enforcement disabled on destination DB for migration')

        src_tables = get_tables(src_conn)
        dst_tables = get_tables(dst_conn)

        logger.info(f'Found {len(src_tables)} tables in source and {len(dst_tables)} in destination')

        overall = {'total': 0, 'migrated': 0, 'skipped_existing': 0, 'failed': 0}
        per_table_stats = {}
        failed_records: List[Dict[str, Any]] = []

        for t in src_tables:
            logger.info(f'Migrating source table: {t}')
            if t in TABLE_MAPPINGS:
                stats = migrate_table_with_mapping(src_conn, dst_conn, t, TABLE_MAPPINGS[t], failed_records, options)
            else:
                # fallback to best-effort intersection strategy
                stats = migrate_table(src_conn, dst_conn, t, failed_records, options)

            per_table_stats[t] = stats
            for k in overall:
                overall[k] += stats.get(k, 0)

            logger.info(f"Table {t} stats: total={stats['total']}, migrated={stats['migrated']}, skipped_existing={stats['skipped_existing']}, failed={stats['failed']}")

        # Write failed records CSV
        write_failed_csv(options.failed_csv, failed_records)

        # Print summary
        logger.info('\n=== MIGRATION SUMMARY ===')
        logger.info(f"Tables processed: {len(src_tables)}")
        logger.info(f"Total rows: {overall['total']}")
        logger.info(f"Migrated: {overall['migrated']}")
        logger.info(f"Skipped (existing): {overall['skipped_existing']}")
        logger.info(f"Failed: {overall['failed']}")

        success_rate = (overall['migrated'] / overall['total'] * 100) if overall['total'] > 0 else 0.0
        logger.info(f"Success rate: {success_rate:.2f}%")

        logger.info('\nPer-table summary:')
        for t, s in per_table_stats.items():
            logger.info(f" - {t}: total={s['total']}, migrated={s['migrated']}, skipped={s['skipped_existing']}, failed={s['failed']}")

    finally:
        src_conn.close()
        dst_conn.close()


if __name__ == '__main__':
    main()
