/* ══════════════════════════
   DATA POR TIPO DE NEGOCIO
══════════════════════════ */
const datos = {
  restaurante: {
    nombre: 'Restaurante',
    kpis: [
      { label:'Ingresos semana', value:'$1.284.000', delta:'+12%', dir:'up', sub:'vs semana anterior', color:'blue' },
      { label:'Clientes atendidos', value:'312', delta:'+8%', dir:'up', sub:'comensales esta semana', color:'green' },
      { label:'Ticket promedio', value:'$4.115', delta:'+3%', dir:'up', sub:'por persona', color:'amber' },
      { label:'Reservas canceladas', value:'14', delta:'-5%', dir:'up', sub:'vs semana anterior', color:'red' },
    ],
    ingresos: [180,210,165,290,320,180,0],
    ingresosPrev: [160,190,155,250,280,160,0],
    clientes: [38,45,30,62,71,40,26],
    satScore: '4.7', satCount: '218 reseñas',
    satRows: [{stars:'⭐⭐⭐⭐⭐',pct:68},{stars:'⭐⭐⭐⭐',pct:22},{stars:'⭐⭐⭐',pct:7},{stars:'⭐⭐',pct:2},{stars:'⭐',pct:1}],
    topTitle:'Top platos', topSub:'Por unidades vendidas',
    tops:[{n:'Risotto de mariscos',v:'89 unid.',d:'+14%'},{n:'Lomo a la brasa',v:'67 unid.',d:'+8%'},{n:'Tiramisú casero',v:'52 unid.',d:'+21%'},{n:'Pasta al pesto',v:'44 unid.',d:'-3%'}],
    chart1Title:'Ingresos diarios (miles $)', chart1Sub:'Esta semana vs semana anterior',
    insight:'El viernes fue el día de mayor ingreso con $320.000, un 14% por encima del viernes anterior. El risotto de mariscos lidera ventas con 89 unidades. Se recomienda reforzar el stock de mariscos para el próximo fin de semana y evaluar una promoción de lunes a miércoles para equilibrar la ocupación semanal.',
    repKpis:[
      {val:'$1.284.000',label:'Ingresos totales',delta:'↑ 12% vs sem. anterior',dir:'up'},
      {val:'312',label:'Clientes atendidos',delta:'↑ 8% vs sem. anterior',dir:'up'},
      {val:'4.7/5',label:'Satisfacción',delta:'↑ 0.2 vs sem. anterior',dir:'up'},
    ],
    highlights:[
      {color:'#16C784',text:'<strong>Viernes récord:</strong> $320.000 en ingresos, el mejor día de las últimas 4 semanas.'},
      {color:'#3B6FFF',text:'<strong>Risotto de mariscos</strong> lidera ventas con 89 unidades (+14% vs semana pasada).'},
      {color:'#F59E0B',text:'Las <strong>reservas canceladas bajaron un 5%</strong> gracias al sistema de recordatorio automático.'},
      {color:'#EA3943',text:'El <strong>martes tuvo la ocupación más baja</strong> (30 clientes). Oportunidad para promoción.'},
    ],
    repInsight:'Esta semana muestra una tendencia positiva: los ingresos crecieron un 12% y la satisfacción alcanzó 4.7/5. El patrón de demanda concentrado en jueves-viernes sugiere una oportunidad de promoción para los días de menor afluencia. Recomendamos un "Menú Express" de lunes a miércoles para equilibrar la carga operacional y aumentar ingresos en días bajos.'
  },
  clinica: {
    nombre: 'Clínica',
    kpis: [
      { label:'Ingresos semana', value:'$2.840.000', delta:'+9%', dir:'up', sub:'vs semana anterior', color:'blue' },
      { label:'Pacientes atendidos', value:'87', delta:'+6%', dir:'up', sub:'consultas esta semana', color:'green' },
      { label:'Valor promedio cita', value:'$32.645', delta:'+2%', dir:'up', sub:'por consulta', color:'amber' },
      { label:'Inasistencias', value:'7', delta:'-38%', dir:'up', sub:'vs semana anterior', color:'red' },
    ],
    ingresos: [480,520,390,650,480,320,0],
    ingresosPrev: [420,470,380,590,430,300,0],
    clientes: [16,19,14,22,10,6,0],
    satScore: '4.9', satCount: '341 reseñas',
    satRows: [{stars:'⭐⭐⭐⭐⭐',pct:81},{stars:'⭐⭐⭐⭐',pct:14},{stars:'⭐⭐⭐',pct:4},{stars:'⭐⭐',pct:1},{stars:'⭐',pct:0}],
    topTitle:'Top tratamientos', topSub:'Por cantidad de consultas',
    tops:[{n:'Ortodoncia invisible',v:'23 citas',d:'+18%'},{n:'Blanqueamiento LED',v:'19 citas',d:'+31%'},{n:'Limpieza dental',v:'28 citas',d:'+4%'},{n:'Radiografía digital',v:'17 citas',d:'+2%'}],
    chart1Title:'Ingresos diarios (miles $)', chart1Sub:'Esta semana vs semana anterior',
    insight:'Las inasistencias cayeron un 38% respecto a la semana anterior gracias al sistema de recordatorios automáticos — esto equivale a recuperar aproximadamente $293.000 en consultas que antes se perdían. El blanqueamiento LED creció un 31%, impulsado por las consultas del mes de marzo. Se recomienda destacar este servicio en las redes sociales esta semana.',
    repKpis:[
      {val:'$2.840.000',label:'Ingresos totales',delta:'↑ 9% vs sem. anterior',dir:'up'},
      {val:'87',label:'Pacientes atendidos',delta:'↑ 6% vs sem. anterior',dir:'up'},
      {val:'4.9/5',label:'Satisfacción',delta:'↑ 0.1 vs sem. anterior',dir:'up'},
    ],
    highlights:[
      {color:'#16C784',text:'Las <strong>inasistencias bajaron un 38%</strong> gracias al recordatorio automático de citas.'},
      {color:'#3B6FFF',text:'El <strong>blanqueamiento LED creció un 31%</strong> — el servicio de mayor crecimiento esta semana.'},
      {color:'#F59E0B',text:'<strong>Jueves fue el día de mayor ingreso</strong> con $650.000, coincidiendo con la agenda completa del Dr. Ramírez.'},
      {color:'#EA3943',text:'El <strong>sábado tuvo baja ocupación</strong> (6 pacientes). Evaluar abrir agenda con descuento.'},
    ],
    repInsight:'El impacto más significativo esta semana fue la reducción de inasistencias en un 38%, directamente atribuible al sistema de recordatorios ValVic. Esto equivale a ~$293.000 recuperados en citas que antes se perdían. El crecimiento del blanqueamiento LED (31%) sugiere alta demanda estética de temporada: recomendamos un paquete combinado blanqueamiento + ortodoncia para aprovechar el momentum.'
  },
  spa: {
    nombre: 'Spa',
    kpis: [
      { label:'Ingresos semana', value:'$980.000', delta:'+15%', dir:'up', sub:'vs semana anterior', color:'blue' },
      { label:'Clientes atendidos', value:'64', delta:'+11%', dir:'up', sub:'sesiones esta semana', color:'green' },
      { label:'Valor promedio sesión', value:'$15.312', delta:'+4%', dir:'up', sub:'por visita', color:'amber' },
      { label:'Cancelaciones', value:'5', delta:'-29%', dir:'up', sub:'vs semana anterior', color:'red' },
    ],
    ingresos: [120,150,90,200,220,140,60],
    ingresosPrev: [100,130,85,170,195,120,55],
    clientes: [9,11,7,15,14,5,3],
    satScore: '4.8', satCount: '129 reseñas',
    satRows: [{stars:'⭐⭐⭐⭐⭐',pct:74},{stars:'⭐⭐⭐⭐',pct:18},{stars:'⭐⭐⭐',pct:6},{stars:'⭐⭐',pct:2},{stars:'⭐',pct:0}],
    topTitle:'Top tratamientos', topSub:'Por sesiones realizadas',
    tops:[{n:'Masaje relajante 60min',v:'28 sesiones',d:'+20%'},{n:'Facial hidratante',v:'18 sesiones',d:'+12%'},{n:'Piedras calientes',v:'11 sesiones',d:'+8%'},{n:'Aromaterapia',v:'7 sesiones',d:'+3%'}],
    chart1Title:'Ingresos diarios (miles $)', chart1Sub:'Esta semana vs semana anterior',
    insight:'Semana excepcional para el spa con ingresos creciendo un 15%. El masaje relajante de 60 min sigue siendo el servicio estrella con 28 sesiones. El viernes y jueves concentran el 43% de los ingresos semanales, lo que sugiere alta demanda de "escape de semana laboral". Se recomienda crear un paquete "Pausa de Jueves" para atraer clientas los días de menor ocupación.',
    repKpis:[
      {val:'$980.000',label:'Ingresos totales',delta:'↑ 15% vs sem. anterior',dir:'up'},
      {val:'64',label:'Sesiones realizadas',delta:'↑ 11% vs sem. anterior',dir:'up'},
      {val:'4.8/5',label:'Satisfacción',delta:'= igual sem. anterior',dir:'up'},
    ],
    highlights:[
      {color:'#16C784',text:'<strong>Mejor semana del mes</strong> con $980.000 en ingresos, un 15% por encima de la semana anterior.'},
      {color:'#3B6FFF',text:'El <strong>masaje relajante lidera</strong> con 28 sesiones — 20% más que la semana pasada.'},
      {color:'#F59E0B',text:'Las <strong>cancelaciones bajaron un 29%</strong> gracias al recordatorio automático de citas.'},
      {color:'#EA3943',text:'El <strong>miércoles tiene la menor ocupación</strong>. Oportunidad para paquete "Miércoles de bienestar".'},
    ],
    repInsight:'El crecimiento de 15% esta semana refleja la efectividad del sistema de recordatorios y la gestión de cancelaciones. La concentración de demanda jueves-viernes es una señal clara: los clientes buscan "descompresión de semana laboral". Recomendamos crear un paquete mid-week con descuento del 15% para equilibrar la ocupación y aumentar ingresos en días bajos.'
  },
  tienda: {
    nombre: 'Tienda',
    kpis: [
      { label:'Ventas semana', value:'$3.120.000', delta:'+22%', dir:'up', sub:'vs semana anterior', color:'blue' },
      { label:'Pedidos procesados', value:'148', delta:'+18%', dir:'up', sub:'órdenes esta semana', color:'green' },
      { label:'Valor promedio pedido', value:'$21.081', delta:'+3%', dir:'up', sub:'por orden', color:'amber' },
      { label:'Carritos abandonados', value:'34', delta:'-12%', dir:'up', sub:'vs semana anterior', color:'red' },
    ],
    ingresos: [380,490,310,680,720,390,150],
    ingresosPrev: [310,400,280,560,590,330,120],
    clientes: [21,28,18,38,30,8,5],
    satScore: '4.6', satCount: '892 reseñas',
    satRows: [{stars:'⭐⭐⭐⭐⭐',pct:62},{stars:'⭐⭐⭐⭐',pct:25},{stars:'⭐⭐⭐',pct:9},{stars:'⭐⭐',pct:3},{stars:'⭐',pct:1}],
    topTitle:'Top productos', topSub:'Por unidades vendidas',
    tops:[{n:'Polera oversize negra',v:'42 unid.',d:'+34%'},{n:'Jeans slim fit azul',v:'31 unid.',d:'+12%'},{n:'Zapatilla casual blanca',v:'28 unid.',d:'+8%'},{n:'Parka impermeable',v:'19 unid.',d:'+41%'}],
    chart1Title:'Ventas diarias (miles $)', chart1Sub:'Esta semana vs semana anterior',
    insight:'Semana excepcional con ventas creciendo un 22%. El viernes y jueves concentran el 45% de las ventas semanales. La parka impermeable creció un 41%, posiblemente por el cambio de temporada — se recomienda destacarla en el home de la tienda y en redes sociales esta semana. Los carritos abandonados bajaron un 12%, posiblemente por el email de recuperación automático.',
    repKpis:[
      {val:'$3.120.000',label:'Ventas totales',delta:'↑ 22% vs sem. anterior',dir:'up'},
      {val:'148',label:'Pedidos procesados',delta:'↑ 18% vs sem. anterior',dir:'up'},
      {val:'4.6/5',label:'Satisfacción',delta:'↑ 0.1 vs sem. anterior',dir:'up'},
    ],
    highlights:[
      {color:'#16C784',text:'<strong>Ventas récord de la semana:</strong> $3.120.000, un 22% más que la semana anterior.'},
      {color:'#3B6FFF',text:'La <strong>parka impermeable creció un 41%</strong> — probable impulso por cambio de temporada.'},
      {color:'#F59E0B',text:'Los <strong>carritos abandonados bajaron un 12%</strong> gracias al email de recuperación automático.'},
      {color:'#EA3943',text:'El <strong>domingo tuvo las ventas más bajas</strong> de la semana — evaluar campaña de email ese día.'},
    ],
    repInsight:'El crecimiento del 22% esta semana es el mayor en el último mes. La recuperación de carritos abandonados está funcionando: se recuperaron aproximadamente $340.000 en ventas que antes se perdían. El auge de la parka impermeable sugiere que los clientes están comprando pensando en otoño — recomendamos adelantar la campaña de temporada esta semana para capturar esa intención de compra.'
  },
  gym: {
    nombre: 'Gimnasio',
    kpis: [
      { label:'Ingresos semana', value:'$1.650.000', delta:'+7%', dir:'up', sub:'mensualidades + clases', color:'blue' },
      { label:'Asistencias', value:'521', delta:'+11%', dir:'up', sub:'visitas esta semana', color:'green' },
      { label:'Nuevos socios', value:'18', delta:'+50%', dir:'up', sub:'vs semana anterior', color:'amber' },
      { label:'Bajas de socios', value:'4', delta:'-20%', dir:'up', sub:'vs semana anterior', color:'red' },
    ],
    ingresos: [210,280,180,310,290,220,160],
    ingresosPrev: [195,260,170,290,270,200,155],
    clientes: [68,82,55,94,88,72,62],
    satScore: '4.5', satCount: '204 reseñas',
    satRows: [{stars:'⭐⭐⭐⭐⭐',pct:58},{stars:'⭐⭐⭐⭐',pct:28},{stars:'⭐⭐⭐',pct:10},{stars:'⭐⭐',pct:3},{stars:'⭐',pct:1}],
    topTitle:'Top clases', topSub:'Por asistentes esta semana',
    tops:[{n:'Spinning mañana',v:'94 asist.',d:'+22%'},{n:'CrossFit 18:00',v:'78 asist.',d:'+15%'},{n:'Yoga restaurativo',v:'61 asist.',d:'+8%'},{n:'HIIT express',v:'54 asist.',d:'+31%'}],
    chart1Title:'Ingresos diarios (miles $)', chart1Sub:'Esta semana vs semana anterior',
    insight:'18 nuevos socios esta semana representa un crecimiento del 50% respecto a la semana anterior. El HIIT express creció un 31%, señal de alta demanda por clases cortas e intensas. El jueves es el día de mayor asistencia (94 personas). Se recomienda agregar una clase adicional los jueves para aliviar la congestión y capturar demanda insatisfecha.',
    repKpis:[
      {val:'$1.650.000',label:'Ingresos totales',delta:'↑ 7% vs sem. anterior',dir:'up'},
      {val:'521',label:'Asistencias',delta:'↑ 11% vs sem. anterior',dir:'up'},
      {val:'4.5/5',label:'Satisfacción',delta:'= igual sem. anterior',dir:'up'},
    ],
    highlights:[
      {color:'#16C784',text:'<strong>18 nuevos socios esta semana</strong>, un 50% más que la semana anterior.'},
      {color:'#3B6FFF',text:'El <strong>HIIT express creció un 31%</strong> en asistencia — demanda creciente por clases cortas.'},
      {color:'#F59E0B',text:'<strong>Solo 4 bajas de socios</strong> esta semana, la cifra más baja del mes.'},
      {color:'#EA3943',text:'El <strong>miércoles tiene la menor asistencia</strong>. Oportunidad para clase especial o promoción.'},
    ],
    repInsight:'El dato más relevante esta semana es la captación de 18 nuevos socios (+50%), muy por encima del promedio mensual. Esto coincide con la campaña de bienvenida automática que se activó el lunes pasado. La baja de socios (4 personas) es la más baja del mes, lo que sugiere que el programa de retención por WhatsApp está siendo efectivo. Recomendamos replicar la campaña de captación la próxima semana.'
  }
};

