# INSTALACION.md — ValVic

> Guía paso a paso para instalar y arrancar el sistema en producción (Oracle VM) y en local (SQLite).

---

## Requisitos previos

- Python 3.11+
- Oracle VM con Ubuntu 22.04 (o entorno local para pruebas con SQLite)
- Claves API: Anthropic (obligatoria), Google Places (opcional), 360dialog (cuando Oracle esté activo)

---

## 1. Preparar el entorno

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

---

## 2. Configurar variables de entorno

```bash
cp .env.example .env
nano .env   # Completar con tus valores reales
```

**Mínimo para correr en local (SQLite):**
```
ANTHROPIC_API_KEY=sk-ant-...
```

**Producción completa (MySQL + WhatsApp):**
```
MYSQL_HOST=<host Oracle HeatWave>
MYSQL_PORT=3306
MYSQL_USER=valvic_app
MYSQL_PASSWORD=<password>
MYSQL_DB=valvic_db
DIALOG360_API_KEY=<key>
DIALOG360_PHONE_ID=<phone id>
GOOGLE_PLACES_API_KEY=<key>
VALVIC_WHATSAPP=56928417992
```

---

## 3. Estructura de carpetas

```
Valvic/
├── Agentes/
│   ├── agente_conversacion.py    ← Vicky (webhook + ventas)
│   ├── subagente_db.py           ← Persistencia SQLite/MySQL
│   ├── prompts_ventas.py         ← Prompts y precios por vertical
│   ├── prospector.py             ← Prospector multi-vertical
│   └── actualizar_openers.py     ← Regenera mensajes opener
├── verticals/
│   ├── dental.yaml, veterinarias.yaml, spa.yaml
│   ├── psicologos.yaml, estetica.yaml, gimnasios.yaml
│   ├── inmobiliarias.yaml, mueblerias.yaml
├── sql/
│   ├── schema_prospeccion_mysql.sql  ← Ejecutar en Oracle ✅
│   ├── valvic_schema_principal.sql   ← Pendiente conversión PG→MySQL
│   └── valvic_schema_reportes.sql    ← Pendiente conversión PG→MySQL
├── ValVic Web/                       ← Frontend valvic.cl
├── Estructuras/                      ← Código legado (Sheets)
├── requirements.txt
├── setup_oracle.sh
├── .env.example
└── PROYECTO (1).md
```

---

## 4. Inicializar base de datos

### Local (SQLite — para pruebas)

```bash
cd Agentes
python3 -c "from subagente_db import SubagenteDB; db = SubagenteDB(); db.init(); print(db.resumen())"
```

Crea `prospectos_vet.db` automáticamente.

### Producción (MySQL en Oracle HeatWave)

```bash
# Asegúrate que MYSQL_* están en .env
mysql -h $MYSQL_HOST -u valvic_app -p $MYSQL_DB < sql/schema_prospeccion_mysql.sql

# Verificar
python3 -c "from subagente_db import SubagenteDB; db = SubagenteDB(); db.init(); print(db.backend, db.resumen())"
```

---

## 5. Verificar verticales disponibles

```bash
cd Agentes
python3 prospector.py --listar-verticales
```

Debe mostrar los 8 verticales: `dental`, `veterinarias`, `spa`, `psicologos`, `estetica`, `gimnasios`, `inmobiliarias`, `mueblerias`.

---

## 6. Primera ejecución — modo test (sin enviar mensajes)

```bash
cd Agentes

# Sin Google Places API (Claude genera lista de negocios ficticios para prueba)
python3 prospector.py --vertical dental --ciudad Santiago --cantidad 10 --test

# Revisar prospectos generados
python3 prospector.py --vertical dental --solo-revisar

# Exportar CSV con links wa.me precompletados
python3 prospector.py --vertical dental --solo-exportar
```

---

## 7. Probar el agente de ventas (simulación)

```bash
cd Agentes
python3 agente_conversacion.py --simular --telefono "+56912345678"
```

Inicia conversación simulada con Vicky sin enviar mensajes reales por WhatsApp.

---

## 8. Despliegue en Oracle VM (producción)

```bash
# Correr el script de instalación automatizada
chmod +x setup_oracle.sh
./setup_oracle.sh

# El script hace:
# 1. Actualiza Ubuntu
# 2. Instala Python 3.11+
# 3. Crea entorno virtual en /opt/valvic/venv
# 4. Copia archivos a /opt/valvic/app
# 5. Instala dependencias
# 6. Configura systemd (valvic-vicky.service)
# 7. Configura cron jobs (prospector lunes 9am, openers 9:30am)
# 8. Instala y configura Nginx como reverse proxy
```

---

## 9. Activar webhook 360dialog

```bash
# 1. Instalar SSL (obligatorio para 360dialog)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.valvic.cl

# 2. Iniciar servicio Vicky
sudo systemctl start valvic-vicky
sudo systemctl enable valvic-vicky
sudo systemctl status valvic-vicky

# 3. Verificar health check
curl https://api.valvic.cl/health

# 4. En el panel de 360dialog:
#    Webhook URL = https://api.valvic.cl/webhook/whatsapp
```

---

## 10. Agregar un nuevo vertical

```bash
# Copiar el YAML de un vertical similar como base
cp verticals/dental.yaml verticals/fisioterapia.yaml

# Editar con los datos del nuevo vertical
nano verticals/fisioterapia.yaml

# Verificar que aparece
python3 Agentes/prospector.py --listar-verticales

# Prospectar (cero cambios de código)
python3 Agentes/prospector.py --vertical fisioterapia --ciudad Santiago --cantidad 10 --test
```

---

## Notas de seguridad

- **Nunca commitear:** `.env`, `*.db`, `*.pem`, `google_credentials.json`
- El `.env.example` **sí va al repo** (sin valores reales)
- Revisar `.gitignore` antes de cada `git push`
- En producción, usar variables de entorno del sistema — no `.env` en el servidor
