const API_BASE="http://localhost:8000/api";
let adminUsuario="",adminPassword="",todosEstudiantes=[];

async function login(){
  const usuario=document.getElementById("inputUsuario").value.trim();
  const password=document.getElementById("inputPassword").value.trim();
  if(!usuario||!password){mostrarAlerta("alertaLogin","error","Completa todos los campos.");return;}
  try{
    const res=await fetch(`${API_BASE}/convocatorias/admin/login`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({usuario,password})});
    const data=await res.json();
    if(!res.ok)throw new Error(data.detail||"Credenciales incorrectas.");
    adminUsuario=usuario;adminPassword=password;
    document.getElementById("panelLogin").classList.add("hidden");
    document.getElementById("panelAdmin").classList.remove("hidden");
    cargarEstado();cargarConvocatorias();cargarEstudiantes();cargarEstadisticas();
  }catch(e){mostrarAlerta("alertaLogin","error",e.message);}
}

function cambiarTab(tab){
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  const tabs=document.querySelectorAll(".tab");
  if(tab==="convocatorias"){
    tabs[0].classList.add("active");
    document.getElementById("tabConvocatorias").style.display="block";
    document.getElementById("tabEstudiantes").style.display="none";
  }else{
    tabs[1].classList.add("active");
    document.getElementById("tabConvocatorias").style.display="none";
    document.getElementById("tabEstudiantes").style.display="block";
    cargarEstudiantes();
  }
}

async function cargarEstadisticas(){
  try{
    const res=await fetch(`${API_BASE}/admin/resumen`);
    const data=await res.json();
    const r=data.resumen_por_estado||[];
    let total=0,env=0,rech=0,pend=0;
    r.forEach(x=>{total+=x.total;if(x.estado==="ENVIADO"||x.estado==="APROBADO")env+=x.total;if(x.estado==="RECHAZADO")rech+=x.total;if(x.estado==="PENDIENTE"||x.estado==="ERROR_VALIDACION")pend+=x.total;});
    document.getElementById("statTotal").textContent=total;
    document.getElementById("statEnviadas").textContent=env;
    document.getElementById("statRechazadas").textContent=rech;
    document.getElementById("statPendientes").textContent=pend;
  }catch(e){}
}

async function cargarEstado(){
  try{
    const res=await fetch(`${API_BASE}/convocatorias/estado`);
    const data=await res.json();
    const b=document.getElementById("estadoBanner");
    if(data.convocatoria_abierta){
      b.className="estado-banner banner-abierta";
      document.getElementById("bannerIcon").textContent="🟢";
      document.getElementById("bannerTitulo").textContent="Convocatoria ABIERTA";
      const c=data.convocatoria_activa;
      document.getElementById("bannerDesc").textContent=`${c.nombre} — Cierra el ${formatFecha(c.fecha_fin)}`;
    }else{
      b.className="estado-banner banner-cerrada";
      document.getElementById("bannerIcon").textContent="🔴";
      document.getElementById("bannerTitulo").textContent="Convocatoria CERRADA";
      document.getElementById("bannerDesc").textContent=data.proxima_convocatoria?`Próxima: ${data.proxima_convocatoria.nombre} — Abre el ${formatFecha(data.proxima_convocatoria.fecha_inicio)}`:"No hay próxima convocatoria programada.";
    }
  }catch(e){}
}

async function cargarConvocatorias(){
  document.getElementById("cargandoLista").classList.remove("hidden");
  document.getElementById("tablaConvocatorias").classList.add("hidden");
  document.getElementById("sinConvocatorias").classList.add("hidden");
  try{
    const res=await fetch(`${API_BASE}/convocatorias/admin/listar?usuario=${adminUsuario}&password=${adminPassword}`);
    const data=await res.json();
    if(!res.ok)throw new Error(data.detail);
    document.getElementById("cargandoLista").classList.add("hidden");
    if(data.length===0){document.getElementById("sinConvocatorias").classList.remove("hidden");return;}
    const tbody=document.getElementById("cuerpoTablaConv");
    tbody.innerHTML="";
    const hoy=new Date().toISOString().split("T")[0];
    data.forEach(c=>{
      const badge=c.activa?'<span class="badge badge-activa">ACTIVA</span>':c.fecha_inicio>hoy?'<span class="badge badge-futura">FUTURA</span>':'<span class="badge badge-cerrada">CERRADA</span>';
      const tr=document.createElement("tr");
      tr.innerHTML=`<td><strong>${c.nombre}</strong></td><td>${formatFecha(c.fecha_inicio)}</td><td>${formatFecha(c.fecha_fin)}</td><td>${badge}</td>
        <td><div class="acciones">
          ${!c.activa?`<button class="btn btn-success btn-sm" onclick="activar(${c.id})">✅ Activar</button>`:`<button class="btn btn-danger btn-sm" onclick="desactivar(${c.id})">🔴 Desactivar</button>`}
          <button class="btn btn-outline btn-sm" onclick="eliminar(${c.id},'${c.nombre}')">🗑 Eliminar</button>
        </div></td>`;
      tbody.appendChild(tr);
    });
    document.getElementById("tablaConvocatorias").classList.remove("hidden");
  }catch(e){document.getElementById("cargandoLista").classList.add("hidden");mostrarAlerta("alertaLista","error","Error: "+e.message);}
}