const dias = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'];
let bizActual = 'restaurante';
let chartLinea, chartBar, chartRep;
let viewActual = 'dashboard';

function setBiz(biz, btn){
  bizActual = biz;
  document.querySelectorAll('.biz-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  render();
}

function setView(v){
  viewActual = v;
  document.getElementById('panel-dashboard').classList.toggle('active', v==='dashboard');
  document.getElementById('panel-report').classList.toggle('active', v==='report');
  document.getElementById('btn-dashboard').classList.toggle('active', v==='dashboard');
  document.getElementById('btn-report').classList.toggle('active', v==='report');
  if(v==='report') renderReport();
}

function render(){
  renderDashboard();
  if(viewActual==='report') renderReport();
}

function renderDashboard(){
  const d = datos[bizActual];

  // KPIs
  document.getElementById('kpis').innerHTML = d.kpis.map(k=>`
    <div class="kpi ${k.color}">
      <div class="kpi-label">${k.label}</div>
      <div class="kpi-value">${k.value}</div>
      <span class="kpi-delta ${k.dir}">${k.dir==='up'?'↑':'↓'} ${k.delta}</span>
      <div class="kpi-sub">${k.sub}</div>
    </div>`).join('');

  // Chart titles
  document.getElementById('chart1-title').textContent = d.chart1Title;
  document.getElementById('chart1-sub').textContent = d.chart1Sub;
  document.getElementById('chart2-title').textContent = `Clientes atendidos`;
  document.getElementById('top-title').textContent = d.topTitle;
  document.getElementById('top-sub').textContent = d.topSub;

  // Satisfaction
  document.getElementById('sat-score').textContent = d.satScore;
  document.getElementById('sat-count').textContent = d.satCount;
  document.getElementById('sat-list').innerHTML = d.satRows.map(r=>`
    <div class="sat-row">
      <div class="sat-stars">${r.stars}</div>
      <div class="sat-bar-wrap"><div class="sat-bar" style="width:${r.pct}%"></div></div>
      <div class="sat-pct">${r.pct}%</div>
    </div>`).join('');

  // Top list
  document.getElementById('top-list').innerHTML = d.tops.map((t,i)=>`
    <div class="top-item">
      <div class="top-rank">${i+1}</div>
      <div class="top-name">${t.n}</div>
      <div class="top-val">${t.v}</div>
      <div class="top-delta">${t.d}</div>
    </div>`).join('');

  // Insight
  document.getElementById('insight-text').textContent = d.insight;

  // Chart linea
  const ctxL = document.getElementById('chart-linea').getContext('2d');
  if(chartLinea) chartLinea.destroy();
  chartLinea = new Chart(ctxL,{
    type:'line',
    data:{
      labels: dias,
      datasets:[
        {label:'Esta semana',data:d.ingresos,borderColor:'#3B6FFF',backgroundColor:'rgba(59,111,255,0.08)',tension:0.4,pointRadius:3,pointBackgroundColor:'#3B6FFF',fill:true},
        {label:'Semana anterior',data:d.ingresosPrev,borderColor:'#E8E5DF',backgroundColor:'transparent',tension:0.4,pointRadius:0,borderDash:[4,4]}
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,position:'top',labels:{font:{size:11,family:'DM Sans'},color:'#A09EA5',boxWidth:12,padding:12}}},scales:{x:{grid:{display:false},ticks:{font:{size:11,family:'DM Sans'},color:'#A09EA5'}},y:{grid:{color:'#F4F2EE'},ticks:{font:{size:11,family:'DM Sans'},color:'#A09EA5'},beginAtZero:false}}}
  });

  // Chart bar
  const ctxB = document.getElementById('chart-bar').getContext('2d');
  if(chartBar) chartBar.destroy();
  chartBar = new Chart(ctxB,{
    type:'bar',
    data:{
      labels: dias,
      datasets:[{data:d.clientes,backgroundColor:d.clientes.map(v=>v===Math.max(...d.clientes)?'#3B6FFF':'#E8E5DF'),borderRadius:6,borderSkipped:false}]
    },
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{font:{size:11,family:'DM Sans'},color:'#A09EA5'}},y:{grid:{color:'#F4F2EE'},ticks:{font:{size:11,family:'DM Sans'},color:'#A09EA5'},beginAtZero:true}}}
  });
}

