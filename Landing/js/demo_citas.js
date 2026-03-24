const ts = () => { const d=new Date(); return d.getHours()+':'+String(d.getMinutes()).padStart(2,'0'); };
let timers=[], esperando=false, bizActual='clinica', flowActual='agendar';

const biznConfig = {
  clinica:     { name:'Clínica DentaPlus', avatar:'C', theme:'theme-clinica' },
  restaurante: { name:'Restaurante Alma',  avatar:'R', theme:'theme-restaurante' },
  spa:         { name:'Spa Serenidad',     avatar:'S', theme:'theme-spa' },
  gym:         { name:'GymPro Training',   avatar:'G', theme:'theme-gym' },
};

const flujos = {
  clinica: {
    agendar: {
      inicio: {
        msgs:['¡Hola! Soy el asistente de <strong>Clínica DentaPlus</strong> 👋','¿En qué puedo ayudarte hoy?'],
        qr:['📅 Agendar una cita','🦷 Consultar servicios','📞 Hablar con alguien']
      },
      '📅 Agendar una cita': {
        msgs:['Con gusto 😊 ¿Para qué especialidad necesitas la cita?'],
        qr:['Ortodoncia','Blanqueamiento dental','Limpieza y control','Implantes']
      },
      'Ortodoncia':         { next:'elegirFecha', espec:'Ortodoncia' },
      'Blanqueamiento dental': { next:'elegirFecha', espec:'Blanqueamiento dental' },
      'Limpieza y control': { next:'elegirFecha', espec:'Limpieza y control' },
      'Implantes':          { next:'elegirFecha', espec:'Implantes' },
      elegirFecha: {
        msgs:['¿Qué fecha te acomoda mejor?'],
        qr:['Mañana','Esta semana','La próxima semana']
      },
      'Mañana':            { next:'elegirHora', fecha:'mañana' },
      'Esta semana':       { next:'elegirHora', fecha:'esta semana' },
      'La próxima semana': { next:'elegirHora', fecha:'la próxima semana' },
      elegirHora: {
        msgs:['Perfecto, tenemos disponibilidad. ¿Qué horario prefieres?'],
        qr:['09:00 AM','11:00 AM','03:00 PM','05:00 PM']
      },
      '09:00 AM': { next:'confirmar', hora:'09:00 AM' },
      '11:00 AM': { next:'confirmar', hora:'11:00 AM' },
      '03:00 PM': { next:'confirmar', hora:'03:00 PM' },
      '05:00 PM': { next:'confirmar', hora:'05:00 PM' },
      confirmar: {
        buildMsgs: (s) => [`Tu cita queda de la siguiente manera:<br><br><span class="tag">🦷 ${s.espec||'Consulta'}</span> <span class="tag">📅 ${s.fecha||'mañana'}</span> <span class="tag">🕐 ${s.hora||'09:00 AM'}</span>`,'¿Confirmo con estos datos?'],
        qr:['✅ Confirmar cita','✏️ Cambiar algo']
      },
      '✅ Confirmar cita': {
        msgs:['<div class="confirmed">✓ ¡Cita confirmada!</div><br>Te enviaremos un recordatorio por WhatsApp 24h antes. Si necesitas cambiar algo, escríbenos aquí 😊']
      },
      '✏️ Cambiar algo': {
        msgs:['Claro, ¿qué deseas modificar?'],
        qr:['🦷 La especialidad','📅 La fecha','🕐 El horario']
      },
      '🦷 La especialidad': { msgs:['¿Para qué especialidad?'], qr:['Ortodoncia','Blanqueamiento dental','Limpieza y control','Implantes'] },
      '📅 La fecha':        { msgs:['¿Qué fecha prefieres?'], qr:['Mañana','Esta semana','La próxima semana'] },
      '🕐 El horario':      { msgs:['¿Qué horario te acomoda?'], qr:['09:00 AM','11:00 AM','03:00 PM','05:00 PM'] },
      '🦷 Consultar servicios': { msgs:['Ofrecemos ortodoncia invisible, blanqueamiento LED, implantes, limpieza y más.\n\n¿Te gustaría agendar una consulta?'], qr:['📅 Sí, agendar','👋 No por ahora'] },
      '📞 Hablar con alguien': { msgs:['Con gusto. Puedes llamarnos al <strong>+56 2 2345 6789</strong> o te contactamos en minutos. ¡Hasta pronto!'] },
      '👋 No por ahora': { msgs:['Perfecto, cuando necesites estamos aquí. ¡Hasta pronto! 👋'] }
    },
    recordar: {
      inicio: {
        msgs:['Hola <strong>María José</strong> 👋','Te escribe <strong>Clínica DentaPlus</strong>.','Tienes una cita agendada para <strong>mañana</strong>:<br><br><span class="tag">🦷 Ortodoncia</span> <span class="tag">📅 Martes 19 Mar</span><br><span class="tag">🕐 10:30 AM</span> <span class="tag">👨‍⚕️ Dr. Ramírez</span>','¿Confirmas tu asistencia?'],
        qr:['✅ Confirmo','❌ Necesito cancelar','📅 Cambiar horario']
      },
      '✅ Confirmo': { msgs:['¡Perfecto! Tu cita está confirmada ✅<br><br>Recuerda llegar 10 minutos antes con tu carnet de identidad. ¡Hasta mañana! 😊'] },
      '❌ Necesito cancelar': { msgs:['Entendemos. ¿Deseas reagendar para otro día?'], qr:['📅 Sí, reagendar','❌ Solo cancelar'] },
      '📅 Cambiar horario':  { msgs:['Claro, ¿qué día te acomoda mejor?'], qr:['Jueves 21 Mar','Viernes 22 Mar','La próxima semana'] },
      '📅 Sí, reagendar':   { msgs:['Nuestro equipo te contactará en los próximos minutos para encontrar el mejor horario 😊'] },
      '❌ Solo cancelar':   { msgs:['Listo, tu cita ha sido cancelada. Cuando quieras reagendar, escríbenos aquí. ¡Hasta pronto! 👋'] },
      'Jueves 21 Mar':      { msgs:['Tu cita ha sido reagendada para el <strong>jueves 21 de marzo a las 11:00 AM</strong> ✅ ¡Hasta entonces!'] },
      'Viernes 22 Mar':     { msgs:['Tu cita ha sido reagendada para el <strong>viernes 22 de marzo a las 09:30 AM</strong> ✅ ¡Hasta entonces!'] },
      'La próxima semana':  { msgs:['Nuestro equipo te contactará para coordinar el mejor horario la próxima semana. ¡Gracias! 😊'] }
    }
  },
  restaurante: {
    agendar: {
      inicio: {
        msgs:['¡Bienvenido a <strong>Restaurante Alma</strong>! 🍽️','¿En qué puedo ayudarte?'],
        qr:['📅 Hacer una reserva','🍷 Ver el menú','📞 Contactar']
      },
      '📅 Hacer una reserva': { msgs:['¡Perfecto! ¿Para cuántas personas?'], qr:['1–2 personas','3–4 personas','5–6 personas','7 o más'] },
      '1–2 personas': { next:'elegirFecha', personas:'1–2 personas' },
      '3–4 personas': { next:'elegirFecha', personas:'3–4 personas' },
      '5–6 personas': { next:'elegirFecha', personas:'5–6 personas' },
      '7 o más':      { msgs:['Para grupos grandes te contactamos directamente. ¿Me das tu nombre y número?'], qr:['📞 Que me llamen'] },
      '📞 Que me llamen': { msgs:['¡Perfecto! Nuestro equipo te llama en los próximos 30 minutos 😊'] },
      elegirFecha: { msgs:['¿Qué fecha prefieres?'], qr:['Hoy','Mañana','Este fin de semana','Otra fecha'] },
      'Hoy':              { next:'elegirHora', fecha:'hoy' },
      'Mañana':           { next:'elegirHora', fecha:'mañana' },
      'Este fin de semana': { next:'elegirHora', fecha:'este fin de semana' },
      'Otra fecha':       { msgs:['Escríbeme la fecha y verifico disponibilidad al instante 🗓️'] },
      elegirHora: { msgs:['¿Qué horario te acomoda?'], qr:['13:00 hrs','14:30 hrs','20:00 hrs','21:30 hrs'] },
      '13:00 hrs': { next:'elegirPref', hora:'13:00 hrs' },
      '14:30 hrs': { next:'elegirPref', hora:'14:30 hrs' },
      '20:00 hrs': { next:'elegirPref', hora:'20:00 hrs' },
      '21:30 hrs': { next:'elegirPref', hora:'21:30 hrs' },
      elegirPref: { msgs:['¿Alguna preferencia especial?'], qr:['Sin preferencia','🪟 Mesa con vista','🌿 Terraza','🎂 Cumpleaños','💑 Ocasión especial'] },
      'Sin preferencia':  { next:'confirmar' },
      '🪟 Mesa con vista': { next:'confirmar', pref:'mesa con vista' },
      '🌿 Terraza':        { next:'confirmar', pref:'terraza' },
      '🎂 Cumpleaños':     { next:'confirmar', pref:'celebración de cumpleaños 🎂' },
      '💑 Ocasión especial': { next:'confirmar', pref:'ocasión especial 💑' },
      confirmar: {
        buildMsgs: (s) => [`Tu reserva:<br><br><span class="tag">👥 ${s.personas||'2'}</span> <span class="tag">📅 ${s.fecha||'mañana'}</span> <span class="tag">🕗 ${s.hora||'20:00 hrs'}</span>${s.pref?` <span class="tag">✨ ${s.pref}</span>`:''}`, '¿Confirmo?'],
        qr:['✅ Confirmar','✏️ Cambiar algo']
      },
      '✅ Confirmar': { msgs:['<div class="confirmed">✓ ¡Reserva confirmada!</div><br>Te enviamos recordatorio 2h antes. ¡Te esperamos! 🍽️'] },
      '✏️ Cambiar algo': { msgs:['¿Qué deseas cambiar?'], qr:['👥 Personas','📅 Fecha','🕗 Horario'] },
      '👥 Personas': { msgs:['¿Para cuántas personas?'], qr:['1–2 personas','3–4 personas','5–6 personas'] },
      '📅 Fecha':   { msgs:['¿Qué fecha prefieres?'], qr:['Hoy','Mañana','Este fin de semana'] },
      '🕗 Horario': { msgs:['¿Qué horario?'], qr:['13:00 hrs','14:30 hrs','20:00 hrs','21:30 hrs'] },
      '🍷 Ver el menú': { msgs:['Nuestro menú completo está en <strong>restaurantealma.cl/menu</strong> 🍽️\n\n¿Te gustaría hacer una reserva?'], qr:['📅 Sí, reservar','👋 No gracias'] },
      '📞 Contactar':   { msgs:['Llámanos al <strong>+56 2 2345 6789</strong> o escríbenos aquí mismo 😊'] },
      '👋 No gracias':  { msgs:['¡Cuando quieras visitarnos, aquí estaremos! 👋'] }
    },
    recordar: {
      inicio: {
        msgs:['Hola <strong>Carlos</strong> 👋','Te escribe <strong>Restaurante Alma</strong>.','Tienes una reserva para <strong>mañana</strong>:<br><br><span class="tag">👥 3 personas</span> <span class="tag">📅 Mar 19 Mar</span><br><span class="tag">🕗 20:00 hrs</span> <span class="tag">🎂 Cumpleaños</span>','¿Confirmas tu asistencia?'],
        qr:['✅ Confirmo','❌ Necesito cancelar','🕗 Cambiar horario']
      },
      '✅ Confirmo':         { msgs:['¡Perfecto! Tu reserva está confirmada ✅\n\nTe esperamos mañana. Recuerda que tenemos tu celebración preparada 🎂'] },
      '❌ Necesito cancelar':{ msgs:['Entendemos. ¿Quieres reagendar?'], qr:['📅 Sí, reagendar','❌ Solo cancelar'] },
      '🕗 Cambiar horario':  { msgs:['¿Qué horario te acomoda mejor?'], qr:['19:00 hrs','20:30 hrs','21:00 hrs','21:30 hrs'] },
      '📅 Sí, reagendar':   { msgs:['¡Con gusto! ¿Qué día te acomoda?'], qr:['Miércoles 20','Jueves 21','Viernes 22'] },
      '❌ Solo cancelar':   { msgs:['Listo, tu reserva ha sido cancelada. ¡Cuando quieras volver, aquí estaremos! 👋'] },
      '19:00 hrs':           { msgs:['Tu reserva ha sido cambiada a las <strong>19:00 hrs</strong> ✅ ¡Hasta mañana!'] },
      '20:30 hrs':           { msgs:['Tu reserva ha sido cambiada a las <strong>20:30 hrs</strong> ✅ ¡Hasta mañana!'] },
      '21:00 hrs':           { msgs:['Tu reserva ha sido cambiada a las <strong>21:00 hrs</strong> ✅ ¡Hasta mañana!'] },
      '21:30 hrs':           { msgs:['Tu reserva ha sido cambiada a las <strong>21:30 hrs</strong> ✅ ¡Hasta mañana!'] },
      'Miércoles 20':        { msgs:['Tu reserva ha sido reagendada para el <strong>miércoles 20 a las 20:00 hrs</strong> ✅ ¡Hasta entonces!'] },
      'Jueves 21':           { msgs:['Tu reserva ha sido reagendada para el <strong>jueves 21 a las 20:00 hrs</strong> ✅ ¡Hasta entonces!'] },
      'Viernes 22':          { msgs:['Tu reserva ha sido reagendada para el <strong>viernes 22 a las 20:00 hrs</strong> ✅ ¡Hasta entonces!'] }
    }
  },
  spa: {
    agendar: {
      inicio: { msgs:['¡Hola! Bienvenida a <strong>Spa Serenidad</strong> 🌿','¿Qué servicio deseas reservar?'], qr:['💆 Masaje relajante','✨ Facial hidratante','🔥 Piedras calientes','🌸 Aromaterapia'] },
      '💆 Masaje relajante':  { next:'elegirDuracion', serv:'Masaje relajante' },
      '✨ Facial hidratante':  { next:'elegirDuracion', serv:'Facial hidratante' },
      '🔥 Piedras calientes': { next:'elegirDuracion', serv:'Piedras calientes' },
      '🌸 Aromaterapia':      { next:'elegirDuracion', serv:'Aromaterapia' },
      elegirDuracion: { msgs:['¿Qué duración prefieres?'], qr:['30 minutos','60 minutos','90 minutos'] },
      '30 minutos': { next:'elegirFecha', dur:'30 min' },
      '60 minutos': { next:'elegirFecha', dur:'60 min' },
      '90 minutos': { next:'elegirFecha', dur:'90 min' },
      elegirFecha: { msgs:['¿Qué día te acomoda?'], qr:['Mañana','Esta semana','Este fin de semana'] },
      'Mañana':            { next:'confirmar', fecha:'mañana' },
      'Esta semana':       { next:'confirmar', fecha:'esta semana' },
      'Este fin de semana':{ next:'confirmar', fecha:'este fin de semana' },
      confirmar: {
        buildMsgs: (s) => [`Tu reserva en Spa Serenidad:<br><br><span class="tag">✨ ${s.serv||'Masaje'}</span> <span class="tag">⏱ ${s.dur||'60 min'}</span><br><span class="tag">📅 ${s.fecha||'mañana'}</span>`,'¿Confirmo?'],
        qr:['✅ Confirmar','✏️ Cambiar algo']
      },
      '✅ Confirmar':    { msgs:['<div class="confirmed">✓ ¡Reserva confirmada!</div><br>Te enviaremos recordatorio el día anterior. ¡Te esperamos con todo listo! 🌿'] },
      '✏️ Cambiar algo': { msgs:['¿Qué deseas cambiar?'], qr:['✨ El servicio','⏱ La duración','📅 La fecha'] },
      '✨ El servicio':  { msgs:['¿Qué servicio prefieres?'], qr:['💆 Masaje relajante','✨ Facial hidratante','🔥 Piedras calientes','🌸 Aromaterapia'] },
      '⏱ La duración':  { msgs:['¿Qué duración?'], qr:['30 minutos','60 minutos','90 minutos'] },
      '📅 La fecha':    { msgs:['¿Qué día te acomoda?'], qr:['Mañana','Esta semana','Este fin de semana'] }
    },
    recordar: {
      inicio: {
        msgs:['Hola <strong>Valentina</strong> 🌸','Te escribe <strong>Spa Serenidad</strong>.','Tienes una sesión agendada para <strong>mañana</strong>:<br><br><span class="tag">💆 Masaje relajante 60 min</span><br><span class="tag">📅 Mar 19 Mar</span> <span class="tag">🕐 11:00 AM</span>','¿Confirmas tu asistencia?'],
        qr:['✅ Confirmo','❌ Necesito cancelar','📅 Cambiar horario']
      },
      '✅ Confirmo':         { msgs:['¡Perfecto! Tu sesión está confirmada ✅\n\nTe recomendamos llegar 10 minutos antes para prepararte. ¡Hasta mañana! 🌿'] },
      '❌ Necesito cancelar':{ msgs:['Entendemos. ¿Quieres reagendar para otro día?'], qr:['📅 Sí, reagendar','❌ Solo cancelar'] },
      '📅 Cambiar horario':  { msgs:['¿Qué horario prefieres?'], qr:['10:00 AM','12:00 PM','03:00 PM','05:00 PM'] },
      '📅 Sí, reagendar':   { msgs:['¡Con gusto! ¿Qué día te acomoda mejor?'], qr:['Jueves 21','Viernes 22','Sábado 23'] },
      '❌ Solo cancelar':   { msgs:['Listo, tu sesión ha sido cancelada. Cuando quieras relajarte, aquí estaremos 🌸'] },
      '10:00 AM': { msgs:['Tu sesión ha sido cambiada a las <strong>10:00 AM</strong> ✅ ¡Hasta mañana!'] },
      '12:00 PM': { msgs:['Tu sesión ha sido cambiada a las <strong>12:00 PM</strong> ✅ ¡Hasta mañana!'] },
      '03:00 PM': { msgs:['Tu sesión ha sido cambiada a las <strong>03:00 PM</strong> ✅ ¡Hasta mañana!'] },
      '05:00 PM': { msgs:['Tu sesión ha sido cambiada a las <strong>05:00 PM</strong> ✅ ¡Hasta mañana!'] },
      'Jueves 21':  { msgs:['Tu sesión ha sido reagendada para el <strong>jueves 21 a las 11:00 AM</strong> ✅ ¡Hasta entonces!'] },
      'Viernes 22': { msgs:['Tu sesión ha sido reagendada para el <strong>viernes 22 a las 11:00 AM</strong> ✅ ¡Hasta entonces!'] },
      'Sábado 23':  { msgs:['Tu sesión ha sido reagendada para el <strong>sábado 23 a las 10:00 AM</strong> ✅ ¡Hasta entonces!'] }
    }
  },
  gym: {
    agendar: {
      inicio: { msgs:['¡Hola! Bienvenido a <strong>GymPro Training</strong> 💪','¿Qué clase deseas reservar?'], qr:['🚴 Spinning','🏋️ CrossFit','🧘 Yoga','⚡ HIIT Express'] },
      '🚴 Spinning':    { next:'elegirHorario', clase:'Spinning' },
      '🏋️ CrossFit':   { next:'elegirHorario', clase:'CrossFit' },
      '🧘 Yoga':        { next:'elegirHorario', clase:'Yoga restaurativo' },
      '⚡ HIIT Express':{ next:'elegirHorario', clase:'HIIT Express' },
      elegirHorario: { msgs:['¿Qué horario prefieres?'], qr:['06:30 AM','08:00 AM','12:00 PM','06:00 PM','07:30 PM'] },
      '06:30 AM': { next:'elegirDia', hora:'06:30 AM' },
      '08:00 AM': { next:'elegirDia', hora:'08:00 AM' },
      '12:00 PM': { next:'elegirDia', hora:'12:00 PM' },
      '06:00 PM': { next:'elegirDia', hora:'06:00 PM' },
      '07:30 PM': { next:'elegirDia', hora:'07:30 PM' },
      elegirDia: { msgs:['¿Para qué día?'], qr:['Mañana','Lunes','Miércoles','Viernes'] },
      'Mañana':    { next:'confirmar', dia:'mañana' },
      'Lunes':     { next:'confirmar', dia:'el lunes' },
      'Miércoles': { next:'confirmar', dia:'el miércoles' },
      'Viernes':   { next:'confirmar', dia:'el viernes' },
      confirmar: {
        buildMsgs: (s) => [`Tu reserva en GymPro:<br><br><span class="tag">💪 ${s.clase||'Clase'}</span> <span class="tag">🕐 ${s.hora||'06:00 PM'}</span><br><span class="tag">📅 ${s.dia||'mañana'}</span>`,'¿Confirmo?'],
        qr:['✅ Confirmar','✏️ Cambiar algo']
      },
      '✅ Confirmar':    { msgs:['<div class="confirmed">✓ ¡Clase reservada!</div><br>Te enviamos recordatorio 2h antes. ¡Trae agua y energía! 🔥'] },
      '✏️ Cambiar algo': { msgs:['¿Qué cambias?'], qr:['💪 La clase','🕐 El horario','📅 El día'] },
      '💪 La clase':  { msgs:['¿Qué clase?'], qr:['🚴 Spinning','🏋️ CrossFit','🧘 Yoga','⚡ HIIT Express'] },
      '🕐 El horario':{ msgs:['¿Qué horario?'], qr:['06:30 AM','08:00 AM','12:00 PM','06:00 PM','07:30 PM'] },
      '📅 El día':    { msgs:['¿Qué día?'], qr:['Mañana','Lunes','Miércoles','Viernes'] }
    },
    recordar: {
      inicio: {
        msgs:['¡Hola <strong>Diego</strong>! 💪','Te escribe <strong>GymPro Training</strong>.','Tienes clase reservada para <strong>mañana</strong>:<br><br><span class="tag">🚴 Spinning</span> <span class="tag">📅 Mar 19 Mar</span><br><span class="tag">🕐 06:30 AM</span> <span class="tag">Sala A</span>','¿Confirmas tu asistencia?'],
        qr:['✅ Confirmo','❌ No puedo ir','🕐 Cambiar horario']
      },
      '✅ Confirmo':    { msgs:['¡Genial! Tu clase está confirmada ✅\n\nRecuerda traer agua y toalla. ¡Nos vemos mañana a las 6:30! 🔥'] },
      '❌ No puedo ir': { msgs:['Sin problema. ¿Quieres reservar para otro día?'], qr:['📅 Sí, cambiar','❌ Solo cancelar'] },
      '🕐 Cambiar horario': { msgs:['¿Qué horario prefieres?'], qr:['08:00 AM','12:00 PM','06:00 PM','07:30 PM'] },
      '📅 Sí, cambiar': { msgs:['¿Qué día?'], qr:['Miércoles','Jueves','Viernes','Sábado'] },
      '❌ Solo cancelar': { msgs:['Listo, tu clase ha sido cancelada. ¡Nos vemos en la próxima! 💪'] },
      '08:00 AM': { msgs:['Tu clase ha sido cambiada a las <strong>08:00 AM</strong> ✅ ¡Hasta mañana!'] },
      '12:00 PM': { msgs:['Tu clase ha sido cambiada a las <strong>12:00 PM</strong> ✅ ¡Hasta mañana!'] },
      '06:00 PM': { msgs:['Tu clase ha sido cambiada a las <strong>06:00 PM</strong> ✅ ¡Hasta mañana!'] },
      '07:30 PM': { msgs:['Tu clase ha sido cambiada a las <strong>07:30 PM</strong> ✅ ¡Hasta mañana!'] },
      'Miércoles': { msgs:['Tu clase ha sido reagendada para el <strong>miércoles a las 06:30 AM</strong> ✅ ¡Hasta entonces!'] },
      'Jueves':    { msgs:['Tu clase ha sido reagendada para el <strong>jueves a las 06:30 AM</strong> ✅ ¡Hasta entonces!'] },
      'Viernes':   { msgs:['Tu clase ha sido reagendada para el <strong>viernes a las 06:30 AM</strong> ✅ ¡Hasta entonces!'] },
      'Sábado':    { msgs:['Tu clase ha sido reagendada para el <strong>sábado a las 08:00 AM</strong> ✅ ¡Hasta entonces!'] }
    }
  }
};

