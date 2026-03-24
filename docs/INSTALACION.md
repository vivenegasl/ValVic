# Guía de Despliegue en Oracle Cloud (ValVic)

¡Felicidades por registrarte en Oracle Cloud! 

Basado en el cerebro estratégico (`PROYECTO.md` y `ARQUITECTURA.md`) y el script automatizado existente en tu repositorio (`setup_oracle.sh`), aquí tienes el paso a paso exacto para desplegar toda la infraestructura:

## Fase 1: Creación de Recursos (Consola de Oracle)

1. **Crear la Máquina Virtual (VM Ampere):**
   - Ve a **Compute > Instances** y haz clic en "Create Instance".
   - **Imagen:** Selecciona **Ubuntu 22.04 LTS**.
   - **Shape (Hardware):** Cambia a `VM.Standard.A1.Flex` (Arquitectura ARM Ampere). Asigna **4 OCPUs** y **24 GB de RAM** (100% gratis en el Free Tier).
   - **Red:** Crea una nueva VCN y Subred Pública.
   - **Llaves SSH:** Genera o sube tu clave pública SSH (`.pub`) para poder conectarte después.

2. **Abrir Puertos en Oracle (Security Lists):**
   - Ve a **Networking > Virtual Cloud Networks**. 
   - Entra a tu VCN > *Security Lists* > *Default Security List*.
   - Añade *Ingress Rules* (Reglas de entrada) para:
     - **Puerto 80** (HTTP) — Origen: `0.0.0.0/0`
     - **Puerto 443** (HTTPS) — Origen: `0.0.0.0/0`

3. **Crear la Base de Datos (MySQL HeatWave):**
   - Ve a **Databases > MySQL**.
   - Crea un nuevo sistema de DB (en la misma VCN de tu VM).
   - Crea un usuario administrador (ej. `valvic_app`) y anota la contraseña.
   - Anota la **Dirección IP Privada** que Oracle le asigne a la base de datos.

---

## Fase 2: Configuración del Servidor (Vía Terminal)

Desde tu computador, conéctate a la VM por SSH usando la IP Pública que te asignó Oracle:
```bash
ssh -i "ruta/a/tu_llave_privada" ubuntu@<IP_PUBLICA_DE_VM>
```

1. **Clonar el Repositorio de ValVic:**
Como en el paso anterior limpiamos y dejamos perfecto el repo en GitHub, descárgalo allí:
```bash
git clone https://github.com/vivenegasl/ValVic.git
cd ValVic
```

2. **Ejecutar el Script Automático:**
El comando `setup_oracle.sh` configurará automáticamente Python 3.11, entornos virtuales, Nginx para proxy reverso y servicios SystemD.
```bash
chmod +x setup_oracle.sh
./setup_oracle.sh
```

---

## Fase 3: Pasos Manuales Post-Instalación

El script copiará el proyecto a `/opt/valvic/app`. Para finalizar, debes hacer lo siguiente:

1. **Configurar Credenciales (.env):**
```bash
nano /opt/valvic/app/.env
```
   Aquí deberás colocar tus tokens reales de Anthropic, Meta API (o 360dialog), Google Places, y configurar `MYSQL_HOST` con la IP Privada de la BD del Paso 1, junto al usuario y contraseña.

2. **Cargar la Base de Datos (Esquema MySQL):**
Ejecuta los schemas que migramos en sesiones anteriores hacia MySQL:
```bash
mysql -h <IP_PRIVADA_MYSQL> -u valvic_app -p < /opt/valvic/app/Database/valvic_schema_principal_mysql.sql
mysql -h <IP_PRIVADA_MYSQL> -u valvic_app -p < /opt/valvic/app/Database/valvic_schema_reportes_mysql.sql
```

3. **Iniciar a Vicky (FastAPI):**
Levanta el servicio web que procesará los mensajes:
```bash
sudo systemctl start valvic-vicky
sudo systemctl enable valvic-vicky
```

4. **Seguridad SSL (Obligatorio para WhatsApp):**
Asegúrate de que en tu gestor de dominios (ej. Hostinger) el subdominio `api.valvic.cl` apunte a la IP Pública de tu VM. Luego corre Certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.valvic.cl
```

Una vez terminado, tu IA estará lista para recibir mensajes en:
👉 `https://api.valvic.cl/webhook/whatsapp`