function renderReport(){
  const d = datos[bizActual];
  document.getElementById('rep-title').textContent = `Reporte Semanal — ${d.nombre}`;
  document.getElementById('rep-date').textContent = new Date().toLocaleDateString('es-CL',{day:'numeric',month:'long',year:'numeric'});
  document.getElementById('rep-kpis').innerHTML = d.repKpis.map(k=>`
    <div class="rep-kpi">
      <div class="rep-kpi-val">${k.val}</div>
      <div class="rep-kpi-label">${k.label}</div>
      <div class="rep-kpi-delta ${k.dir}">${k.delta}</div>
    </div>`).join('');
  document.getElementById('highlights').innerHTML = d.highlights.map(h=>`
    <div class="highlight">
      <div class="hl-dot" style="background:${h.color}"></div>
      <div class="hl-text">${h.text}</div>
    </div>`).join('');
  document.getElementById('rep-insight').textContent = d.repInsight;

  const ctxR = document.getElementById('rep-chart').getContext('2d');
  if(chartRep) chartRep.destroy();
  chartRep = new Chart(ctxR,{
    type:'line',
    data:{
      labels: dias,
      datasets:[
        {label:'Esta semana',data:d.ingresos,borderColor:'#3B6FFF',backgroundColor:'rgba(59,111,255,0.08)',tension:0.4,pointRadius:3,fill:true},
        {label:'Sem. anterior',data:d.ingresosPrev,borderColor:'#E8E5DF',tension:0.4,pointRadius:0,borderDash:[4,4]}
      ]
    },
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'top',labels:{font:{size:10,family:'DM Sans'},color:'#A09EA5',boxWidth:10}}},scales:{x:{grid:{display:false},ticks:{font:{size:10,family:'DM Sans'},color:'#A09EA5'}},y:{grid:{color:'#F4F2EE'},ticks:{font:{size:10,family:'DM Sans'},color:'#A09EA5'},beginAtZero:false}}}
  });
}

render();

// ── Event listeners ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Business selector buttons
  document.querySelectorAll('.biz-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.biz-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      setBiz(btn.dataset.biz);
    });
  });

  // Period select
  const periodSelect = document.getElementById('period-select');
  if (periodSelect) periodSelect.addEventListener('change', render);

  // View toggle buttons
  document.querySelectorAll('.view-btn').forEach(btn => {
    btn.addEventListener('click', () => setView(btn.dataset.view));
  });

  // Download PDF button
  const dlBtn = document.getElementById('download-btn');
  if (dlBtn) dlBtn.addEventListener('click', () =>
    alert('En la versión real, el reporte se descarga como PDF o se envía automáticamente por email.')
  );
});
