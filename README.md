# 🐾 ValVic

> **Hola Gissele 💜**
> Necesito tu cerebro (y tus ganas) para hacer que esto funcione.
> Si estás leyendo esto, es porque confío en ti para construir algo increíble juntos.
> Bienvenida al equipo. 🚀

---

## ¿Qué es ValVic?

**ValVic** es una plataforma SaaS que automatiza la **gestión de citas** para clínicas, consultorios y centros de salud a través de **WhatsApp con Inteligencia Artificial**.

El producto principal es **Vicky** — una asistente virtual que:
- 📱 Recibe mensajes de pacientes por WhatsApp (vía Meta Cloud API)
- 🧠 Entiende la intención con IA (Claude de Anthropic)
- 📅 Agenda citas automáticamente cruzando disponibilidad
- 🔔 Envía recordatorios y confirmaciones
- 📊 Reporta métricas al dueño del negocio

**¿Para quién?** Clínicas dentales, veterinarias, centros de estética, spas, psicólogos, gimnasios y más. Cada vertical tiene su propio agente personalizado con nombre, personalidad y configuración específica.

---

## Arquitectura del Sistema

```
                                    ┌──────────────────────┐
                                    │   Hostinger Business  │
                                    │  (Landing + Panel UI) │
                                    └──────────┬───────────┘
                                               │ HTTPS
┌─────────────┐     Meta Graph API     ┌───────┴───────────┐
│  Paciente   │ ◄──────────────────► │   Oracle Cloud VM   │
│ (WhatsApp)  │     Webhooks          │  ┌───────────────┐  │
└─────────────┘                       │  │   FastAPI      │  │
                                      │  │  (Python 3.11) │  │
┌─────────────┐     Claude API        │  └───────┬───────┘  │
│  Anthropic  │ ◄────────────────────│          │          │
│  (Haiku +   │                       │  ┌───────┴───────┐  │
│   Sonnet)   │                       │  │ MySQL HeatWave│  │
└─────────────┘                       │  │   (50 GB)     │  │
                                      │  └───────────────┘  │
┌─────────────┐     Places API        │                     │
│   Google    │ ◄────────────────────│                     │
│   Places    │                       └─────────────────────┘
└─────────────┘
```

---

## Stack Tecnológico

| Capa | Tecnología | Motivo |
|---|---|---|
| **Frontend** | HTML/CSS/JS puro (Vanilla) | CSP estricto, cero dependencias, deploy drag-and-drop |
| **Backend** | Python 3.11 + FastAPI | SDK Anthropic nativo, async I/O, ideal para dev solitario |
| **Base de datos** | MySQL HeatWave (Oracle) | Always Free permanente, 50GB, control total |
| **Mensajería** | Meta WhatsApp Cloud API (Graph v20.0) | Conexión directa con Meta, sin intermediarios |
| **IA** | Claude Sonnet (respuestas) + Haiku (clasificación) | Sonnet para persuasión, Haiku para volumen barato |
| **Infra** | Oracle Cloud Free Tier | VM ARM 4CPU/24GB gratis de por vida |
| **Automatización** | Python + crontab | Sin vendor lock-in, lógica compleja nativa |

> ⚠️ **Regla de oro**: Nunca proponer React, Vue, Node.js, LangChain, Supabase, AWS ni cualquier framework/plataforma fuera de este stack. Lee `docs/PROYECTO.md` para el detalle completo.

---

## Estructura del Proyecto

