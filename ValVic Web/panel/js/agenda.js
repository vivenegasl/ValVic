/**
 * agenda.js — ValVic CRM Panel
 * Lógica del panel de agenda: fetch, render, filtros, sidebar móvil.
 * Sin inline styles ni eval. CSP-compliant.
 */

(function () {
  "use strict";

  // ── Constantes ────────────────────────────────────────────────────────────
  const API_URL     = "/api/agenda";
  const POLL_MS     = 60_000;       // Refresco automático cada 60 s
  let   allCitas    = [];           // Almacén local para filtros
  let   activeFilter = "all";

  // ── Elementos DOM ─────────────────────────────────────────────────────────
  const container    = document.getElementById("agenda-container");
  const statTotal    = document.getElementById("stat-total");
  const statIa       = document.getElementById("stat-ia");
  const statPending  = document.getElementById("stat-pending");
  const btnRefresh   = document.getElementById("btn-refresh");
  const btnLogout    = document.getElementById("btn-logout");
  const btnMenu      = document.getElementById("btn-menu");
  const sidebar      = document.getElementById("sidebar");
  const overlay      = document.getElementById("sidebar-overlay");
  const pillBtns     = document.querySelectorAll(".pill-btn");

  // ── Sidebar móvil ─────────────────────────────────────────────────────────
  function openSidebar() {
    sidebar.classList.add("sidebar--open");
    overlay.classList.add("sidebar-overlay--open");
    overlay.removeAttribute("aria-hidden");
    btnMenu.setAttribute("aria-expanded", "true");
  }

  function closeSidebar() {
    sidebar.classList.remove("sidebar--open");
    overlay.classList.remove("sidebar-overlay--open");
    overlay.setAttribute("aria-hidden", "true");
    btnMenu.setAttribute("aria-expanded", "false");
  }

  if (btnMenu)  btnMenu.addEventListener("click", openSidebar);
  if (overlay)  overlay.addEventListener("click", closeSidebar);

  // ── Cerrar sesión ─────────────────────────────────────────────────────────
  if (btnLogout) {
    btnLogout.addEventListener("click", function () {
      // En producción: fetch('/api/logout', {method:'POST'}) para invalidar JWT
      window.location.href = "login.html";
    });
  }

  // ── Filtros por estado ────────────────────────────────────────────────────
  pillBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      pillBtns.forEach(function (b) { b.classList.remove("pill-btn--active"); });
      btn.classList.add("pill-btn--active");
      activeFilter = btn.dataset.filter;
      renderAgenda(allCitas);
    });
  });

  // ── Botón refrescar ───────────────────────────────────────────────────────
  if (btnRefresh) {
    btnRefresh.addEventListener("click", function () {
      btnRefresh.disabled = true;
      btnRefresh.querySelector("i").classList.add("ph-spin");
      fetchAgenda().finally(function () {
        btnRefresh.disabled = false;
        btnRefresh.querySelector("i").classList.remove("ph-spin");
      });
    });
  }

  // ── Fetch ─────────────────────────────────────────────────────────────────
  async function fetchAgenda() {
    showLoading();
    try {
      const res = await fetch(API_URL, { credentials: "include" });
      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      allCitas = data.citas || [];
      renderStats(allCitas);
      renderAgenda(allCitas);
    } catch (err) {
      console.error("[agenda.js] fetchAgenda error:", err);
      showError();
    }
  }

  // ── Render estadísticas ───────────────────────────────────────────────────
  function renderStats(citas) {
    if (statTotal)   statTotal.textContent   = citas.length;
    if (statPending) statPending.textContent = citas.filter(function (c) {
      return c.estado_cita === "pendiente_confirmacion";
    }).length;
    // "Mes actual" = mes del sistema (datos reales vendrán del backend)
    const now = new Date();
    if (statIa) statIa.textContent = citas.filter(function (c) {
      const d = new Date(c.created_at || c.updated_at);
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
    }).length;
  }

  // ── Render tabla de agenda ────────────────────────────────────────────────
  function renderAgenda(citas) {
    // Aplicar filtro
    const filtered = activeFilter === "all"
      ? citas
      : citas.filter(function (c) { return c.estado_cita === activeFilter; });

    if (filtered.length === 0) {
      showEmpty();
      return;
    }

    // Construir filas con createElement (sin innerHTML masivo para evitar XSS)
    const frag = document.createDocumentFragment();

    // Header
    frag.appendChild(buildHeaderRow());

    // Delay escalonado para animación de entrada
    filtered.forEach(function (cita, i) {
      const row = buildCitaRow(cita);
      row.style.animationDelay = (i * 40) + "ms";
      frag.appendChild(row);
    });

    container.innerHTML = "";
    container.appendChild(frag);
  }

  // ── Fila de encabezado ────────────────────────────────────────────────────
  function buildHeaderRow() {
    const row = document.createElement("div");
    row.className = "agenda-item agenda-header";
    row.setAttribute("role", "row");
    ["Fecha / Hora", "Cliente", "Servicio / Etapa", "Estado", "Acción"].forEach(function (txt) {
      const cell = document.createElement("span");
      cell.setAttribute("role", "columnheader");
      cell.textContent = txt;
      row.appendChild(cell);
    });
    return row;
  }

  // ── Fila de cita ────────────────────────────────────────────────────────
  function buildCitaRow(cita) {
    const row = document.createElement("div");
    row.className = "agenda-item";
    row.setAttribute("role", "listitem");

    // ── Columna 1: Fecha/Hora ──
    const dt = cita.created_at || cita.updated_at;
    const date = dt ? new Date(dt) : null;
    const timeCell = document.createElement("div");
    timeCell.className = "time-badge";
    const hourEl = document.createElement("span");
    hourEl.className = "time-hour";
    hourEl.textContent = date ? date.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit" }) : "—";
    const dateEl = document.createElement("span");
    dateEl.className = "time-date";
    dateEl.textContent = date ? date.toLocaleDateString("es-CL", { day: "2-digit", month: "short" }) : "";
    timeCell.appendChild(hourEl);
    timeCell.appendChild(dateEl);
    row.appendChild(timeCell);

    // ── Columna 2: Paciente/Cliente ──
    const patCell = document.createElement("div");
    patCell.className = "patient-info";
    const nameEl = document.createElement("span");
    nameEl.className = "patient-name";
    nameEl.textContent = sanitize(cita.nombre_negocio || "Lead Autogenerado");
    const phoneEl = document.createElement("span");
    phoneEl.className = "patient-phone";
    phoneEl.textContent = sanitize(cita.telefono || "—");
    patCell.appendChild(nameEl);
    patCell.appendChild(phoneEl);
    row.appendChild(patCell);

    // ── Columna 3: Servicio/Etapa ──
    const svcCell = document.createElement("div");
    const svcTag = document.createElement("span");
    svcTag.className = "service-tag";
    const etapa = cita.servicio_acordado || cita.etapa_crm || "—";
    svcTag.textContent = etapa.replace(/_/g, " ");
    svcCell.appendChild(svcTag);
    row.appendChild(svcCell);

    // ── Columna 4: Estado ──
    const statusCell = document.createElement("div");
    const badge = document.createElement("span");
    const estado = cita.estado_cita || "pendiente_confirmacion";
    badge.className = "badge-status status-" + estado;
    badge.textContent = estadoLabel(estado);
    statusCell.appendChild(badge);
    row.appendChild(statusCell);

    // ── Columna 5: Acciones ──
    const actCell = document.createElement("div");
    const waLink = document.createElement("a");
    const tel = (cita.telefono || "").replace(/\D/g, "");
    waLink.href = "https://wa.me/" + tel;
    waLink.target = "_blank";
    waLink.rel = "noopener noreferrer";
    waLink.className = "action-btn action-btn--wa";
    waLink.title = "Continuar chat en WhatsApp";
    waLink.setAttribute("aria-label", "Abrir WhatsApp con " + (cita.nombre_negocio || cita.telefono));
    const waIcon = document.createElement("i");
    waIcon.className = "ph ph-whatsapp-logo";
    waIcon.setAttribute("aria-hidden", "true");
    waLink.appendChild(waIcon);
    actCell.appendChild(waLink);
    row.appendChild(actCell);

    return row;
  }

  // ── Helpers de UI ──────────────────────────────────────────────────────────
  function showLoading() {
    container.innerHTML = "";
    const div = document.createElement("div");
    div.className = "agenda-loading";
    const spinner = document.createElement("div");
    spinner.className = "spinner";
    spinner.setAttribute("aria-hidden", "true");
    const txt = document.createElement("span");
    txt.textContent = "Cargando citas en tiempo real…";
    div.appendChild(spinner);
    div.appendChild(txt);
    container.appendChild(div);
  }

  function showEmpty() {
    container.innerHTML = "";
    const div = document.createElement("div");
    div.className = "agenda-empty";
    const icon = document.createElement("i");
    icon.className = "ph ph-calendar-blank";
    icon.style.fontSize = "36px";
    icon.style.opacity = ".35";
    icon.setAttribute("aria-hidden", "true");
    const txt = document.createElement("span");
    txt.textContent = activeFilter === "all"
      ? "No hay citas registradas aún."
      : "No hay citas con este filtro activo.";
    div.appendChild(icon);
    div.appendChild(txt);
    container.appendChild(div);
  }

  function showError() {
    container.innerHTML = "";
    const div = document.createElement("div");
    div.className = "agenda-error";
    const icon = document.createElement("i");
    icon.className = "ph ph-warning-circle";
    icon.style.fontSize = "32px";
    icon.setAttribute("aria-hidden", "true");
    const strong = document.createElement("strong");
    strong.textContent = "Backend desconectado";
    const txt = document.createTextNode(" — inicia el servidor para ver datos reales.");
    const cmd = document.createElement("code");
    cmd.className = "error-cmd";
    cmd.textContent = "uvicorn agente_conversacion:app --host 0.0.0.0 --port 8001";
    div.appendChild(icon);
    div.appendChild(strong);
    div.appendChild(txt);
    div.appendChild(cmd);
    container.appendChild(div);
  }

  function estadoLabel(estado) {
    const labels = {
      confirmada:             "Confirmada",
      pendiente_confirmacion: "Pendiente",
      realizada:              "Realizada",
      cancelada:              "Cancelada",
      reagendada:             "Reagendada",
    };
    return labels[estado] || estado.replace(/_/g, " ");
  }

  /** Sanitiza texto antes de insertarlo como textContent (xss-safe para DOM) */
  function sanitize(str) {
    if (typeof str !== "string") return "";
    return str.trim().slice(0, 200);
  }

  // ── Scroll reveal (reutiliza clase .rv de la landing) ─────────────────────
  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) e.target.classList.add("visible");
    });
  }, { threshold: 0.1 });
  document.querySelectorAll(".rv").forEach(function (el) { observer.observe(el); });

  // ── Inicialización ─────────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", function () {
    fetchAgenda();
    // Auto-refresh cada minuto
    setInterval(fetchAgenda, POLL_MS);
  });

})();
