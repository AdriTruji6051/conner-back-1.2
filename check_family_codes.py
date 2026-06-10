import sqlite3, os
src=r"C:\Users\SrPap\Documents\GitHub\conner-back\db\data_base.db"
conn=sqlite3.connect(src)
cur=conn.cursor()
cur.execute("SELECT COUNT(1) FROM products WHERE familyCode IS NOT NULL AND familyCode != ''")
print('familyCode non-null count:', cur.fetchone()[0])
cur.execute("SELECT familyCode, COUNT(1) FROM products WHERE familyCode IS NOT NULL AND familyCode != '' GROUP BY familyCode ORDER BY COUNT(1) DESC LIMIT 50")
for r in cur.fetchall():
    print(r)
conn.close()
