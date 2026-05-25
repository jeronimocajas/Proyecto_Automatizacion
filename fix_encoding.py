import re

files = [
    'routers/archivos.py',
    'routers/auth.py',
    'services/agente_validacion.py',
    'services/correo.py',
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Guardar con encoding utf-8 explícito y agregar declaración al inicio
    if not content.startswith('# -*- coding: utf-8 -*-'):
        content = '# -*- coding: utf-8 -*-\n' + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'Fixed: {filepath}')

print('Done!')