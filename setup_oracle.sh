#!/bin/bash
# ================================================================
#  ValVic — Setup automatizado en Oracle VM
#  Ejecutar UNA SOLA VEZ como usuario ubuntu en la VM
#
#  Uso:
#    chmod +x setup_oracle.sh
#    ./setup_oracle.sh
# ================================================================

set -e  # detener si cualquier comando falla

VERDE="\033[0;32m"
AMARILLO="\033[1;33m"
ROJO="\033[0;31m"
RESET="\033[0m"

ok()   { echo -e "${VERDE}[OK]${RESET} $1"; }
info() { echo -e "${AMARILLO}[..] $1${RESET}"; }
err()  { echo -e "${ROJO}[ERROR]${RESET} $1"; exit 1; }

echo ""
echo "================================================================"
echo "  ValVic — Setup Oracle VM"
echo "================================================================"
echo ""

# ── 1. Verificar que estamos en la VM correcta ────────────────────
info "Verificando sistema..."
[[ "$(uname -m)" == "aarch64" ]] && ok "ARM Ampere detectado (correcto)" \
  || echo "[AVISO] No es ARM — continúa igual si es tu VM"

# ── 2. Actualizar sistema ─────────────────────────────────────────
info "Actualizando paquetes del sistema..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq
ok "Sistema actualizado"

# ── 3. Instalar Python 3.11+ ──────────────────────────────────────
info "Verificando Python..."
if ! python3 --version | grep -qE "3\.(11|12|13)"; then
    info "Instalando Python 3.11..."
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip -qq
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
fi
ok "Python $(python3 --version)"

# ── 4. Crear entorno virtual ──────────────────────────────────────
info "Creando entorno virtual..."
VENV_DIR="/opt/valvic/venv"
sudo mkdir -p /opt/valvic
sudo chown ubuntu:ubuntu /opt/valvic
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
ok "Entorno virtual en $VENV_DIR"

# ── 5. Copiar archivos del proyecto ───────────────────────────────
info "Copiando archivos del proyecto..."
APP_DIR="/opt/valvic/app"
mkdir -p "$APP_DIR"

# Si estás corriendo este script desde la carpeta del proyecto:
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR"/*.py "$APP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR"/Agentes/*.py "$APP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/requirements.txt" "$APP_DIR/"
cp "$SCRIPT_DIR/.env.example" "$APP_DIR/"
mkdir -p "$APP_DIR/verticals"
cp "$SCRIPT_DIR"/verticals/*.yaml "$APP_DIR/verticals/" 2>/dev/null || true
ok "Archivos copiados en $APP_DIR"

# ── 6. Instalar dependencias Python ──────────────────────────────
info "Instalando dependencias Python..."
pip install --quiet --upgrade pip
pip install --quiet -r "$APP_DIR/requirements.txt"
ok "Dependencias instaladas"

# ── 7. Configurar .env ────────────────────────────────────────────
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo ""
    echo -e "${AMARILLO}IMPORTANTE: Edita el .env con tus credenciales reales:${RESET}"
    echo "  nano $APP_DIR/.env"
    echo ""
fi

# ── 8. Instalar MySQL client para ejecutar schema ─────────────────
info "Instalando MySQL client..."
sudo apt-get install -y mysql-client -qq
ok "MySQL client instalado"

# ── 9. Configurar servicio systemd para el webhook ───────────────
info "Configurando servicio systemd para Vicky (webhook)..."
sudo tee /etc/systemd/system/valvic-vicky.service > /dev/null <<EOF
[Unit]
Description=ValVic — Vicky Agente de Ventas WhatsApp
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/valvic/app
Environment="PATH=/opt/valvic/venv/bin"
EnvironmentFile=/opt/valvic/app/.env
ExecStart=/opt/valvic/venv/bin/uvicorn agente_conversacion:app --host 0.0.0.0 --port 8001 --workers 1
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=valvic-vicky

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
ok "Servicio valvic-vicky.service configurado"

# ── 10. Configurar cron jobs ──────────────────────────────────────
info "Configurando cron jobs..."
(crontab -l 2>/dev/null; echo "# ValVic — Prospector veterinarias (lunes 9am)") | crontab -
(crontab -l 2>/dev/null; echo "0 9 * * 1 cd /opt/valvic/app && /opt/valvic/venv/bin/python prospector.py --vertical veterinarias --ciudad 'Santiago' --cantidad 50 >> /var/log/valvic/prospector.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "# ValVic — Actualizar openers (lunes 9:30am, después del prospector)") | crontab -
(crontab -l 2>/dev/null; echo "30 9 * * 1 cd /opt/valvic/app && /opt/valvic/venv/bin/python actualizar_openers.py --cantidad 50 >> /var/log/valvic/openers.log 2>&1") | crontab -

mkdir -p /var/log/valvic
sudo chown ubuntu:ubuntu /var/log/valvic
ok "Cron jobs configurados"

# ── 11. Configurar firewall (Oracle tiene su propio security list) ─
info "Abriendo puerto 8001 en firewall local (Ubuntu)..."
sudo ufw allow 8001/tcp 2>/dev/null || true
ok "Puerto 8001 abierto"

# ── 12. Configurar Nginx como reverse proxy ───────────────────────
info "Instalando y configurando Nginx..."
sudo apt-get install -y nginx -qq
sudo tee /etc/nginx/sites-available/valvic > /dev/null <<'EOF'
server {
    listen 80;
    server_name api.valvic.cl;

    location /webhook/whatsapp {
        proxy_pass         http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_read_timeout 30s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8001;
    }

    location / {
        return 404;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/valvic /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
ok "Nginx configurado"

echo ""
echo "================================================================"
echo -e "  ${VERDE}Setup completado${RESET}"
echo "================================================================"
echo ""
echo "PASOS MANUALES QUE QUEDAN:"
echo ""
echo "  1. Editar credenciales:"
echo "     nano /opt/valvic/app/.env"
echo ""
echo "  2. Ejecutar schema MySQL (una sola vez):"
echo "     mysql -h \$MYSQL_HOST -u valvic_app -p valvic_db < /opt/valvic/app/schema_prospeccion_mysql.sql"
echo ""
echo "  3. Verificar conexión MySQL:"
echo "     cd /opt/valvic/app && python3 -c 'from subagente_db import SubagenteDB; db=SubagenteDB(); db.init(); print(db.resumen())'"
echo ""
echo "  4. Iniciar el servicio de Vicky:"
echo "     sudo systemctl start valvic-vicky"
echo "     sudo systemctl enable valvic-vicky"
echo "     sudo systemctl status valvic-vicky"
echo ""
echo "  5. Instalar SSL (obligatorio para 360dialog):"
echo "     sudo apt install certbot python3-certbot-nginx -y"
echo "     sudo certbot --nginx -d api.valvic.cl"
echo ""
echo "  6. Configurar webhook en 360dialog:"
echo "     URL: https://api.valvic.cl/webhook/whatsapp"
echo ""
echo "  7. Primer prospector manual (prueba):"
echo "     cd /opt/valvic/app && python3 prospector.py --vertical veterinarias --ciudad 'Santiago' --cantidad 10 --test"
echo ""
