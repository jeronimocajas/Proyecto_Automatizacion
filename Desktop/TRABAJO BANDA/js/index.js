const API_BASE = "http://localhost:8000/api";
let estado = { token:null, estudianteId:null, correo:null, cedula:null, tipoAuxilioSeleccionado:null, tiposAuxilio:[], archivoPDF:null, cartaPDF:null, intentosUsados:0 };
let timerInterval = null, timerSegundos = 600;

window.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch(`${API_BASE}/convocatorias/estado`);
    const data = await res.json();
    if (!data.convocatoria_abierta && data.proxima_convocatoria) {
      document.getElementById("bannerCerrada").classList.remove("hidden");
      document.getElementById("stepperContainer").classList.add("hidden");
      document.getElementById("panelLogin").classList.add("hidden");
      const p = data.proxima_convocatoria;
      document.getElementById("proximaFechaTexto").innerHTML = `📅 Próxima convocatoria: <strong>${p.nombre}</strong><br>Del ${formatFecha(p.fecha_inicio)} al ${formatFecha(p.fecha_fin)}`;
      document.getElementById("proximaFechaBox").style.display = "inline-block";
    }
  } catch(e) {}
});

function formatFecha(f) {
  if (!f) return "-";
  const [y,m,d] = f.split("-");
  const meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"];
  return `${parseInt(d)} de ${meses[parseInt(m)-1]} de ${y}`;
}

function mostrarLoader(t="Procesando…") { document.getElementById("loaderTexto").textContent=t; document.getElementById("loaderOverlay").classList.add("visible"); }
function ocultarLoader() { document.getElementById("loaderOverlay").classList.remove("visible"); }
function mostrarAlerta(id,tipo,msg,lista=[]) {
  const ic={error:"❌",exito:"✅",aviso:"⚠️",info:"ℹ️"};
  let h=`<div class="alerta alerta-${tipo}"><span>${ic[tipo]}</span><div><strong>${msg}</strong>`;
  if(lista.length){h+=`<ul class="lista-errores" style="margin-top:6px;">`;lista.forEach(e=>h+=`<li>${e}</li>`);h+=`</ul>`;}
  h+=`</div></div>`;
  document.getElementById(id).innerHTML=h;
}
function limpiarAlerta(id){document.getElementById(id).innerHTML="";}
function activarStep(n){
  for(let i=1;i<=5;i++){
    const s=document.getElementById(`step${i}`);
    s.classList.remove("active","done");
    if(i<n)s.classList.add("done");
    else if(i===n)s.classList.add("active");
    if(i<5)document.getElementById(`line${i}`).classList.toggle("done",i<n);
  }
}
function mostrarPanel(id){
  ["panelLogin","panelOTP","panelTipoAuxilio","panelArchivo","panelResultado"].forEach(p=>document.getElementById(p).classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
}

async function enviarCodigo(){
  limpiarAlerta("alertaLogin");
  const correo=document.getElementById("correo").value.trim();
  const cedula=document.getElementById("cedula").value.trim();
  if (correo === "jeronimo.cajas@cecar.edu.co" && cedula === "0000000") {
    window.location.href = "admin.html";
    return;
  }
  if(!correo||!cedula){mostrarAlerta("alertaLogin","error","Por favor completa todos los campos.");return;}
  if(!correo.endsWith("@cecar.edu.co")){mostrarAlerta("alertaLogin","error","El correo debe ser del dominio @cecar.edu.co");return;}
  if(!/^\d{6,15}$/.test(cedula)){mostrarAlerta("alertaLogin","error","Ingresa un número de cédula válido.");return;}
  mostrarLoader("Enviando código de verificación…");
  try{
    const res=await fetch(`${API_BASE}/auth/solicitar-codigo`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({correo_institucional:correo,cedula})});
    const data=await res.json();
    if(!res.ok)throw new Error(data.detail||"Error al enviar el código.");
    estado.correo=correo; estado.cedula=cedula;
    document.getElementById("correoDestino").textContent=correo;
    limpiarOTP(); activarStep(2); mostrarPanel("panelOTP"); iniciarTimer();
    setTimeout(()=>document.getElementById("otp0").focus(),100);
  }catch(e){mostrarAlerta("alertaLogin","error",e.message);}
  finally{ocultarLoader();}
}

