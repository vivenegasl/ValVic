/**
 * login.js — ValVic Panel CRM
 * Maneja el formulario de login: POST /api/login, cookie HttpOnly.
 * Sin inline scripts — cumple CSP 'self'.
 */

(function () {
  "use strict";

  const form    = document.getElementById("loginForm");
  const btnEl   = document.getElementById("btn-submit");
  const errorEl = document.getElementById("errorMsg");

  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    // Validación básica
    if (!email || !password) {
      showError("Por favor completa todos los campos.");
      return;
    }

    // Estado cargando
    btnEl.disabled     = true;
    btnEl.innerHTML    = '<i class="ph ph-spinner ph-spin" aria-hidden="true"></i> Autenticando…';
    errorEl.style.display = "none";

    try {
      const res = await fetch("/api/login", {
        method:      "POST",
        credentials: "include",          // necesario para recibir la cookie HttpOnly
        headers:     { "Content-Type": "application/json" },
        body:        JSON.stringify({ email, password }),
      });

      if (res.ok) {
        // El backend colocó la cookie vv_token (HttpOnly).
        // Redirigir al panel — la cookie viaja automáticamente.
        window.location.href = "agenda.html";
      } else if (res.status === 401) {
        showError("Credenciales incorrectas. Verifica tu correo y contraseña.");
      } else if (res.status === 0 || !res.status) {
        showError("No se pudo conectar con el servidor. ¿Está encendido el backend?");
      } else {
        const data = await res.json().catch(() => ({}));
        showError(data.detail || "Error al iniciar sesión. Intenta de nuevo.");
      }
    } catch (err) {
      console.error("[login.js] fetch error:", err);
      showError("Sin conexión con el servidor backend. Verifica que Vicky esté activo.");
    } finally {
      btnEl.disabled  = false;
      btnEl.innerHTML = "Ingresar al Panel";
    }
  });

  function showError(msg) {
    errorEl.textContent   = msg;
    errorEl.style.display = "block";
  }

})();
