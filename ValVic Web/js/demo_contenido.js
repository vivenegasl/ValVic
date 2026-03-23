// Chips — tono (single select)
document.getElementById('tono-chips').addEventListener('click', e => {
  const chip = e.target.closest('.chip');
  if (!chip) return;
  document.querySelectorAll('#tono-chips .chip').forEach(c => c.classList.remove('selected'));
  chip.classList.add('selected');
});

// Chips — redes (multi select, al menos 1)
document.getElementById('redes-chips').addEventListener('click', e => {
  const chip = e.target.closest('.chip');
  if (!chip) return;
  const selected = document.querySelectorAll('#redes-chips .chip.selected');
  if (chip.classList.contains('selected') && selected.length === 1) return;
  chip.classList.toggle('selected');
});

function getChipVal(containerId) {
  return [...document.querySelectorAll(`#${containerId} .chip.selected`)].map(c => c.dataset.val);
}

const loadMsgs = ['Analizando tu negocio...','Adaptando el tono...','Creando los posts...','Optimizando hashtags...'];

function generar() {
  const nombre = document.getElementById('nombre').value.trim() || 'Tu negocio';
  const tipo   = document.getElementById('tipo').value;
  const dif    = document.getElementById('diferenciador').value.trim();
  const promo  = document.getElementById('promo').value.trim();
  const tono   = getChipVal('tono-chips')[0] || 'cercano';
  const redes  = getChipVal('redes-chips');

  const btn = document.getElementById('gen-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Generando...';

  const results = document.getElementById('results');
  let mi = 0;
  results.innerHTML = `<div class="loading-wrap"><div class="loading-dots"><span></span><span></span><span></span></div><div class="loading-msg" id="lmsg">${loadMsgs[0]}</div></div>`;
  const interval = setInterval(() => {
    mi = (mi + 1) % loadMsgs.length;
    const el = document.getElementById('lmsg');
    if (el) el.textContent = loadMsgs[mi];
  }, 700);

  setTimeout(() => {
    clearInterval(interval);
    mostrarResultados(nombre, tipo, tono, redes, dif, promo, results);
    btn.disabled = false;
    btn.textContent = '✨ Regenerar contenido';
  }, 2200);
}

// ── Content library ──────────────────────────────────────────
const library = {
  restaurante: {
    cercano: {
      ig: { d:'Lunes', e:'🍝', t:(n,dif,promo)=>`¿Lunes difícil? Tenemos la solución perfecta.\n\nEn ${n} cocinamos con ingredientes frescos y mucho cariño. Ven a reconectarte.${dif?'\n\n'+dif+'.':''}${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#ComidaRica','#LunesRicos','#Gastronomía'] },
      fb: { d:'Miércoles', e:'🎉', t:(n,dif,promo)=>`¿Ya tienes plan para esta semana? 😊\n\n${n} te espera con mesas disponibles y el menú que necesitas.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#Reservas','#RestauranteChile','#ComidaCasera'] },
      li: { d:'Viernes', e:'🌿', t:(n,dif,promo)=>`En ${n} trabajamos con proveedores locales y recibimos ingredientes frescos cada mañana.\n\nCalidad honesta en cada plato.${dif?'\n\n'+dif+'.':''}`, tags:['#Gastronomía','#ProductoLocal','#Emprendimiento'] }
    },
    profesional: {
      ig: { d:'Lunes', e:'🍽️', t:(n,dif,promo)=>`Menú de temporada disponible en ${n}.\n\nIngredientes seleccionados, presentación impecable.${dif?'\n\n'+dif+'.':''}${promo?'\n\n'+promo+'.':''}`, tags:['#AltaCocina','#MenuTemporada','#Gastronomía'] },
      fb: { d:'Miércoles', e:'🥂', t:(n,dif,promo)=>`${n} — experiencia gastronómica completa.\n\nHorario: martes a domingo, 13:00–23:00 hrs.${promo?'\n\n'+promo+'.':''}`, tags:['#Restaurante','#ExperienciaGastronómica'] },
      li: { d:'Viernes', e:'📊', t:(n,dif,promo)=>`La gastronomía de calidad como diferenciador empresarial.\n\n${n} ofrece espacios para reuniones de alto nivel y eventos corporativos.${dif?'\n\n'+dif+'.':''}`, tags:['#GastronomíaEjecutiva','#EventosCorporativos'] }
    },
    divertido: {
      ig: { d:'Lunes', e:'😋', t:(n,dif,promo)=>`Psst… te tenemos un secreto 🤫\n\nLos lunes en ${n} son tranquilos, sin esperas y con la misma magia de siempre.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#SecretsOfTheMenu','#FoodieChile','#ComeSinEsperar'] },
      fb: { d:'Miércoles', e:'🎊', t:(n,dif,promo)=>`¿Buscas excusa para salir a comer rico? Nosotros te la damos 😂\n\n${n} tiene mesas disponibles y el menú perfecto para el miércoles.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#PlanesTiempo','#ComerRico'] },
      li: { d:'Viernes', e:'🚀', t:(n,dif,promo)=>`En ${n} creemos que una buena comida cambia el humor de todo el equipo.\n\n¿Tu empresa ya descubrió su restaurante favorito para celebrar logros?${dif?'\n\n'+dif+'.':''}`, tags:['#CulturaLaboral','#TeamBuilding'] }
    },
    inspirador: {
      ig: { d:'Lunes', e:'✨', t:(n,dif,promo)=>`Cada plato que sale de nuestra cocina lleva una historia.\n\n${n} nació del amor por la gastronomía honesta. Gracias por ser parte.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#GastronomíaConAlma','#FoodLovers'] },
      fb: { d:'Miércoles', e:'🌟', t:(n,dif,promo)=>`Cocinar es un acto de amor. Comer también.\n\n${n} te invita a vivir esa experiencia con las personas que más quieres.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#MomentosEspeciales','#AmorPorLaCocina'] },
      li: { d:'Viernes', e:'💡', t:(n,dif,promo)=>`Emprender en gastronomía es apostar por el encuentro entre personas.\n\n${n}: construyendo comunidad, un plato a la vez.${dif?'\n\n'+dif+'.':''}`, tags:['#Emprendimiento','#Gastronomía','#PropósitoMarca'] }
    }
  },
  clinica: {
    cercano: {
      ig: { d:'Lunes', e:'😁', t:(n,dif,promo)=>`Tu sonrisa lo dice todo 😁\n\nEn ${n} cuidamos tu salud dental con atención personalizada y sin esperas.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#SaludDental','#SonrizaSaludable','#Odontología'] },
      fb: { d:'Miércoles', e:'✨', t:(n,dif,promo)=>`¿Cuándo fue tu última limpieza dental?\n\nPrevenir siempre es más fácil (y más económico) que curar. En ${n} te esperamos con agenda disponible.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#SaludBucal','#Prevención'] },
      li: { d:'Viernes', e:'🩺', t:(n,dif,promo)=>`La salud dental impacta directamente la calidad de vida y productividad laboral.\n\nUna revisión anual puede prevenir problemas costosos. ${n} lo hace accesible.${dif?'\n\n'+dif+'.':''}`, tags:['#SaludLaboral','#Bienestar','#Odontología'] }
    },
    profesional: {
      ig: { d:'Lunes', e:'🦷', t:(n,dif,promo)=>`Tecnología de punta al servicio de tu salud bucal.\n\n${n} — diagnóstico digital de precisión y atención especializada.${promo?'\n\n'+promo+'.':''}`, tags:['#OdontologíaDigital','#SaludBucal'] },
      fb: { d:'Miércoles', e:'🔬', t:(n,dif,promo)=>`Diagnóstico con radiografía digital de baja radiación, seguro para toda la familia.\n\n${n}: precisión y seguridad en cada consulta.${promo?'\n\n'+promo+'.':''}`, tags:['#TecnologíaDental','#DiagnósticoPreciso'] },
      li: { d:'Viernes', e:'📊', t:(n,dif,promo)=>`El 60% de las enfermedades periodontales se detectan en etapas avanzadas por falta de controles.\n\n${n} ofrece protocolos preventivos completos para empresas y familias.${dif?'\n\n'+dif+'.':''}`, tags:['#SaludPublica','#OdontologíaPreventiva'] }
    },
    divertido: {
      ig: { d:'Lunes', e:'🎉', t:(n,dif,promo)=>`¡Spoiler alert! Tener los dientes limpios se nota (y mucho) 😂✨\n\n${n}: donde tu sonrisa es la protagonista.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#DentalGlow','#SonrizaPotente'] },
      fb: { d:'Miércoles', e:'😄', t:(n,dif,promo)=>`"No tengo tiempo para el dentista" — tú, hace 6 meses.\n\nEn ${n} tenemos horarios que sí te acomodan. Ya no hay excusas 😄${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#ExcusasNoBasta','#SaludDental'] },
      li: { d:'Viernes', e:'🚀', t:(n,dif,promo)=>`La salud dental no debería ser un lujo ni una molestia.\n\n${n}: hacemos que cuidar tu boca sea fácil, accesible y hasta entretenido.${dif?'\n\n'+dif+'.':''}`, tags:['#InnovaciónEnSalud','#DentalCare'] }
    },
    inspirador: {
      ig: { d:'Lunes', e:'🌟', t:(n,dif,promo)=>`Una sonrisa sana es la mejor inversión que puedes hacer en ti mismo.\n\n${n}: porque te lo mereces.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#SonrizaConfiada','#InversiónEnTuSalud'] },
      fb: { d:'Miércoles', e:'❤️', t:(n,dif,promo)=>`Cada paciente que entra a ${n} trae una historia. Nosotros ayudamos a escribir la siguiente: con salud y una sonrisa que habla por sí sola.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#HistoriasQueSanan','#SaludDental'] },
      li: { d:'Viernes', e:'💡', t:(n,dif,promo)=>`Fundamos ${n} con una convicción: la atención dental de calidad debe ser accesible para todos.\n\nGracias a quienes confían en nosotros cada día.${dif?'\n\n'+dif+'.':''}`, tags:['#PropósitoEnSalud','#Odontología'] }
    }
  },
  spa: {
    cercano: {
      ig: { d:'Lunes', e:'🌸', t:(n,dif,promo)=>`Te lo mereces — sí, tú.\n\nEn ${n} tienes una hora solo para ti. Llega y desconéctate de todo.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#Autocuidado','#RelaxMode','#Spa'] },
      fb: { d:'Miércoles', e:'💆', t:(n,dif,promo)=>`Miércoles de bienestar 🌿\n\n${n} te espera con agenda disponible. Porque el descanso no debería ser un lujo.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#BienestarTotal','#MasajeRelajante'] },
      li: { d:'Viernes', e:'🧠', t:(n,dif,promo)=>`El estrés laboral no es inevitable. Equipos que incorporan pausas de bienestar reportan hasta 34% más de productividad.\n\n${n} ofrece planes corporativos.${dif?'\n\n'+dif+'.':''}`, tags:['#WellnessLaboral','#Productividad'] }
    },
    profesional: {
      ig: { d:'Lunes', e:'✨', t:(n,dif,promo)=>`Protocolos de bienestar diseñados para cada tipo de piel y necesidad.\n\n${n}: atención personalizada desde el primer momento.${promo?'\n\n'+promo+'.':''}`, tags:['#TratamientoPersonalizado','#Bienestar','#CuidadoDePiel'] },
      fb: { d:'Miércoles', e:'🌿', t:(n,dif,promo)=>`Utilizamos productos naturales certificados, libres de parabenos y testados dermatológicamente.\n\n${n}: tu bienestar comienza con lo que aplicamos en tu piel.${promo?'\n\n'+promo+'.':''}`, tags:['#ProductosNaturales','#SkinCare'] },
      li: { d:'Viernes', e:'📋', t:(n,dif,promo)=>`El bienestar corporativo reduce el ausentismo laboral hasta un 30%.\n\n${n} ofrece planes de bienestar para equipos de trabajo.${dif?'\n\n'+dif+'.':''}`, tags:['#BienestarCorporativo','#RRHH'] }
    },
    divertido: {
      ig: { d:'Lunes', e:'🛁', t:(n,dif,promo)=>`Señal del universo: deja de decir "mañana me relajo" 😂\n\n${n} tiene agenda disponible ahora mismo. Hoy es el día.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#SelfCare','#HoyEsElDía','#Spa'] },
      fb: { d:'Miércoles', e:'😌', t:(n,dif,promo)=>`¿Tu cuerpo te está pidiendo pausa? Escúchalo 🙏\n\n${n}: masajes, faciales y aromaterapia para que llegues al fin de semana recargado.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#EscúchaTuCuerpo','#BienestarTotal'] },
      li: { d:'Viernes', e:'🚀', t:(n,dif,promo)=>`Fun fact: los equipos que se relajan juntos rinden mejor juntos.\n\n${n} tiene planes de bienestar corporativo que tu empresa debería conocer.${dif?'\n\n'+dif+'.':''}`, tags:['#CulturaLaboral','#TeamBuilding','#Wellness'] }
    },
    inspirador: {
      ig: { d:'Lunes', e:'🌙', t:(n,dif,promo)=>`Cuidarte no es egoísmo — es la base para cuidar a todos los demás.\n\n${n} te da el espacio para volver a ti misma.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#SelfLove','#Bienestar','#CuidadoFemenino'] },
      fb: { d:'Miércoles', e:'🌺', t:(n,dif,promo)=>`Cada sesión en ${n} es un recordatorio: te mereces tiempo de calidad.\n\nInvierte en ti hoy — los resultados los sientes desde la primera visita.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#InversiónEnTi','#BienestarReal'] },
      li: { d:'Viernes', e:'💡', t:(n,dif,promo)=>`Creamos ${n} porque creemos que el bienestar no debería ser un privilegio.\n\nAccesible, profesional y orientado a resultados reales.${dif?'\n\n'+dif+'.':''}`, tags:['#PropósitoMarca','#Wellness','#Emprendimiento'] }
    }
  },
  tienda: {
    cercano: {
      ig: { d:'Lunes', e:'🛍️', t:(n,dif,promo)=>`¡Llegó lo que estabas esperando! 🎉\n\nEso que tenías en mente ya está disponible en ${n}. Entra antes de que se agote.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#NuevaColección','#TiendaOnline','#ShoppingOnline'] },
      fb: { d:'Miércoles', e:'📦', t:(n,dif,promo)=>`Despacho rápido, devolución fácil y atención real.\n\n${n}: comprar online sin complicaciones.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#CompraOnline','#DespachoRápido','#TiendaOnline'] },
      li: { d:'Viernes', e:'📈', t:(n,dif,promo)=>`Crecimos 3× en ventas online apostando por una cosa: atención al cliente real y envíos rápidos.\n\nEl e-commerce no es solo tecnología — es confianza.${dif?'\n\n'+dif+'.':''}`, tags:['#Ecommerce','#CrecimientoDigital'] }
    },
    profesional: {
      ig: { d:'Lunes', e:'🎯', t:(n,dif,promo)=>`Selección curada de productos de alta calidad.\n\nEn ${n} cada ítem pasa por un proceso de evaluación riguroso antes de llegar a ti.${promo?'\n\n'+promo+'.':''}`, tags:['#CalidadGarantizada','#TiendaOnline'] },
      fb: { d:'Miércoles', e:'🔒', t:(n,dif,promo)=>`Compra con confianza: pago seguro, devolución gratuita en 30 días y soporte real.\n\n${n}: tu satisfacción es nuestra prioridad.${promo?'\n\n'+promo+'.':''}`, tags:['#CompraSegura','#SatisfacciónGarantizada'] },
      li: { d:'Viernes', e:'🌐', t:(n,dif,promo)=>`El 78% de los consumidores prefieren marcas con propósito claro.\n\n${n}: democratizando el acceso a productos de calidad sin intermediarios.${dif?'\n\n'+dif+'.':''}`, tags:['#PropósitoMarca','#RetailDigital'] }
    },
    divertido: {
      ig: { d:'Lunes', e:'😍', t:(n,dif,promo)=>`Ese producto que llevas semanas mirando… sigue disponible 👀\n\n${n} te está esperando. ¿Cuándo le das clic?${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#AddToCart','#ShoppingOnline','#TeLoDices'] },
      fb: { d:'Miércoles', e:'🎁', t:(n,dif,promo)=>`Tener buen gusto es un arte. Encontrar precios justos también 😄\n\n${n} tiene lo mejor de los dos mundos.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#BuenGusto','#CompraInteligente'] },
      li: { d:'Viernes', e:'🚀', t:(n,dif,promo)=>`Dato curioso: el 67% de las compras online ocurren por impulso… pero solo si el proceso es fácil.\n\nEn ${n} lo hicimos tan simple que da gusto.${dif?'\n\n'+dif+'.':''}`, tags:['#UXComercial','#Ecommerce','#VentasOnline'] }
    },
    inspirador: {
      ig: { d:'Lunes', e:'✨', t:(n,dif,promo)=>`Cada compra en ${n} es una forma de elegirte a ti mismo.\n\nCuídate. Regálate calidad.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#ElegirteATiMismo','#Lifestyle','#TiendaOnline'] },
      fb: { d:'Miércoles', e:'🌟', t:(n,dif,promo)=>`Creamos ${n} con una misión: que encontrar algo de calidad no sea difícil ni caro.\n\nGracias a quienes confían en nosotros.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#PropósitoMarca','#Ecommerce'] },
      li: { d:'Viernes', e:'💡', t:(n,dif,promo)=>`${n} nació de una pregunta simple: ¿por qué lo bueno tiene que ser complicado de conseguir?\n\nSeguimos trabajando para responderla cada día.${dif?'\n\n'+dif+'.':''}`, tags:['#Emprendimiento','#Propósito','#RetailDigital'] }
    }
  },
  gym: {
    cercano: {
      ig: { d:'Lunes', e:'💪', t:(n,dif,promo)=>`¡Lunes de arrancar!\n\nSi ya estás pensando en empezar a entrenar, esta es la señal. En ${n} te esperamos.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#FitnessMotivation','#Gym','#EntrenamientoChile'] },
      fb: { d:'Miércoles', e:'🏋️', t:(n,dif,promo)=>`Mito: necesitas 2 horas diarias para ver resultados.\nRealidad: 45 minutos bien enfocados 3 veces por semana transforman tu cuerpo.\n\n${n} te muestra cómo.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#FitnessRealista','#EntrenamientoEfectivo'] },
      li: { d:'Viernes', e:'🧠', t:(n,dif,promo)=>`El ejercicio regular mejora la concentración hasta un 20% y reduce el estrés laboral significativamente.\n\nInvertir en tu cuerpo es invertir en tu rendimiento.${dif?'\n\n'+dif+'.':''}`, tags:['#SaludLaboral','#FitnessEjecutivo'] }
    },
    profesional: {
      ig: { d:'Lunes', e:'🎯', t:(n,dif,promo)=>`Programas de entrenamiento personalizados según tus objetivos y nivel.\n\n${n}: tu plan, tu ritmo, tus resultados.${promo?'\n\n'+promo+'.':''}`, tags:['#EntrenamientoPersonalizado','#Fitness'] },
      fb: { d:'Miércoles', e:'📊', t:(n,dif,promo)=>`Medimos tu progreso mensualmente con análisis de composición corporal — no solo peso.\n\n${n}: resultados reales con metodología respaldada.${promo?'\n\n'+promo+'.':''}`, tags:['#MediciónDeResultados','#CienciaDelDeporte'] },
      li: { d:'Viernes', e:'🤝', t:(n,dif,promo)=>`Planes corporativos para empresas que priorizan el bienestar de sus equipos.\n\n${n}: entrenamiento en instalaciones o presencial en tu empresa.${dif?'\n\n'+dif+'.':''}`, tags:['#FitnessCorporativo','#BienestarLaboral'] }
    },
    divertido: {
      ig: { d:'Lunes', e:'🏃', t:(n,dif,promo)=>`Señal del universo: deja de decir "mañana empiezo" 😂\n\nEn ${n} siempre hay un buen momento para el primer paso.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#MañanaEmpiezo','#GymLife','#Fitness'] },
      fb: { d:'Miércoles', e:'🎊', t:(n,dif,promo)=>`Fun fact: los que van al gym los miércoles son estadísticamente más constantes 🤓\n\n¿Ya eres parte del club? ${n} te espera hoy.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#FunFitnessFact','#Gym','#Constancia'] },
      li: { d:'Viernes', e:'🚀', t:(n,dif,promo)=>`Los equipos que se mueven juntos, rinden juntos.\n\n${n} tiene el programa corporativo que tu empresa necesita — sin excusas.${dif?'\n\n'+dif+'.':''}`, tags:['#TeamBuilding','#FitnessCorporativo'] }
    },
    inspirador: {
      ig: { d:'Lunes', e:'🌅', t:(n,dif,promo)=>`Cada repetición es un voto por la persona que quieres ser.\n\n${n}: aquí construyes tu mejor versión.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#MejorVersión','#FitnessMotivation','#Gym'] },
      fb: { d:'Miércoles', e:'❤️', t:(n,dif,promo)=>`No entrenes para verte bien en fotos. Entrena para sentirte bien en tu vida.\n\n${n} te acompaña en ese camino.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#SaludReal','#Bienestar','#GymLife'] },
      li: { d:'Viernes', e:'💡', t:(n,dif,promo)=>`Creamos ${n} convencidos de que el bienestar físico y el rendimiento profesional están directamente conectados.\n\nInvierte en tu equipo hoy.${dif?'\n\n'+dif+'.':''}`, tags:['#PropósitoMarca','#Wellness','#Fitness'] }
    }
  },
  educacion: {
    cercano: {
      ig: { d:'Lunes', e:'📚', t:(n,dif,promo)=>`¿Tienes ganas de aprender algo nuevo?\n\nEn ${n} aprender es fácil, entretenido y vas a tu ritmo. ¡Empieza hoy!${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#Educación','#AprendeOnline','#Cursos'] },
      fb: { d:'Miércoles', e:'🎓', t:(n,dif,promo)=>`El mejor momento para aprender algo nuevo es ahora.\n\n${n} tiene el curso que estabas buscando — con profesores reales y comunidad activa.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#FormaCión','#Cursos','#DesarrolloPersonal'] },
      li: { d:'Viernes', e:'🧠', t:(n,dif,promo)=>`Las personas que invierten en aprendizaje continuo tienen 3× más probabilidades de ascender en los próximos 2 años.\n\n${n} te ayuda a ser uno de ellos.${dif?'\n\n'+dif+'.':''}`, tags:['#AprendizajeContinuo','#DesarrolloProfesional'] }
    },
    profesional: {
      ig: { d:'Lunes', e:'🎯', t:(n,dif,promo)=>`Programas diseñados con metodología probada y enfoque práctico.\n\n${n}: formación que se traduce en resultados reales.${promo?'\n\n'+promo+'.':''}`, tags:['#FormaciónProfesional','#Educación','#Cursos'] },
      fb: { d:'Miércoles', e:'📊', t:(n,dif,promo)=>`Más de [X] egresados en [X] países. Nuestros programas están validados por la industria.\n\n${n}: aprende de quienes lo han hecho.${promo?'\n\n'+promo+'.':''}`, tags:['#Egresados','#EducaciónDeCalidad'] },
      li: { d:'Viernes', e:'🤝', t:(n,dif,promo)=>`Formamos alianzas con empresas líderes para asegurar que nuestros programas responden a la demanda real del mercado.\n\n${n}: formación relevante, no teórica.${dif?'\n\n'+dif+'.':''}`, tags:['#EducaciónEmpresarial','#Capacitación'] }
    },
    divertido: {
      ig: { d:'Lunes', e:'🤓', t:(n,dif,promo)=>`"Aprender es aburrido" — alguien que nunca ha tomado un curso en ${n} 😂\n\nProfe bueno + comunidad activa + certificado real = diferente.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#AprendizajeDivertido','#Cursos','#Educación'] },
      fb: { d:'Miércoles', e:'🎊', t:(n,dif,promo)=>`Fun fact: el cerebro aprende mejor cuando se divierte.\n\nPor eso en ${n} diseñamos clases que no parecen clases 😄${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#CienciaDelAprendizaje','#Cursos'] },
      li: { d:'Viernes', e:'🚀', t:(n,dif,promo)=>`El upskilling ya no es opcional — es el diferenciador de los equipos de alto rendimiento.\n\n${n} lo hace accesible, dinámico y medible.${dif?'\n\n'+dif+'.':''}`, tags:['#Upskilling','#RRHH','#DesarrolloOrganizacional'] }
    },
    inspirador: {
      ig: { d:'Lunes', e:'✨', t:(n,dif,promo)=>`Lo que aprendes nadie te lo puede quitar.\n\n${n}: porque cada conocimiento nuevo es una puerta que se abre.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#PoderDelConocimiento','#Educación','#Aprendizaje'] },
      fb: { d:'Miércoles', e:'🌟', t:(n,dif,promo)=>`Cada persona que aprende algo nuevo cambia un poco su perspectiva del mundo.\n\n${n}: formando personas, no solo profesionales.${promo?'\n\n🎁 '+promo+'.':''}`, tags:['#FormandoPersonas','#EducaciónConPropósito'] },
      li: { d:'Viernes', e:'💡', t:(n,dif,promo)=>`Fundamos ${n} convencidos de que la educación de calidad debe ser accesible para todos.\n\nGracias a cada estudiante que confía en este camino.${dif?'\n\n'+dif+'.':''}`, tags:['#PropósitoEducativo','#Emprendimiento','#EdTech'] }
    }
  }
};

const plats = {
  ig: { name:'Instagram', color:'#E1306C', dias:['Lunes','Martes'] },
  fb: { name:'Facebook',  color:'#1877F2', dias:['Miércoles','Jueves'] },
  li: { name:'LinkedIn',  color:'#0A66C2', dias:['Viernes'] }
};

function mostrarResultados(nombre, tipo, tono, redes, dif, promo, results) {
  results.innerHTML = '';

  // Context banner
  const banner = document.createElement('div');
  banner.className = 'context-banner';
  banner.innerHTML = `
    <span style="font-weight:500;color:var(--ink);">Generado para:</span>
    <span class="ctx-tag">📌 ${nombre}</span>
    <span class="ctx-tag">${tono}</span>
    ${dif ? `<span class="ctx-tag">⭐ ${dif.slice(0,28)}${dif.length>28?'…':''}</span>` : ''}
    ${promo ? `<span class="ctx-tag">🎁 Promo activa</span>` : ''}`;
  results.appendChild(banner);

  const src = library[tipo]?.[tono] || library.restaurante.cercano;

  redes.forEach((r, i) => {
    const plat = plats[r];
    const post = src[r];
    if (!post) return;

    setTimeout(() => {
      const texto = post.t(nombre, dif, promo);
      const card = document.createElement('div');
      card.className = 'post-card';
      card.style.animationDelay = '0s';
      card.innerHTML = `
        <div class="post-header">
          <div class="plat-dot" style="background:${plat.color}"></div>
          <span class="plat-name">${plat.name}</span>
          <span class="post-day">${post.d}</span>
        </div>
        <div class="post-body">
          <div class="post-text">${post.e} ${texto}</div>
          <div class="post-tags">${post.tags.map(t=>`<span class="post-tag">${t}</span>`).join('')}</div>
        </div>
        <div class="post-actions">
          <button class="post-btn copy-btn">Copiar</button>
          <button class="post-btn">Editar</button>
          <button class="post-btn">Programar</button>
        </div>`;
      card.dataset.copyText = `${post.e} ${texto}

${post.tags.join(' ')}`;
      results.appendChild(card);
    }, i * 130);
  });
}

function copiar(btn, texto) {
  navigator.clipboard.writeText(texto).then(() => {
    btn.textContent = '¡Copiado!'; btn.classList.add('done');
    setTimeout(() => { btn.textContent = 'Copiar'; btn.classList.remove('done'); }, 2000);
  });
}

// ── Event listeners ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  const genBtn = document.getElementById('gen-btn');
  if (genBtn) genBtn.addEventListener('click', generar);

  // Copy button via event delegation
  const resultsEl = document.getElementById('results');
  if (resultsEl) resultsEl.addEventListener('click', e => {
    const btn = e.target.closest('.copy-btn');
    if (!btn) return;
    const card = btn.closest('[data-copy-text]');
    if (card) copiar(btn, card.dataset.copyText);
  });

  document.querySelectorAll('#tono-chips .chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('#tono-chips .chip').forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
    });
  });

  document.querySelectorAll('#redes-chips .chip').forEach(chip => {
    chip.addEventListener('click', () => chip.classList.toggle('selected'));
  });
});