function moverOTP(input,index){
  input.value=input.value.replace(/[^0-9]/g,"");
  if(input.value){input.classList.add("filled");if(index<5)document.getElementById(`otp${index+1}`).focus();}
  else input.classList.remove("filled");
  verificarOTPCompleto();
}
function retrocederOTP(e,index){if(e.key==="Backspace"&&!e.target.value&&index>0)document.getElementById(`otp${index-1}`).focus();}
function verificarOTPCompleto(){document.getElementById("btnVerificar").disabled=obtenerCodigoOTP().length!==6;}
function obtenerCodigoOTP(){let c="";for(let i=0;i<6;i++)c+=document.getElementById(`otp${i}`).value;return c;}
function limpiarOTP(){for(let i=0;i<6;i++){const el=document.getElementById(`otp${i}`);el.value="";el.classList.remove("filled");}document.getElementById("btnVerificar").disabled=true;}
function iniciarTimer(){
  clearInterval(timerInterval); timerSegundos=600; actualizarTimer();
  timerInterval=setInterval(()=>{timerSegundos--;actualizarTimer();if(timerSegundos<=0){clearInterval(timerInterval);mostrarAlerta("alertaOTP","aviso","El código expiró. Solicita uno nuevo.");document.getElementById("btnVerificar").disabled=true;}},1000);
}
function actualizarTimer(){
  const min=Math.floor(timerSegundos/60).toString().padStart(2,"0");
  const seg=(timerSegundos%60).toString().padStart(2,"0");
  document.getElementById("timerCuenta").textContent=`${min}:${seg}`;
  document.getElementById("timerTexto").className="timer"+(timerSegundos<=60?" urgente":"");
}
async function verificarCodigo(){
  limpiarAlerta("alertaOTP");
  const codigo=obtenerCodigoOTP();
  if(codigo.length!==6)return;
  mostrarLoader("Verificando código…");
  try{
    const res=await fetch(`${API_BASE}/auth/verificar-codigo`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({correo_institucional:estado.correo,cedula:estado.cedula,codigo})});
    const data=await res.json();
    if(!res.ok)throw new Error(data.detail||"Código incorrecto.");
    clearInterval(timerInterval);
    estado.token=data.token; estado.estudianteId=data.estudiante_id;
    document.getElementById("tokenInfo").textContent=`🔑 Sesión activa para ${estado.correo} · válida hasta ${new Date(data.expira_en).toLocaleString("es-CO")}`;
    await cargarTiposAuxilio(); activarStep(3); mostrarPanel("panelTipoAuxilio");
  }catch(e){mostrarAlerta("alertaOTP","error",e.message);limpiarOTP();setTimeout(()=>document.getElementById("otp0").focus(),100);}
  finally{ocultarLoader();}
}
async function reenviarCodigo(){
  limpiarAlerta("alertaOTP");
  mostrarLoader("Reenviando código…");
  try{
    const res=await fetch(`${API_BASE}/auth/solicitar-codigo`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({correo_institucional:estado.correo,cedula:estado.cedula})});
    const data=await res.json();
    if(!res.ok)throw new Error(data.detail||"Error al reenviar.");
    limpiarOTP(); iniciarTimer(); mostrarAlerta("alertaOTP","exito","Nuevo código enviado.");
    setTimeout(()=>document.getElementById("otp0").focus(),100);
  }catch(e){mostrarAlerta("alertaOTP","error",e.message);}
  finally{ocultarLoader();}
}
function volverALogin(){clearInterval(timerInterval);limpiarAlerta("alertaOTP");activarStep(1);mostrarPanel("panelLogin");}