async function crearConvocatoria(){
  limpiarAlerta("alertaCrear");
  const nombre=document.getElementById("inputNombre").value.trim();
  const inicio=document.getElementById("inputInicio").value;
  const fin=document.getElementById("inputFin").value;
  if(!nombre||!inicio||!fin){mostrarAlerta("alertaCrear","error","Completa todos los campos.");return;}
  if(fin<=inicio){mostrarAlerta("alertaCrear","error","La fecha de cierre debe ser posterior.");return;}
  try{
    const res=await fetch(`${API_BASE}/convocatorias/admin/crear?usuario=${adminUsuario}&password=${adminPassword}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({nombre,fecha_inicio:inicio,fecha_fin:fin})});
    const data=await res.json();if(!res.ok)throw new Error(data.detail);
    mostrarAlerta("alertaCrear","exito","Convocatoria creada exitosamente.");
    document.getElementById("inputNombre").value="";document.getElementById("inputInicio").value="";document.getElementById("inputFin").value="";
    cargarConvocatorias();cargarEstado();
  }catch(e){mostrarAlerta("alertaCrear","error",e.message);}
}
async function activar(id){try{const res=await fetch(`${API_BASE}/convocatorias/admin/activar/${id}?usuario=${adminUsuario}&password=${adminPassword}`,{method:"PUT"});const data=await res.json();if(!res.ok)throw new Error(data.detail);mostrarAlerta("alertaLista","exito",data.mensaje);cargarConvocatorias();cargarEstado();}catch(e){mostrarAlerta("alertaLista","error",e.message);}}
async function desactivar(id){try{const res=await fetch(`${API_BASE}/convocatorias/admin/desactivar/${id}?usuario=${adminUsuario}&password=${adminPassword}`,{method:"PUT"});const data=await res.json();if(!res.ok)throw new Error(data.detail);mostrarAlerta("alertaLista","exito",data.mensaje);cargarConvocatorias();cargarEstado();}catch(e){mostrarAlerta("alertaLista","error",e.message);}}
async function eliminar(id,nombre){if(!confirm(`¿Eliminar "${nombre}"?`))return;try{const res=await fetch(`${API_BASE}/convocatorias/admin/eliminar/${id}?usuario=${adminUsuario}&password=${adminPassword}`,{method:"DELETE"});const data=await res.json();if(!res.ok)throw new Error(data.detail);mostrarAlerta("alertaLista","exito",data.mensaje);cargarConvocatorias();cargarEstado();}catch(e){mostrarAlerta("alertaLista","error",e.message);}}

async function cargarEstudiantes(){
  document.getElementById("cargandoEstudiantes").classList.remove("hidden");
  document.getElementById("tablaEstudiantes").classList.add("hidden");
  document.getElementById("sinEstudiantes").classList.add("hidden");
  try{
    const res=await fetch(`${API_BASE}/convocatorias/admin/estudiantes?usuario=${adminUsuario}&password=${adminPassword}`);
    const data=await res.json();if(!res.ok)throw new Error(data.detail);
    todosEstudiantes=data;
    document.getElementById("cargandoEstudiantes").classList.add("hidden");
    renderizarEstudiantes(data);
  }catch(e){document.getElementById("cargandoEstudiantes").classList.add("hidden");mostrarAlerta("alertaEstudiantes","error","Error: "+e.message);}
}

function filtrarEstudiantes(){
  const q=document.getElementById("buscarEstudiante").value.toLowerCase();
  renderizarEstudiantes(todosEstudiantes.filter(e=>(e.correo_institucional||"").toLowerCase().includes(q)||(e.cedula||"").includes(q)));
}

function renderizarEstudiantes(data){
  if(data.length===0){document.getElementById("sinEstudiantes").classList.remove("hidden");document.getElementById("tablaEstudiantes").classList.add("hidden");return;}
  const badges={"ENVIADO":'<span class="badge badge-enviado">ENVIADO</span>',"APROBADO":'<span class="badge badge-enviado">APROBADO</span>',"PENDIENTE":'<span class="badge badge-pendiente">PENDIENTE</span>',"ERROR_VALIDACION":'<span class="badge badge-error">ERROR</span>',"RECHAZADO":'<span class="badge badge-rechazado">RECHAZADO</span>',"VALIDANDO":'<span class="badge badge-validando">VALIDANDO</span>'};
  const tbody=document.getElementById("cuerpoTablaEst");
  tbody.innerHTML="";
  data.forEach(e=>{
    const estado=e.estado||"SIN SOLICITUD";
    const badge=badges[estado]||`<span class="badge badge-pendiente">${estado}</span>`;
    const intentos=e.intentos??0;
    const intentosBadge=intentos>=2?`<span style="color:var(--error);font-weight:900;">${intentos}/2 ⚠️</span>`:`${intentos}/2`;
    const fecha=e.creado_en?new Date(e.creado_en).toLocaleDateString("es-CO"):"-";
    const tr=document.createElement("tr");
    tr.innerHTML=`
      <td>${e.correo_institucional||"-"}</td>
      <td>${e.cedula||"-"}</td>
      <td>${e.tipo_auxilio||"<span style='color:var(--gris)'>Sin solicitud</span>"}</td>
      <td>${badge}</td><td>${intentosBadge}</td><td>${fecha}</td>
      <td><div class="acciones">
        ${e.solicitud_id&&(e.estado==="ERROR_VALIDACION"||e.estado==="RECHAZADO"||e.intentos>=2)
          ?`<button class="btn btn-warning btn-sm" onclick="reiniciarIntentos('${e.solicitud_id}','${e.correo_institucional}')">🔄 Reiniciar</button>`
          :e.solicitud_id?'<span style="color:var(--gris);font-size:12px;">Sin acciones</span>'
          :'<span style="color:var(--gris);font-size:12px;">Sin solicitud</span>'}
      </div></td>`;
    tbody.appendChild(tr);
  });
  document.getElementById("tablaEstudiantes").classList.remove("hidden");
  document.getElementById("sinEstudiantes").classList.add("hidden");
}

async function reiniciarIntentos(id,correo){
  if(!confirm(`¿Reiniciar los intentos de ${correo}?`))return;
  try{
    const res=await fetch(`${API_BASE}/convocatorias/admin/reiniciar-intentos/${id}?usuario=${adminUsuario}&password=${adminPassword}`,{method:"PUT"});
    const data=await res.json();if(!res.ok)throw new Error(data.detail);
    mostrarAlerta("alertaEstudiantes","exito",`✅ ${data.mensaje}`);
    cargarEstudiantes();cargarEstadisticas();
  }catch(e){mostrarAlerta("alertaEstudiantes","error",e.message);}
}

function cerrarSesion(){adminUsuario="";adminPassword="";document.getElementById("panelAdmin").classList.add("hidden");document.getElementById("panelLogin").classList.remove("hidden");document.getElementById("inputUsuario").value="";document.getElementById("inputPassword").value="";limpiarAlerta("alertaLogin");}
function formatFecha(f){if(!f)return"-";const[y,m,d]=f.split("-");const ms=["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];return`${d} ${ms[parseInt(m)-1]} ${y}`;}
function mostrarAlerta(id,tipo,msg){const ic={error:"❌",exito:"✅",info:"ℹ️"};document.getElementById(id).innerHTML=`<div class="alerta alerta-${tipo}"><span>${ic[tipo]}</span><div>${msg}</div></div>`;}
function limpiarAlerta(id){document.getElementById(id).innerHTML="";}
document.addEventListener("keydown",e=>{if(e.key==="Enter"&&!document.getElementById("panelLogin").classList.contains("hidden"))login();});