const flowDescriptions = {
  agendar: [
    { n:'Cliente escribe al WhatsApp', p:'El asistente responde al instante, las 24 horas, sin que nadie en tu equipo haga nada.' },
    { n:'Elige servicio, fecha y horario', p:'Guía al cliente paso a paso con opciones claras. Sin confusión ni llamadas de ida y vuelta.' },
    { n:'Confirmación inmediata', p:'El cliente recibe confirmación al instante y queda registrado en tu sistema automáticamente.' },
    { n:'Recordatorio automático', p:'24h antes de la cita, el sistema le escribe solo para confirmar o reprogramar.' }
  ],
  recordar: [
    { n:'Detección de cita próxima', p:'El sistema revisa tu agenda y detecta citas para las próximas 24–48 horas automáticamente.' },
    { n:'Mensaje personalizado', p:'Envía un WhatsApp con el nombre del cliente, servicio, fecha y hora exacta.' },
    { n:'El cliente responde con un clic', p:'Confirma, cancela o cambia horario sin llamar a nadie. Todo queda registrado.' },
    { n:'Notificación a tu equipo', p:'Si cancela, tu equipo recibe alerta al instante y puede ofrecer el cupo a lista de espera.' }
  ]
};

let estado = {};

function setFlow(f, btn) {
  flowActual = f;
  document.querySelectorAll('.ftab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderFlow();
  reiniciar();
}

function renderFlow() {
  const steps = flowDescriptions[flowActual];
  document.getElementById('flow-steps').innerHTML = steps.map((s, i) => `
    <div class="flow-step">
      <div class="step-dot">${i+1}</div>
      <div class="step-content"><h4>${s.n}</h4><p>${s.p}</p></div>
    </div>`).join('');
}

function setBiz(biz, chip) {
  bizActual = biz;
  document.querySelectorAll('.biz-chip').forEach(c => c.classList.remove('active'));
  chip.classList.add('active');
  const cfg = biznConfig[biz];
  const phone = document.getElementById('phone');
  phone.className = `phone ${cfg.theme}`;
  document.getElementById('phone-avatar').textContent = cfg.avatar;
  document.getElementById('phone-name').textContent = cfg.name;
  reiniciar();
}

function reiniciar() {
  timers.forEach(clearTimeout); timers = []; esperando = false; estado = {};
  document.getElementById('chat').innerHTML = '';
  ocultarQR();
  setTimeout(() => ejecutar('inicio'), 300);
}

function addTyping() {
  removeTyping();
  const chat = document.getElementById('chat');
  const t = document.createElement('div');
  t.className = 'typing'; t.id = 'typ';
  t.innerHTML = '<span></span><span></span><span></span>';
  chat.appendChild(t);
  setTimeout(() => t.classList.add('visible'), 40);
  chat.scrollTop = chat.scrollHeight;
}
function removeTyping() { const t = document.getElementById('typ'); if(t) t.remove(); }

function addBotMsg(html) {
  removeTyping();
  const chat = document.getElementById('chat');
  const d = document.createElement('div');
  d.className = 'msg bot';
  d.innerHTML = html + `<div class="msg-time">${ts()}</div>`;
  chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
}
function addUserMsg(text) {
  const chat = document.getElementById('chat');
  const d = document.createElement('div');
  d.className = 'msg user';
  d.innerHTML = text + `<div class="msg-time">${ts()}</div>`;
  chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
}

function mostrarQR(opts) {
  const qz = document.getElementById('qr-zone');
  qz.classList.remove('hidden');
  qz.innerHTML = '';
  opts.forEach(q => {
    const btn = document.createElement('button');
    btn.className = 'qr';
    btn.textContent = q;
    btn.dataset.opcion = q;
    qz.appendChild(btn);
  });
  esperando = true;
}
function ocultarQR() {
  const qz = document.getElementById('qr-zone');
  qz.classList.add('hidden'); qz.innerHTML = ''; esperando = false;
}

function ejecutar(clave) {
  const flujo = flujos[bizActual][flowActual];
  const nodo = flujo[clave];
  if (!nodo) return;
  if (nodo.next) {
    if (nodo.personas) estado.personas = nodo.personas;
    if (nodo.espec)    estado.espec    = nodo.espec;
    if (nodo.fecha)    estado.fecha    = nodo.fecha;
    if (nodo.hora)     estado.hora     = nodo.hora;
    if (nodo.dur)      estado.dur      = nodo.dur;
    if (nodo.serv)     estado.serv     = nodo.serv;
    if (nodo.clase)    estado.clase    = nodo.clase;
    if (nodo.dia)      estado.dia      = nodo.dia;
    ejecutar(nodo.next); return;
  }
  const msgs = nodo.buildMsgs ? nodo.buildMsgs(estado) : (nodo.msgs || []);
  let delay = 0;
  msgs.forEach((msg, i) => {
    const t1 = setTimeout(() => addTyping(), delay + 300);
    const t2 = setTimeout(() => {
      addBotMsg(msg);
      if (i === msgs.length - 1 && nodo.qr) mostrarQR(nodo.qr);
    }, delay + 1300);
    timers.push(t1, t2); delay += 1500;
  });
}

function elegir(opcion) {
  if (!esperando) return;
  ocultarQR(); addUserMsg(opcion);
  const flujo = flujos[bizActual][flowActual];
  const nodo = flujo[opcion];
  if (nodo) {
    if (nodo.personas) estado.personas = nodo.personas;
    if (nodo.pref)     estado.pref     = nodo.pref;
    if (nodo.fecha)    estado.fecha    = nodo.fecha;
    if (nodo.hora)     estado.hora     = nodo.hora;
  }
  const t = setTimeout(() => ejecutar(opcion), 500);
  timers.push(t);
}

// Init
renderFlow();
const cfg = biznConfig[bizActual];
document.getElementById('phone').className = `phone ${cfg.theme}`;
reiniciar();


// ── Event listeners (CSP-safe, no inline onclick) ────────────
document.addEventListener('DOMContentLoaded', () => {

  // QR option buttons via event delegation
  const qzEl = document.getElementById('qr-zone');
  if (qzEl) qzEl.addEventListener('click', e => {
    const btn = e.target.closest('[data-opcion]');
    if (btn) elegir(btn.dataset.opcion);
  });

  // Flow tabs
  document.querySelectorAll('.ftab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ftab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      setFlow(btn.dataset.flow || btn.textContent.toLowerCase().includes('recordar') ? 'recordar' : 'agendar', btn);
    });
  });

  // Business chips
  document.querySelectorAll('.biz-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.biz-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      setBiz(chip.dataset.biz || chip.textContent.trim().toLowerCase().split(' ').pop(), chip);
    });
  });

  // Restart button
  const restartBtn = document.getElementById('restart-btn');
  if (restartBtn) restartBtn.addEventListener('click', reiniciar);
});
