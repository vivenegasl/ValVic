/**
 * mockup.js
 * Chat animado en la sección de servicios/demos.
 */

(function () {
  const chat = document.getElementById("mockup-chat");
  if (!chat) return;

  const convs = [
    [
      { t: "bot",  m: "Hola 👋 ¿En qué puedo ayudarte?" },
      { t: "user", m: "Quiero agendar una cita" },
      { t: "bot",  m: "¿Para qué día te acomoda?" },
      { t: "user", m: "Mañana por la tarde" },
      { t: "bot",  m: "Listo ✅ Reserva confirmada para mañana a las 3:00 PM." },
    ],
    [
      { t: "bot",  m: "Recordatorio 📅 Tu cita es mañana a las 10:30 AM." },
      { t: "user", m: "✅ Confirmo" },
      { t: "bot",  m: "¡Perfecto! Te esperamos. Recuerda llegar 10 min antes 😊" },
    ],
    [
      { t: "user", m: "¿Tienen disponibilidad este viernes?" },
      { t: "bot",  m: "Sí, tenemos las 14:00 y 16:30 hrs. ¿Cuál prefieres?" },
      { t: "user", m: "Las 14:00 hrs" },
      { t: "bot",  m: "¡Reservado! 🎉 Recibirás un recordatorio 24h antes." },
    ],
  ];

  let ci = 0;

  function timeStr() {
    return new Date().toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
  }

  function addMsg(cls, html) {
    const d = document.createElement("div");
    d.className = cls;
    d.style.animationDelay = "0s";
    d.innerHTML = html + `<div class="mockup-msg-time">${timeStr()}</div>`;
    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;
  }

  function runConv() {
    chat.innerHTML = "";
    const msgs = convs[ci % convs.length];
    ci++;
    let delay = 600;

    msgs.forEach((msg) => {
      if (msg.t === "bot") {
        setTimeout(() => {
          const typ = document.createElement("div");
          typ.className = "mockup-typing show";
          typ.innerHTML = "<span></span><span></span><span></span>";
          chat.appendChild(typ);
          chat.scrollTop = chat.scrollHeight;
          setTimeout(() => {
            typ.remove();
            addMsg("mockup-msg bot", msg.m);
          }, 900);
        }, delay);
        delay += 1400;
      } else {
        setTimeout(() => addMsg("mockup-msg user", msg.m), delay);
        delay += 1200;
      }
    });

    setTimeout(runConv, delay + 2800);
  }

  setTimeout(runConv, 1200);
})();
