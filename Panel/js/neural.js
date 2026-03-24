/**
 * neural.js
 * Animación de red neuronal en canvas para el hero.
 */

(function () {
  const canvas = document.getElementById("neural");
  if (!canvas) return;

  const ctx  = canvas.getContext("2d");
  const N    = 95;
  const CONN = 175;
  const HUBS = 10;

  let W, H, nodes = [], mouse = { x: -9999, y: -9999 };

  function resize() {
    W = canvas.width  = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }

  function init() {
    resize();
    nodes = Array.from({ length: N }, (_, i) => ({
      x:          Math.random() * W,
      y:          Math.random() * H,
      vx:         (Math.random() - 0.5) * 0.5,
      vy:         (Math.random() - 0.5) * 0.5,
      isHub:      i < HUBS,
      baseR:      i < HUBS ? Math.random() * 2.5 + 3 : Math.random() * 1.5 + 1,
      pulse:      Math.random() * Math.PI * 2,
      pulseSpeed: Math.random() * 0.025 + 0.008,
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);

    // Conexiones
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      for (let j = i + 1; j < nodes.length; j++) {
        const b  = nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const d  = Math.sqrt(dx * dx + dy * dy);
        if (d < CONN) {
          const near  = Math.hypot(a.x - mouse.x, a.y - mouse.y) < 140
                     || Math.hypot(b.x - mouse.x, b.y - mouse.y) < 140;
          const alpha = (1 - d / CONN) * (near ? 0.65 : 0.2);
          const g     = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
          g.addColorStop(0,   `rgba(16,185,129,${alpha})`);
          g.addColorStop(0.5, `rgba(52,211,153,${alpha * 0.5})`);
          g.addColorStop(1,   `rgba(16,185,129,${alpha})`);
          ctx.beginPath();
          ctx.strokeStyle = g;
          ctx.lineWidth   = near ? 1.3 : 0.65;
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }

    // Nodos
    nodes.forEach((n) => {
      n.pulse += n.pulseSpeed;
      const pm     = Math.sin(n.pulse) * 0.35 + 1;
      const r      = n.baseR * pm;
      const near   = Math.hypot(n.x - mouse.x, n.y - mouse.y) < 140;
      const bright = near ? 1 : n.isHub ? 0.85 : 0.6;
      const gr     = r * (near ? 6 : n.isHub ? 5 : 3.5);

      const grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, gr);
      grd.addColorStop(0,    `rgba(16,185,129,${bright * 0.45})`);
      grd.addColorStop(0.35, `rgba(16,185,129,${bright * 0.15})`);
      grd.addColorStop(1,    "rgba(16,185,129,0)");
      ctx.beginPath();
      ctx.arc(n.x, n.y, gr, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = near
        ? `rgba(110,231,183,${bright})`
        : `rgba(16,185,129,${bright})`;
      ctx.fill();

      if (n.isHub || near) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, r * 0.38, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${bright * 0.65})`;
        ctx.fill();
      }

      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > W) n.vx *= -1;
      if (n.y < 0 || n.y > H) n.vy *= -1;
    });

    requestAnimationFrame(draw);
  }

  // Mouse tracking en la sección hero (no en el canvas, que tiene pointer-events:none)
  const heroSection = canvas.parentElement;
  heroSection.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
  });
  heroSection.addEventListener("mouseleave", () => {
    mouse.x = -9999;
    mouse.y = -9999;
  });

  window.addEventListener("resize", resize);
  init();
  draw();
})();