const ICONOS={ESPECIAL:"🎓",PLAN_PADRINO:"🤝",INCLUSION:"♿",MONITORIA_SERV:"🏫",MONITORIA_ACAD:"📚",DEPORTES:"⚽",CULTURA:"🎭",ESCUELAS:"🎓",CONVENIO:"🤝",TRABAJADOR:"👔",OTRO:"📋"};
async function cargarTiposAuxilio(){
  try{const res=await fetch(`${API_BASE}/solicitudes/tipos-auxilio`);estado.tiposAuxilio=await res.json();
  document.getElementById("auxilioGrid").innerHTML=estado.tiposAuxilio
  .filter(t => t.codigo !== "INCLUSION")
  .map(t=>`    <div class="auxilio-card" id="tipo-${t.codigo}" onclick="seleccionarTipo('${t.codigo}','${t.nombre}')">
      <div class="check-badge">✓</div>
      <div class="auxilio-icon">${ICONOS[t.codigo]||"📋"}</div>
      <div class="auxilio-nombre">${t.nombre}</div>
      <div class="auxilio-desc">${t.descripcion||""}</div>
    </div>`).join("");}
  catch{mostrarAlerta("alertaTipo","error","No se pudieron cargar los tipos de auxilio.");}
}
function seleccionarTipo(codigo,nombre){
  document.querySelectorAll(".auxilio-card").forEach(c=>c.classList.remove("selected"));
  document.getElementById(`tipo-${codigo}`).classList.add("selected");
  estado.tipoAuxilioSeleccionado={codigo,nombre};
  document.getElementById("btnContinuarTipo").disabled=false;
}
function continuarATipo(){if(!estado.tipoAuxilioSeleccionado)return;verificarEstadoPrevio();activarStep(4);mostrarPanel("panelArchivo");}
async function verificarEstadoPrevio(){try{const res=await fetch(`${API_BASE}/archivos/estado/${estado.token}`);const data=await res.json();if(data.intentos_usados>0)actualizarIntentos(data.intentos_usados);}catch{}}
function volverATipoAuxilio(){activarStep(3);mostrarPanel("panelTipoAuxilio");}

