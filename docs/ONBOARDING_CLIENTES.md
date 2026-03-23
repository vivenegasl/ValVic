# Estrategia de Onboarding para Clientes (WhatsApp API)

Para que el servicio de "Agenda con IA" sea escalable, los clientes de ValVic deben poder vincular sus propios números de forma autónoma.

## 1. Vinculación Técnica: Embedded Signup
Se recomienda implementar el **Embedded Signup** de Meta en el panel de administración de ValVic:
- El cliente inicia sesión con su cuenta de Facebook en una ventana emergente.
- Elige o crea su cuenta de WhatsApp Business (WABA).
- Autoriza a la App de ValVic a enviar mensajes en su nombre.
- El sistema recibe automáticamente el `PhoneID` y el `WABA_ID` para configurar a Vicky.

## 2. Gestión de Números
- **Número dedicado:** Se sugiere al cliente adquirir un nuevo número (físico o virtual) para Vicky. Esto evita que pierda su acceso a la aplicación de WhatsApp tradicional (que se desactiva al usar la API).
- **Consistencia de Marca:** El nombre del perfil de WhatsApp se configura desde el Business Manager de Meta y se sincroniza con el branding de ValVic si es necesario.

## 3. Costes y Facturación de Meta
- **Mensajes Gratuitos:** Meta regala 1,000 conversaciones de servicio (iniciadas por el usuario final) al mes **por cada cuenta WABA**. Esto es una ventaja competitiva para tus clientes.
- **Facturación Directa:** El cliente asocia su propia tarjeta de crédito en Meta. ValVic no actúa como intermediario de pagos para Meta, simplificando la administración y los impuestos.
