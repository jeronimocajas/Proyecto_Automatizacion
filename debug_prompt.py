import sys
sys.stdout.reconfigure(encoding='utf-8')

from core.config import settings
from services.agente_validacion import PROMPT_VALIDACION

tipo = "Plan Padrino"
prompt = PROMPT_VALIDACION + f"\n\nEl estudiante selecciono el tipo de auxilio: {tipo}."

print("Longitud:", len(prompt))
print("Char en pos 109:", repr(prompt[109]))
print("Contexto:", repr(prompt[90:130]))

for i, ch in enumerate(prompt):
    if ord(ch) > 127:
        print(f"pos {i}: U+{ord(ch):04X} {repr(ch)}")