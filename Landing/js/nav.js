/**
 * nav.js
 * Navegación: scroll sticky, menú móvil, smooth scroll.
 */

(function () {
  // ── Sticky nav ────────────────────────────────────────────
  const nav = document.getElementById("nav");
  if (nav) {
    window.addEventListener("scroll", () => {
      nav.classList.toggle("scrolled", window.scrollY > 20);
    });
  }

  // ── Mobile menu (event listeners — CSP compliant) ────────
  function toggleMobile() {
    document.getElementById("mobile-nav")?.classList.toggle("open");
  }

  function closeMobile() {
    document.getElementById("mobile-nav")?.classList.remove("open");
  }

  const mobileBtn = document.querySelector(".mobile-btn");
  if (mobileBtn) mobileBtn.addEventListener("click", toggleMobile);

  document.querySelectorAll("#mobile-nav a").forEach((a) => {
    a.addEventListener("click", closeMobile);
  });

  // ── Smooth scroll para links internos ─────────────────────
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener("click", (e) => {
      const href = a.getAttribute("href");
      if (href === "#") return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        closeMobile();
        target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  // ── Cursor glow ───────────────────────────────────────────
  const glow = document.getElementById("cursor-glow");
  if (glow) {
    document.addEventListener("mousemove", (e) => {
      glow.style.left = e.clientX + "px";
      glow.style.top = e.clientY + "px";

      const isHero = e.target.closest(".hero");
      // Mapeo exhaustivo de secciones oscuras
      const isDark = e.target.closest(".hero, .services-section, .pricing-section, .rubros-section, footer");

      if (isHero) {
        glow.style.opacity = "0";
      } else {
        glow.style.opacity = "1";
        if (isDark) {
          // Fondos Oscuros -> Esmeralda (Consistencia con Panel)

          glow.style.background = "radial-gradient(circle, rgba(225,29,72,0.12) 0%, transparent 70%)";
        } else {
          // Fondos Blancos/Claros -> Rubí (Contraste Máximo)
          glow.style.background = "radial-gradient(circle, rgba(16,185,129,0.18) 0%, transparent 70%)";
        }
      }
    });
  }
})();
