files = [
    'routers/archivos.py',
    'routers/auth.py', 
    'services/agente_validacion.py',
    'services/correo.py',
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazar caracteres problemáticos
    replacements = {
        '\u2190': '<-',   # ←
        '\u2192': '->',   # →
        '\u2500': '-',    # ─
        '\u2501': '-',    # ━
        '\u2502': '|',    # │
        '\u2550': '=',    # ═
        '\u2588': '#',    # █
        '\u2705': '[OK]', # ✅
        '\u274c': '[X]',  # ❌
        '\u26a0': '[!]',  # ⚠
        '\ufe0f': '',     # variacion emoji
        '\U0001f4cb': '', # 📋
    }
    
    for char, replacement in replacements.items():
        content = content.replace(char, replacement)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'Limpiado: {filepath}')

print('Listo!')