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
      const target = document.querySelector(a.getAttribute("href"));
      if (target) {
        e.preventDefault();
        window.closeMobile();
        target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  // ── Cursor glow ───────────────────────────────────────────
  const glow = document.getElementById("cursor-glow");
  if (glow) {
    document.addEventListener("mousemove", (e) => {
      glow.style.left = e.clientX + "px";
      glow.style.top  = e.clientY + "px";
    });
  }
})();
