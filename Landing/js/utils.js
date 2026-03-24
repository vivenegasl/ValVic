/**
 * utils.js
 * Funciones puras — sin side effects, 100% testeables.
 */

/**
 * Sanitiza una cadena eliminando caracteres HTML peligrosos.
 * @param {string} str
 * @returns {string}
 */
function sanitize(str) {
  if (typeof str !== "string") return "";
  const map = { "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;", "&": "&amp;" };
  return str.trim().replace(/[<>"'&]/g, (c) => map[c]);
}

/**
 * Valida nombre y contacto del formulario.
 * @param {string} nombre
 * @param {string} contacto
 * @returns {string|null} — mensaje de error, o null si es válido
 */
function validarForm(nombre, contacto) {
  if (!nombre || nombre.length < 2)
    return "El nombre debe tener al menos 2 caracteres.";
  if (nombre.length > 80)
    return "El nombre es demasiado largo.";

  const esEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contacto);
  const esTel   = /^\+?[\d\s\-\(\)]{7,16}$/.test(contacto);

  if (!esEmail && !esTel)
    return "Ingresa un email válido o un teléfono con código de país.";

  return null;
}

/**
 * Verifica si el cooldown de rate limiting ha pasado.
 * @param {number} ultimoEnvio — timestamp en ms del último envío
 * @param {number} cooldownMs  — ms de espera requeridos
 * @param {number} ahora       — timestamp actual (inyectable para tests)
 * @returns {{ ok: boolean, segundosRestantes: number }}
 */
function checkRateLimit(ultimoEnvio, cooldownMs, ahora = Date.now()) {
  const diff = ahora - ultimoEnvio;
  if (diff < cooldownMs) {
    return { ok: false, segundosRestantes: Math.ceil((cooldownMs - diff) / 1000) };
  }
  return { ok: true, segundosRestantes: 0 };
}

/**
 * Construye el payload del formulario sanitizando cada campo.
 * @param {Object} campos — { nombre, negocio, contacto, tipo, mensaje }
 * @param {string} origen — dominio de origen
 * @returns {Object}
 */
function buildPayload(campos, origen) {
  return {
    nombre:   sanitize(campos.nombre   || ""),
    negocio:  sanitize(campos.negocio  || ""),
    contacto: sanitize(campos.contacto || ""),
    tipo:     sanitize(campos.tipo     || ""),
    mensaje:  sanitize(campos.mensaje  || ""),
    origen,
  };
}
