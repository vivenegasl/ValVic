/**
 * animations.js
 * Scroll reveal y contadores animados.
 */

(function () {
  // ── Scroll reveal ─────────────────────────────────────────
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) e.target.classList.add("visible");
      });
    },
    { threshold: 0.12 }
  );
  document.querySelectorAll(".rv").forEach((el) => observer.observe(el));

  // ── Contadores animados ───────────────────────────────────
  let countersRan = false;

  function animateCounters() {
    document.querySelectorAll("[data-count]").forEach((el) => {
      const target = parseInt(el.dataset.count, 10);
      const prefix = el.dataset.prefix || "";
      const suffix = el.dataset.suffix !== undefined ? el.dataset.suffix : "";
      let cur      = 0;
      const step   = Math.max(1, Math.ceil(target / 45));

      const timer = setInterval(() => {
        cur = Math.min(cur + step, target);
        el.textContent = prefix + cur + suffix;
        if (cur >= target) clearInterval(timer);
      }, 28);
    });
  }

  const statsEl = document.querySelector(".hero-stats");
  if (statsEl) {
    new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting && !countersRan) {
          countersRan = true;
          animateCounters();
        }
      },
      { threshold: 0.5 }
    ).observe(statsEl);
  }
})();
