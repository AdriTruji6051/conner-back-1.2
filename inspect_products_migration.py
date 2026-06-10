import sqlite3
import os

src = r"C:\Users\SrPap\Documents\GitHub\conner-back\db\data_base.db"
dst = r"C:\Users\SrPap\Documents\GitHub\conner.1.2\conner-back-1.2\db\conner.db"

if not os.path.isfile(src) or not os.path.isfile(dst):
    print('Source or destination DB missing')
    raise SystemExit(1)

s = sqlite3.connect(src)
d = sqlite3.connect(dst)
sc = s.cursor()
dc = d.cursor()

# counts
sc.execute("SELECT COUNT(1) FROM products")
src_count = sc.fetchone()[0]
dc.execute("SELECT COUNT(1) FROM products")
dst_count = dc.fetchone()[0]
print(f"products: source={src_count}, dest={dst_count}")

# check columns mapping presence
sc.execute("PRAGMA table_info('products')")
scols = [r[1] for r in sc.fetchall()]
dc.execute("PRAGMA table_info('products')")
dcols = [r[1] for r in dc.fetchall()]
print('source columns:', scols)
print('dest columns:', dcols)

# count rows where key mapped fields differ or nulls
checks = [
    ("saleType","sale_type"),
    ("salePrice","sale_price"),
    ("wholesalePrice","wholesale_price"),
    ("modifiedAt","modified_at"),
    ("profitMargin","profit_margin"),
    ("parentCode","parent_code"),
]
for scn, dcn in checks:
    if scn in scols and dcn in dcols:
        sc.execute(f"SELECT COUNT(1) FROM products WHERE {scn} IS NULL")
        s_null = sc.fetchone()[0]
        dc.execute(f"SELECT COUNT(1) FROM products WHERE {dcn} IS NULL")
        d_null = dc.fetchone()[0]
        print(f"Nulls {scn}->{dcn}: source_null={s_null}, dest_null={d_null}")
    else:
        print(f"Skipping check for {scn}->{dcn} because one side missing")

# sample mismatches for code-level
sc.execute("SELECT code, salePrice, saleType, wholesalePrice FROM products LIMIT 5")
rows = sc.fetchall()
print('\nsource sample:\n', rows)

dc.execute("SELECT code, sale_price, sale_type, wholesale_price FROM products LIMIT 5")
rows2 = dc.fetchall()
print('\ndest sample:\n', rows2)

s.close()
d.close()