function actualizarIntentos(usados){
  estado.intentosUsados=usados;
  for(let i=1;i<=2;i++)document.getElementById(`dot${i}`).className="intento-dot "+(i<=usados?"usado":"disponible");
  const r=2-usados;
  document.getElementById("intentosTexto").textContent=`${r} intento(s) restante(s) de 2`;
  if(r<=0){document.getElementById("btnEnviar").disabled=true;mostrarAlerta("alertaArchivo","error","Has agotado todos los intentos. Contacta a Bienestar Institucional.");}
}
function dragOver(e){e.preventDefault();document.getElementById("uploadZone").classList.add("dragover");}
function dragLeave(){document.getElementById("uploadZone").classList.remove("dragover");}
function dropFile(e){e.preventDefault();dragLeave();if(e.dataTransfer.files[0])procesarArchivo(e.dataTransfer.files[0]);}
function archivoSeleccionado(i){if(i.files[0])procesarArchivo(i.files[0]);}
function procesarArchivo(file){
  limpiarAlerta("alertaArchivo");
  if(file.type!=="application/pdf"){mostrarAlerta("alertaArchivo","error","Solo se aceptan archivos PDF.");return;}
  if(file.size>10*1024*1024){mostrarAlerta("alertaArchivo","error","El archivo supera los 10MB.");return;}
  estado.archivoPDF=file;
  document.getElementById("uploadZone").classList.add("has-file");
  document.getElementById("fileInfo").textContent=`✅ ${file.name} (${(file.size/1024).toFixed(0)} KB)`;
  document.getElementById("fileInfo").classList.remove("hidden");
  document.getElementById("btnEnviar").disabled=false;
}
function dragOverCarta(e){e.preventDefault();document.getElementById("uploadZonaCarta").classList.add("dragover");}
function dragLeaveCarta(){document.getElementById("uploadZonaCarta").classList.remove("dragover");}
function dropCarta(e){e.preventDefault();dragLeaveCarta();if(e.dataTransfer.files[0])procesarCarta(e.dataTransfer.files[0]);}
function cartaSeleccionada(i){if(i.files[0])procesarCarta(i.files[0]);}
function procesarCarta(file){
  if(file.type!=="application/pdf"){mostrarAlerta("alertaArchivo","error","La carta debe ser PDF.");return;}
  if(file.size>10*1024*1024){mostrarAlerta("alertaArchivo","error","La carta supera los 10MB.");return;}
  estado.cartaPDF=file;
  document.getElementById("uploadZonaCarta").classList.add("has-file");
  document.getElementById("cartaInfo").textContent=`✅ ${file.name} (${(file.size/1024).toFixed(0)} KB)`;
  document.getElementById("cartaInfo").classList.remove("hidden");
}
async function enviarFormulario(){
  if(!estado.archivoPDF||!estado.tipoAuxilioSeleccionado)return;
  limpiarAlerta("alertaArchivo");
  mostrarLoader("🤖 El agente IA está analizando tu formulario…");
  const form=new FormData();
  form.append("token",estado.token);
  form.append("tipo_auxilio_codigo",estado.tipoAuxilioSeleccionado.codigo);
  form.append("formulario_pdf",estado.archivoPDF);
  if(estado.cartaPDF)form.append("carta_pdf",estado.cartaPDF);
  try{
    const res=await fetch(`${API_BASE}/archivos/cargar`,{method:"POST",body:form});
    const data=await res.json();
    if(res.ok){
      activarStep(5);mostrarPanel("panelResultado");
      const cm=estado.cartaPDF?" y tu carta":"";
      document.getElementById("contenidoResultado").innerHTML=`
        <div class="resultado-icono">🎉</div>
        <h2 class="resultado-titulo" style="color:var(--verde-oscuro);">¡Solicitud enviada exitosamente!</h2>
        <p class="resultado-msg">Tu formulario${cm} de <strong>${estado.tipoAuxilioSeleccionado.nombre}</strong> fue validado y enviado a <strong>Bienestar Institucional</strong>. Recibirás respuesta en los próximos días hábiles.</p>
        <div class="alerta alerta-exito" style="text-align:left;max-width:420px;margin:0 auto;">✅ Correo enviado a bienestar@cecar.edu.co</div>`;
    }else{
      const det=data.detail||{};
      const intentos=det.intentos_restantes??0;
      const problemas=det.campos_con_problemas||[];
      actualizarIntentos(2-intentos);
      if(intentos<=0){
        activarStep(5);mostrarPanel("panelResultado");
        document.getElementById("contenidoResultado").innerHTML=`
          <div class="resultado-icono">🚫</div>
          <h2 class="resultado-titulo" style="color:var(--error);">Intentos agotados</h2>
          <p class="resultado-msg">Contacta directamente a <strong>Bienestar Institucional</strong>.</p>`;
      }else{
        mostrarAlerta("alertaArchivo","aviso",`El formulario tiene errores. Corrígelos y vuelve a subir. (${intentos} intento(s) restante(s))`,
          problemas.length?problemas:[det.motivo||"Verifica todos los campos."]);
        estado.archivoPDF=null;
        document.getElementById("uploadZone").classList.remove("has-file");
        document.getElementById("fileInfo").classList.add("hidden");
        document.getElementById("archivoInput").value="";
        document.getElementById("btnEnviar").disabled=true;
      }
    }
  }catch(e){mostrarAlerta("alertaArchivo","error","Error de conexión. Intenta de nuevo.");}
  finally{ocultarLoader();}
}
function reiniciar(){
  clearInterval(timerInterval);
  estado={token:null,estudianteId:null,correo:null,cedula:null,tipoAuxilioSeleccionado:null,tiposAuxilio:[],archivoPDF:null,cartaPDF:null,intentosUsados:0};
  document.getElementById("correo").value="";document.getElementById("cedula").value="";
  limpiarOTP();
  document.getElementById("uploadZone").classList.remove("has-file");document.getElementById("fileInfo").classList.add("hidden");document.getElementById("archivoInput").value="";
  document.getElementById("uploadZonaCarta").classList.remove("has-file");document.getElementById("cartaInfo").classList.add("hidden");document.getElementById("cartaInput").value="";
  limpiarAlerta("alertaLogin");activarStep(1);mostrarPanel("panelLogin");
}
document.addEventListener("keydown",e=>{
  if(e.key==="Enter"){
    if(!document.getElementById("panelLogin").classList.contains("hidden"))enviarCodigo();
    else if(!document.getElementById("panelOTP").classList.contains("hidden")&&obtenerCodigoOTP().length===6)verificarCodigo();
  }
});