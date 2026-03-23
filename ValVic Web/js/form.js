/**
 * form.js
 * Manejo seguro del formulario de contacto.
 * Depende de: config.js, utils.js
 */

(function () {
  let ultimoEnvio = 0;

  function mostrarError(msg) {
    const el = document.getElementById("f-error");
    if (!el) return;
    el.textContent = "❌ " + msg;
    el.style.display = "block";
    setTimeout(() => { el.style.display = "none"; }, 5000);
  }

  async function submitForm(e) {
    e.preventDefault();

    // Rate limiting
    const limite = checkRateLimit(ultimoEnvio, CONFIG.FORM_COOLDOWN_MS);
    if (!limite.ok) {
      mostrarError(`Por favor espera ${limite.segundosRestantes} segundos antes de enviar de nuevo.`);
      return;
    }

    // Construir payload sanitizado
    const payload = buildPayload(
      {
        nombre:   document.getElementById("f-nombre")?.value,
        negocio:  document.getElementById("f-negocio")?.value,
        contacto: document.getElementById("f-contacto")?.value,
        tipo:     document.getElementById("f-tipo")?.value,
        mensaje:  document.getElementById("f-mensaje")?.value,
      },
      CONFIG.FORM_ORIGIN
    );

    // Validar
    const error = validarForm(payload.nombre, payload.contacto);
    if (error) { mostrarError(error); return; }

    // UI — cargando
    const btn = document.getElementById("f-btn");
    if (btn) { btn.textContent = "Enviando..."; btn.classList.add("loading"); }

    try {
      await fetch(CONFIG.APPS_SCRIPT_URL, {
        method:  "POST",
        mode:    "no-cors",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      });

      ultimoEnvio = Date.now();
      const form    = document.getElementById("c-form");
      const success = document.getElementById("f-success");
      if (form)    form.style.display    = "none";
      if (success) success.style.display = "block";

    } catch {
      if (btn) { btn.textContent = "Enviar mensaje →"; btn.classList.remove("loading"); }
      mostrarError("Hubo un error. Escríbenos directo por WhatsApp.");
    }
  }

  // Registrar el handler cuando el DOM esté listo
  const form = document.getElementById("c-form");
  if (form) form.addEventListener("submit", submitForm);
})();
