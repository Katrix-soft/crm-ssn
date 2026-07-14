import sqlite3

for db_path in [
    "/home/nachin/Documentos/katrix/productor de seguros/data/productores_scraped.db",
    "/home/nachin/Documentos/katrix/productor de seguros/api-crm/data/productores_scraped.db"
]:
    print("Checking database:", db_path)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licencias")
        rows = cursor.fetchall()
        print("Licenses:")
        for r in rows:
            print(dict(r))
        conn.close()
    except Exception as e:
        print("Error:", e)
