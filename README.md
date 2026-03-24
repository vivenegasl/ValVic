# ValVic — Repositorio Principal

> [!IMPORTANT]
> **REGLA DE MEMORIA VIVA (MANDATORIA):** Al inicio de cada sesión comercial o técnica, el agente DEBE leer la carpeta `/.agent/brain/`. Al finalizar cada hito o antes de terminar la sesión, el agente DEBE actualizar proactivamente `ESTADO_ACTUAL.md` y `ARQUITECTURA.md` basándose en el trabajo realizado. Esto garantiza la persistencia del contexto senior de ValVic.

## Estructura del Proyecto
- `/Landing`: Sitio web de marketing, activos públicos y demos.
- `/Panel`: Aplicativo de clientes (Agenda, Pacientes, Cobros).
- `/Agentes`: Backend FastAPI y lógica de agentes IA (Vicky).
- `/.agent/brain`: Memoria compartida del proyecto.

## CÓMO EJECUTAR EL PROSPECTOR 

*(Requiere que `.env` esté correctamente configurado con las claves)*

```bash
# Ver verticales disponibles en la carpeta yml
python Agentes/prospector.py --listar-verticales

# Prospectar (Simulación CLI)
python Agentes/prospector.py --vertical dental --ciudad Santiago --cantidad 5 --test

# Enviar en Firme en Producción
python Agentes/prospector.py --vertical psicologos --ciudad Santiago --enviar

# Revisar mensajes generados o estado de prospectos
python Agentes/prospector.py --vertical dental --solo-revisar
```
