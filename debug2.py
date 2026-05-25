import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from services.agente_validacion import PROMPT_VALIDACION

tipo = "Auxilio Especial"
tipo_limpio = tipo.encode("ascii", "ignore").decode("ascii")
prompt_final = PROMPT_VALIDACION + f"\n\nTipo de auxilio seleccionado: {tipo_limpio}. Verifica que coincida con el formulario."

# Buscar en el prompt
for i, ch in enumerate(prompt_final):
    if ord(ch) > 127:
        print(f"PROMPT pos {i}: U+{ord(ch):04X} contexto: {repr(prompt_final[max(0,i-20):i+20])}")

# Buscar en config
from core.config import settings
api_key = settings.ANTHROPIC_API_KEY
for i, ch in enumerate(api_key):
    if ord(ch) > 127:
        print(f"API_KEY pos {i}: U+{ord(ch):04X}")

print("Busqueda completada")