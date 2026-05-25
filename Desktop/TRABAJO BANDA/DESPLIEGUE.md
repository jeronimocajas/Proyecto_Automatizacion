# 🚀 Guía de Despliegue en VPS — Sistema de Auxilios CECAR

## Requisitos del VPS
- Ubuntu 22.04 LTS o superior
- Python 3.11+
- PostgreSQL 15+
- Nginx
- Mínimo 1GB RAM, 20GB disco

---

## 1. Preparar el servidor

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx git
```

---

## 2. Configurar PostgreSQL

```bash
sudo -u postgres psql
```
```sql
CREATE USER auxilios_user WITH PASSWORD 'UNA_PASSWORD_SEGURA';
CREATE DATABASE auxilios_cecar OWNER auxilios_user;
GRANT ALL PRIVILEGES ON DATABASE auxilios_cecar TO auxilios_user;
\q
```

Ejecutar el schema:
```bash
sudo -u postgres psql -d auxilios_cecar -f /ruta/al/proyecto/database/schema.sql
```

---

## 3. Configurar el backend

```bash
cd /home/ubuntu
git clone <tu-repo> auxilio-cecar
cd auxilio-cecar/backend

python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env   # Editar con tus valores reales
```

### Variables críticas a configurar en .env:
| Variable | Valor |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://auxilios_user:PASSWORD@localhost:5432/auxilios_cecar` |
| `SECRET_KEY` | Ejecuta `openssl rand -hex 32` |
| `ANTHROPIC_API_KEY` | Tu API key de Anthropic |
| `SMTP_HOST` | Servidor SMTP de CECAR |
| `SMTP_USER` | noreply@cecar.edu.co |
| `SMTP_PASSWORD` | Password del correo |
| `CORREO_DESTINO_BIENESTAR` | bienestar@cecar.edu.co |

---

## 4. Systemd service (para que corra siempre)

```bash
sudo nano /etc/systemd/system/auxilios-cecar.service
```

```ini
[Unit]
Description=Sistema Auxilios CECAR FastAPI
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/auxilio-cecar/backend
ExecStart=/home/ubuntu/auxilio-cecar/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/ubuntu/auxilio-cecar/backend

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable auxilios-cecar
sudo systemctl start auxilios-cecar
sudo systemctl status auxilios-cecar
```

---

## 5. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/auxilios-cecar
```

```nginx
server {
    listen 80;
    server_name tu-dominio.cecar.edu.co;

    # Frontend estático
    root /home/ubuntu/auxilio-cecar/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 15M;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/auxilios-cecar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6. HTTPS con Let's Encrypt (recomendado)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.cecar.edu.co
```

---

## 7. Carpeta de uploads

```bash
mkdir -p /home/ubuntu/auxilio-cecar/backend/uploads
chmod 750 /home/ubuntu/auxilio-cecar/backend/uploads
```

---

## 8. Verificar que todo funcione

```bash
# Probar la API
curl http://localhost:8000/health

# Ver logs en tiempo real
sudo journalctl -u auxilios-cecar -f
```

---

## Estructura de archivos final en el VPS

```
/home/ubuntu/auxilio-cecar/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env                 ← NO subir a git
│   ├── core/
│   ├── models/
│   ├── routers/
│   ├── services/
│   └── uploads/             ← PDFs subidos por estudiantes
├── frontend/
│   └── index.html
└── database/
    └── schema.sql
```

---

## Seguridad adicional recomendada

- ✅ Backup diario de PostgreSQL: `pg_dump auxilios_cecar > backup_$(date +%Y%m%d).sql`
- ✅ Firewall: `ufw allow 22,80,443/tcp && ufw enable`
- ✅ Fail2ban para proteger contra fuerza bruta
- ✅ Los archivos PDF deben almacenarse fuera del directorio web público

---

## Configuración SMTP de CECAR

Si el servidor SMTP institucional no está disponible, puedes usar Gmail con App Password:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tucuenta@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  ← App Password de Google
```
