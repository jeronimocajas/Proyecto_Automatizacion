files = ['services/agente_validacion.py', 'services/correo.py', 'routers/archivos.py', 'routers/auth.py']
for f in files:
    content = open(f, encoding='utf-8').read()
    for i, ch in enumerate(content):
        if ord(ch) > 127:
            print(f'{f} pos {i}: U+{ord(ch):04X} -> {repr(content[max(0,i-30):i+30])}')