#!/bin/bash
echo -e "\033[1;36m📡 Monitoreando en vivo el enriquecimiento de CUITs Dateas...\033[0m\n"
tail -n 30 -f dateas_enrich.log | python3 -u -c '
import sys, re
for line in sys.stdin:
    if "📌 Quedan" in line or "terminado" in line:
        # Destacar en Naranja/Amarillo Neón la cantidad de pendientes
        line = re.sub(r"(📌 Quedan \d+ productores pendientes\.)", r"\033[1;38;5;208m\1\033[0m", line)
        line = re.sub(r"(⏳ Lote #\d+ terminado.*?\))", r"\033[1;38;5;51m\1\033[0m", line)
        line = f"{line.rstrip()}\n"
    elif "✓" in line:
        line = f"\033[1;38;5;46m{line.rstrip()}\033[0m\n"
    elif "⚡" in line:
        line = f"\033[1;38;5;226m{line.rstrip()}\033[0m\n"
    elif "Sin coincidencia" in line:
        line = f"\033[38;5;244m{line.rstrip()}\033[0m\n"
    elif "Lote #" in line:
        line = f"\033[1;38;5;201m{line.rstrip()}\033[0m\n"
    print(line, end="", flush=True)
'
