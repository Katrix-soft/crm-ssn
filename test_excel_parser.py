import zipfile
import xml.etree.ElementTree as ET
import os

def parse_activities():
    file_path = "PLANILLA SEGUIMIENTO REUNION Y LLAMADOS.xlsx"
    if not os.path.exists(file_path):
        print("File not found")
        return
        
    with zipfile.ZipFile(file_path) as z:
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            with z.open('xl/sharedStrings.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for t in root.findall('.//ns:t', ns):
                    shared_strings.append(t.text if t.text else '')

        with z.open('xl/worksheets/sheet3.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            rows = root.findall('.//ns:row', ns)
            
            # Row 5 (index 4) has month names
            # Row 6 (index 5) has day numbers
            row5 = rows[4]
            row6 = rows[5]
            
            months_dict = {}
            for c in row5.findall('ns:c', ns):
                cell_ref = c.attrib.get('r')
                col_letter = ''.join([char for char in cell_ref if char.isalpha()])
                val_tag = c.find('ns:v', ns)
                val = val_tag.text if val_tag is not None else ''
                if c.attrib.get('t') == 's' and val.isdigit():
                    val = shared_strings[int(val)]
                if val.strip():
                    months_dict[col_letter] = val.strip()
                    
            def col_idx_to_letter(idx):
                letter = ''
                while idx > 0:
                    idx, remainder = divmod(idx - 1, 26)
                    letter = chr(65 + remainder) + letter
                return letter
                
            col_letters = [col_idx_to_letter(i) for i in range(8, 200)] # 8 is H
            
            col_to_month = {}
            current_month = 'ABRIL'
            for col in col_letters:
                if col in months_dict:
                    current_month = months_dict[col]
                col_to_month[col] = current_month
                
            col_to_day = {}
            for c in row6.findall('ns:c', ns):
                cell_ref = c.attrib.get('r')
                col_letter = ''.join([char for char in cell_ref if char.isalpha()])
                val_tag = c.find('ns:v', ns)
                val = val_tag.text if val_tag is not None else ''
                if c.attrib.get('t') == 's' and val.isdigit():
                    val = shared_strings[int(val)]
                if val.strip():
                    col_to_day[col_letter] = val.strip()

            month_mapping = {
                'ABRIL': '04',
                'MAYO': '05',
                'JUNIO': '06',
                'JULIO': '07',
                'AGOSTO': '08',
                'SETIEMBRE': '09'
            }

            activities = []
            for r in rows[6:]:
                r_vals = {}
                for c in r.findall('ns:c', ns):
                    cell_type = c.attrib.get('t')
                    val_tag = c.find('ns:v', ns)
                    val = val_tag.text if val_tag is not None else ''
                    if cell_type == 's' and val.isdigit():
                        val = shared_strings[int(val)]
                    col_name = ''.join([char for char in c.attrib.get('r') if char.isalpha()])
                    r_vals[col_name] = val
                    
                name = r_vals.get('B', '').strip()
                if name and name != 'Nombre Productor' and not name.startswith('Total'):
                    comp = r_vals.get('C', '').strip()
                    for col, val in r_vals.items():
                        if col in col_to_month and val in ['1', '2']:
                            m_name = col_to_month[col]
                            m_num = month_mapping.get(m_name, '01')
                            day_str = col_to_day.get(col, '01')
                            # Zero-pad day
                            if len(day_str) == 1:
                                day_str = '0' + day_str
                            date_str = f"2024-{m_num}-{day_str}"
                            act_type = 'Llamado' if val == '1' else 'Reunión'
                            activities.append({
                                'nombre': name,
                                'compania': comp,
                                'fecha': date_str,
                                'tipo': act_type
                            })
            print(f"Parsed {len(activities)} activities successfully!")
            for act in activities[:10]:
                print(act)

if __name__ == "__main__":
    parse_activities()