```
ValVic/
├── Landing/                  # 🌐 Sitio web público (marketing, demos)
│   ├── index.html            #    Landing page principal
│   ├── css/                  #    Estilos (Fraunces + DM Sans, glassmorphism)
│   ├── js/                   #    Lógica (animaciones, partículas, formulario)
│   ├── demos/                #    Demos interactivas de cada servicio
│   └── tests/                #    27 unit tests (sanitize, validación, XSS)
│
├── Panel/                    # 🖥️ Dashboard de clientes (app privada)
│   ├── login.html            #    Autenticación JWT
│   ├── agenda.html           #    Gestión de citas
│   ├── pacientes.html        #    Base de pacientes
│   ├── configuracion.html    #    Ajustes del negocio
│   ├── css/                  #    Estilos del panel (Esmeralda Premium)
│   └── js/                   #    Web Components (sidebar-nav, topbar-header)
│
├── Agentes/                  # 🤖 Backend IA + FastAPI
│   ├── agente_conversacion.py #   Webhook WhatsApp + Vicky (Claude)
│   ├── prospector.py          #   Prospección automatizada multi-vertical
│   ├── subagente_db.py        #   Interfaz de base de datos (SQLite/MySQL)
│   ├── prompts_ventas.py      #   System prompts y escalera de concesiones
│   ├── auth_panel.py          #   Autenticación JWT para el Panel
│   ├── backup_mysql.py        #   Backup encriptado a Oracle Object Storage
│   ├── actualizar_openers.py  #   Generador de mensajes de apertura con IA
│   └── verticals/             #   Configs YAML por vertical (dental, vet, etc.)
│
├── Database/                 # 🗄️ Esquemas SQL
│   ├── *_mysql.sql           #    Schemas de producción (MySQL HeatWave)
│   ├── legacy_postgres/      #    Respaldo de schemas PostgreSQL originales
│   └── schema_prospeccion_mysql.sql
│
├── docs/                     # 📚 Documentación del proyecto
│   ├── PROYECTO.md           #    ⭐ Constitución técnica (LEER PRIMERO)
│   ├── INSTALACION.md        #    Guía de despliegue en Oracle Cloud
│   ├── VENTAS.md             #    Precios, verticales y estrategia comercial
│   ├── ONBOARDING_CLIENTES.md #   Flujo de vinculación de clientes (Embedded Signup)
│   └── ROADMAP.md            #    Tareas pendientes por fase
│
├── .agent/                   # 🧠 Contexto para asistentes IA
│   ├── brain/                #    Memoria compartida (estado, arquitectura, reglas)
│   └── MASTER_PROMPT_OPUS.md #    Prompt orquestador para Opus 4.6
│
├── legacy/                   # 🪦 Scripts antiguos (ya no se usan)
├── valvic_logos/              # 🎨 Logos en todos los formatos
├── .env.example              # 🔑 Template de variables de entorno
├── .cursorrules              # 🤖 Reglas para asistentes IA en el IDE
├── requirements.txt          # 📦 Dependencias Python
└── setup_oracle.sh           # ⚙️ Script de setup automatizado para Oracle VM
```

---

## Requisitos Previos

- **Python 3.11+**
- **pip** (gestor de paquetes)
- **Git**
- Claves API:
  - [Anthropic (Claude)](https://console.anthropic.com/) — para la IA
  - [Meta Developer Portal](https://developers.facebook.com/) — para WhatsApp
  - [Google Cloud Console](https://console.cloud.google.com/) — para Places API

---

## Configuración Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/vivenegasl/ValVic.git
cd ValVic

# 2. Crear y activar entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus claves reales
```

---

## Ejecución

### Agente conversacional (Vicky)
```bash
# Levantar el servidor FastAPI (desarrollo)
uvicorn Agentes.agente_conversacion:app --reload --port 8000
```

### Prospector (captación de clientes)
```bash
# Ver verticales disponibles
python Agentes/prospector.py --listar-verticales

# Prospectar en modo test (simulación CLI)
python Agentes/prospector.py --vertical dental --ciudad Santiago --cantidad 5 --test

# Enviar en producción
python Agentes/prospector.py --vertical dental --ciudad Santiago --enviar

# Solo revisar estado de prospectos
python Agentes/prospector.py --vertical dental --solo-revisar
```

### Panel de clientes
Abrir `Panel/login.html` en el navegador (requiere que el backend FastAPI esté corriendo).

---

## Documentación Interna

| Documento | Descripción |
|---|---|
| [docs/PROYECTO.md](docs/PROYECTO.md) | ⭐ **Constitución técnica** — reglas de oro, stack autorizado, estándares de código. Lectura obligatoria. |
| [docs/INSTALACION.md](docs/INSTALACION.md) | Guía paso a paso para desplegar en Oracle Cloud (VM + MySQL + SSL). |
| [docs/VENTAS.md](docs/VENTAS.md) | Precios por servicio, agentes por vertical, escalera de concesiones, costos operativos. |
| [docs/ONBOARDING_CLIENTES.md](docs/ONBOARDING_CLIENTES.md) | Cómo los clientes vinculan su WhatsApp Business vía Meta Embedded Signup. |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Roadmap de desarrollo — fases pendientes y completadas. |
| [.env.example](.env.example) | Template con todas las variables de entorno necesarias y documentadas. |

---

## Reglas de Contribución

1. **Lee `docs/PROYECTO.md`** antes de escribir cualquier línea de código
2. **Vanilla only** — HTML/CSS/JS puro en el frontend, cero frameworks
3. **Python + FastAPI** en el backend, cero LangChain ni abstracciones de agentes
4. **MySQL HeatWave** — nunca PostgreSQL, Supabase ni alternativas
5. **Pydantic v2** para toda validación de datos en Python
6. **UUIDs** como primary keys en tablas expuestas al exterior
7. **Credenciales** siempre en `.env`, nunca hardcodeadas
8. **CSP-ready** — sin scripts inline, sin styles inline
9. **Try/except** en toda llamada a API externa con logging

---

<p align="center">
  <strong>ValVic</strong> · Automatizamos lo que tu clínica no debería hacer a mano 💚
</p>
