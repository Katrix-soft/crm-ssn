import sqlite3
conn = sqlite3.connect("productores_scraped.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM productores_detalle LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    print(dict(r))
conn.close()
