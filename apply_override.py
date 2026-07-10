import sqlite3, openpyxl, os, re

ROOT = r"D:\AI+\羽智选  BadmintonGear AI 羽毛球装备智能导购"
db = os.path.join(ROOT, "server", "dev.db")
xlsx = os.path.join(ROOT, "知识库", "badminton_kb_final_v4_avg_price", "商品库与知识库平均价覆盖_v4.xlsx")

def norm(s):
    return re.sub(r'\s+', ' ', (s or '').upper()).strip()

# ---- build excel map: norm(raw_name) -> (raw_name, price_float|None) ----
wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
ws = wb["商品库最终版"]
rows = list(ws.iter_rows(values_only=True))
header = list(rows[0]); H = {h: i for i, h in enumerate(header)}
excel_map = {}
conflicts = 0
for r in rows[1:]:
    raw = r[H["raw_name"]]
    ref = r[H["reference_price"]]
    k = norm(raw)
    if not k:
        continue
    price = None
    if ref is not None:
        try:
            price = float(str(ref).strip())
        except Exception:
            price = None
    if k in excel_map:
        conflicts += 1
        continue
    excel_map[k] = (raw, price)

conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT id, name, price FROM t_product WHERE category_id=1")
db_rows = cur.fetchall()

updated_name = 0
name_changed = 0
price_updated = 0
skipped_no_match = 0
skipped_price_bad = 0

for did, dname, dprice in db_rows:
    k = norm(dname)
    if k not in excel_map:
        skipped_no_match += 1
        continue
    ex_raw, ex_price = excel_map[k]
    updated_name += 1
    # name: only write when actually different
    if ex_raw is not None and ex_raw != dname:
        cur.execute("UPDATE t_product SET name=? WHERE id=?", (ex_raw, did))
        name_changed += 1
    # price: only write when valid and different
    if ex_price is not None:
        try:
            if dprice is None or abs(float(dprice) - ex_price) > 1e-6:
                cur.execute("UPDATE t_product SET price=? WHERE id=?", (ex_price, did))
                price_updated += 1
        except Exception:
            skipped_price_bad += 1
    else:
        skipped_price_bad += 1

conn.commit()
conn.close()

print("excel map size:", len(excel_map), "| raw_name conflicts(ignored):", conflicts)
print("db racket rows:", len(db_rows))
print("matched (name will be covered):", updated_name)
print("name actually changed (norm-equal but raw differs):", name_changed)
print("price updated:", price_updated)
print("skipped (no excel match):", skipped_no_match)
print("skipped price (invalid/empty in excel):", skipped_price_bad)
