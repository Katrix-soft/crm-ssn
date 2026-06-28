import sqlite3
import os
import zipfile
import xml.etree.ElementTree as ET
from ssn_test import DB_PATH, inicializar_db, guardar_en_db

def importar_datos_completos(excel_path):
    print("Inicializando base de datos...")
    inicializar_db()
    
    print(f"Abriendo {excel_path}...")
    if not os.path.exists(excel_path):
        print(f"Error: No se encontró el archivo {excel_path}")
        return
        
    try:
        with zipfile.ZipFile(excel_path, 'r') as z:
            names = z.namelist()
            
            # Cargar shared strings
            shared_strings = []
            if "xl/sharedStrings.xml" in names:
                print("Cargando cadenas compartidas...")
                with z.open("xl/sharedStrings.xml") as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    for t in root.findall('.//ns:t', ns):
                        shared_strings.append(t.text)
                print(f"Leídas {len(shared_strings)} cadenas compartidas.")
            
            # Leer sheet1.xml (el listado completo de PAS)
            if "xl/worksheets/sheet1.xml" not in names:
                print("Error: No se encontró xl/worksheets/sheet1.xml en el archivo Excel.")
                return
                
            print("Procesando la hoja de datos (sheet1.xml)...")
            with z.open("xl/worksheets/sheet1.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                rows = root.findall('.//ns:row', ns)
                
                print(f"Total de filas encontradas: {len(rows)}")
                
                # Abrir conexión SQLite y usar una única transacción
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                registros_insertados = 0
                
                # Omitir el encabezado (fila 1)
                for r in rows[1:]:
                    cells = r.findall('ns:c', ns)
                    row_data = {}
                    for c in cells:
                        cell_ref = c.attrib.get('r')
                        col_letter = ''.join([char for char in cell_ref if char.isalpha()])
                        cell_type = c.attrib.get('t')
                        val_tag = c.find('ns:v', ns)
                        val = val_tag.text if val_tag is not None else ""
                        
                        if cell_type == 's' and val.isdigit():
                            idx = int(val)
                            if idx < len(shared_strings):
                                val = shared_strings[idx]
                                
                        row_data[col_letter] = val.strip() if val else ""
                    
                    matricula = row_data.get('A', '')
                    if matricula:
                        provincia = row_data.get('H', '').strip().upper() or "—"
                        localidad = row_data.get('G', '').strip().upper() or "—"
                        
                        # Guardar usando una consulta directa en la conexión compartida
                        cursor.execute("""
                            INSERT OR REPLACE INTO productores_detalle (
                                matricula, nombre, documento, cuit, ramo, provincia, telefono, email, 
                                resolucion, fecha_resolucion, domicilio, localidad, cod_postal, scraped_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            matricula,
                            row_data.get('B', '').strip(),
                            row_data.get('C', '').strip(),
                            row_data.get('D', '').strip(),
                            row_data.get('E', '').strip(),
                            provincia,
                            row_data.get('I', '').strip(),
                            row_data.get('J', '').strip(),
                            "Excel Import",
                            "—",
                            row_data.get('F', '').strip(),
                            localidad,
                            row_data.get('K', '').strip()
                        ))
                        registros_insertados += 1
                        
                conn.commit()
                conn.close()
                print(f"\n¡Importación completada! Se insertaron/actualizaron {registros_insertados} productores.")
                
    except Exception as e:
        print(f"Error durante la importación: {e}")

if __name__ == "__main__":
    importar_datos_completos("BASE DATOS PAS DESDE MAT 77713 al 88367.xlsm")
