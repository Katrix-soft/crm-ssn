import sys
import os

sys.path.append("api-crm")
import ssn_test as db

# Initialize parent database
db.DB_PATH = "/home/nachin/Documentos/katrix/productor de seguros/data/productores_scraped.db"
print("Initializing parent database at:", db.DB_PATH)
db.inicializar_db()

# Initialize local database
db.DB_PATH = "/home/nachin/Documentos/katrix/productor de seguros/api-crm/data/productores_scraped.db"
print("Initializing local database at:", db.DB_PATH)
db.inicializar_db()

print("Both databases initialized successfully.")
