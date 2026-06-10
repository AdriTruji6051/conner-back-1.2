import os
import sys
import sqlite3
import json


def resolve_db_path(p):
    if os.path.isdir(p):
        for candidate in ["data_base.db", "database.db", "db.sqlite", "db.sqlite3", "db"]:
            c = os.path.join(p, candidate)
            if os.path.isfile(c):
                return c
        db_files = [os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith('.db')]
        if len(db_files) == 1:
            return db_files[0]
        raise SystemExit(f"Directory {p} contains multiple or no .db files; pass a file path instead.")
    return p


def inspect_db(path):
    path = resolve_db_path(path)
    if not os.path.isfile(path):
        raise SystemExit(f"DB file not found: {path}")
    conn = sqlite3.connect(path)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    out = {"db": path, "tables": {}}
    for t in tables:
        cols_cur = conn.execute(f"PRAGMA table_info('{t}')")
        cols = []
        for r in cols_cur.fetchall():
            cols.append({"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3], "dflt_value": r[4], "pk": r[5]})
        out["tables"][t] = {"columns": cols}
    conn.close()
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: db_inspect.py <db-file-or-dir>")
        sys.exit(2)
    inspect_db(sys.argv[1])