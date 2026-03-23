# Plan de Migración: WhatsApp Cloud API (Meta Directo)

Este documento detalla la transición de 360dialog a la infraestructura directa de Meta para optimizar costes y control.

## 1. Justificación Técnica
- **Ahorro Fijo:** Eliminación de los ~$60 USD mensuales de 360dialog.
- **Rendimiento:** Conexión directa con los servidores de Meta en la nube.
- **Transparencia:** Sin intermediarios en el flujo de mensajería.

## 2. Pasos de Configuración (Meta Developer Portal)
1.  **App Setup:** Crear App de tipo "Business" en `developers.facebook.com`.
2.  **Product Setup:** Añadir el producto "WhatsApp" a la App.
3.  **Token:** Generar un `System User Access Token` permanente con permisos `whatsapp_business_messaging`.
4.  **Verificación:** Completar la verificación del negocio en el Business Manager.

## 3. Cambios en el Backend (FastAPI)
- **Endpoint Webhook:** Crear `/webhook/whatsapp` (GET para verificación, POST para mensajes).
- **Seguridad:** Implementar validación de firma `X-Hub-Signature-256`.
- **Lógica de Envío:** Migrar de `360dialog.com` a `graph.facebook.com/v20.0/`.
- **Parseo de JSON:** Adaptar la estructura de los objetos de mensaje de Meta (diferente a la de 360dialog).

## 4. Plan de Despliegue
1.  Configurar variables de entorno en Oracle VM (`META_ACCESS_TOKEN`, `META_VERIFY_TOKEN`).
2.  Desplegar nueva versión de `agente_conversacion.py`.
3.  Configurar URL de Webhook en el portal de Meta y verificar conexión.
