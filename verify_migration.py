import sqlite3

conn = sqlite3.connect('db/conner.db')

print('=== MIGRATION VERIFICATION ===\n')

cur = conn.execute('SELECT COUNT(*) FROM products')
print(f'Total products: {cur.fetchone()[0]}')

cur = conn.execute('SELECT COUNT(*) FROM tickets')
print(f'Total tickets: {cur.fetchone()[0]}')

cur = conn.execute('SELECT COUNT(*) FROM product_in_ticket')
print(f'Total product_in_ticket records: {cur.fetchone()[0]}')

print('\n=== SAMPLE MIGRATED DATA ===')

cur = conn.execute('SELECT id, created_at, total, user_id FROM tickets ORDER BY id LIMIT 3')
print('\nFirst 3 tickets:')
for r in cur.fetchall():
    print(f'  ID: {r[0]}, Date: {r[1]}, Total: ${r[2]}, User: {r[3]}')

cur = conn.execute('SELECT code, description, sale_price, inventory FROM products WHERE code IN ("CONT", "25046020652", "724609301251")')
print('\nSample products:')
for r in cur.fetchall():
    desc = r[1][:30] + '...' if len(r[1]) > 30 else r[1]
    print(f'  Code: {r[0]}, Desc: {desc}, Price: ${r[2]}, Inv: {r[3]}')

cur = conn.execute('SELECT id, ticket_id, code, description, sale_price, wholesale_price FROM product_in_ticket ORDER BY id LIMIT 5')
print('\nFirst 5 product_in_ticket records:')
for r in cur.fetchall():
    desc = r[3][:25] + '...' if len(r[3]) > 25 else r[3]
    print(f'  ID: {r[0]}, Ticket: {r[1]}, Code: {r[2]}, Desc: {desc}, Sale: ${r[4]}, Wholesale: ${r[5]}')

conn.close()
