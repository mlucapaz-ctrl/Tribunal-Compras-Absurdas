"""En esta nueva versión comparada con la anterior, he añadido que "Mitral-nemo" (el modelo del juez) también redacte un titular y una entradilla al más puro estilo clickbait para la prensa amarilla, basándose en la compra absurda y la sentencia dictada. Este titular se muestra en rojo en la pantalla final para darle un toque de escándalo mediático. Además, he incluido esta noticia sensacionalista tanto en el PDF de la sentencia como en el acta de conclusiones, para que el jugador pueda compartirla o guardarla junto con el veredicto oficial. ¡Ahora el juicio no solo es absurdo, sino también un bombazo informativo!"""

import streamlit as st
import streamlit.components.v1 as components
import ollama
import time
import pandas as pd
from fpdf import FPDF
import json
import os
import random

# --- TRES AGENTES DE IA DIFERENTES ---
MODELO_DEBATE = "gemma2:2b"
MODELO_JUEZ = "mistral-nemo"
MODELO_GUIONISTA = "qwen2.5:3b"

# ==========================================
# 🎮 MODO MINIJUEGO (Lluvia de Emojis Rotatorios + IA Predictiva)
# ==========================================
if "juego" in st.query_params:
    st.set_page_config(page_title="Ejecución de Sentencia", page_icon="⚖️", layout="centered")
    
    if os.path.exists("juicio_actual.json"):
        with open("juicio_actual.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
    else:
        datos = {"objeto": "Desconocido", "fiscal": "", "abogado": "", "juez": "Error.", "palabras_ok": ["💎", "✨", "🏆"], "palabras_mal": ["💩", "💸", "🗑️"]}

    sentencia_limpia = datos['juez'].replace('\n', '<br>').replace('"', '\\"').replace("'", "\\'")
    json_palabras_ok = json.dumps(datos.get('palabras_ok', ["💎", "✨", "🏆"]))
    json_palabras_mal = json.dumps(datos.get('palabras_mal', ["💩", "💸", "🗑️"]))
    emojis_buenos_str = " ".join(datos.get('palabras_ok', ["💎", "✨", "🏆"]))
    emojis_malos_str = " ".join(datos.get('palabras_mal', ["💩", "💸", "🗑️"]))
    
    html_juego = f"""
    <style>
        body {{ font-family: 'Arial', sans-serif; background-color: #1e272e; color: white; margin: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; }}
        h1, h2, p {{ text-align: center; }}
        .pantalla {{ display: none; width: 100%; max-width: 700px; padding: 20px; box-sizing: border-box; animation: fadeIn 0.4s; }}
        .activa {{ display: block; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        #game-canvas {{ background-color: #2c3e50; border: 4px solid #f1c40f; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); cursor: none; }}
        .btn {{ background-color: #e74c3c; color: white; border: none; padding: 15px 30px; font-size: 20px; border-radius: 8px; cursor: pointer; text-transform: uppercase; font-weight: bold; transition: 0.2s; box-shadow: 0 5px 0 #c0392b; margin-top: 20px; }}
        .btn:hover {{ transform: translateY(2px); box-shadow: 0 3px 0 #c0392b; }}
        .caja-sentencia {{ background-color: #2c3e50; padding: 30px; border-radius: 15px; border: 4px solid #2ecc71; text-align: left; margin-top: 20px; overflow-y: auto; max-height: 400px; }}
    </style>
    <div id="pantalla-inicio" class="pantalla activa">
        <h1 style="color: #f1c40f; font-size: 35px; margin-bottom: 5px;">⚖️ ARGUMENTOS AL VUELO</h1>
        <h2 style="color: #bdc3c7; margin-top: 0;">Caso: '{datos['objeto']}'</h2>
        <p style="font-size: 18px; line-height: 1.5;">Atrapa las pruebas <b>A FAVOR</b> y esquiva las objeciones <b>EN CONTRA</b> generadas por la IA.</p>
        <div style="background-color: #34495e; padding: 15px; border-radius: 10px; display: inline-block; margin: 15px 0; font-size: 22px;">
            <p style="margin: 5px 0; color: #2ecc71;">✅ <b>Atrápalos (+15 Pts):</b> {emojis_buenos_str}</p>
            <p style="margin: 5px 0; color: #e74c3c;">❌ <b>Esquívalos (-10 Pts):</b> {emojis_malos_str}</p>
        </div>
        <br><button class="btn" onclick="iniciarJuego()">¡Empezar Juicio!</button>
    </div>
    <div id="pantalla-juego" class="pantalla" style="text-align: center;"><canvas id="game-canvas" width="650" height="450"></canvas></div>
    <div id="pantalla-victoria" class="pantalla">
        <h1 style="color: #2ecc71; font-size: 45px; margin-top: 0;">¡ORDEN EN LA SALA! 💥</h1>
        <div class="caja-sentencia"><h2 style="color: #2ecc71; margin-top: 0; border-bottom: 2px solid #2ecc71; padding-bottom: 10px;">📜 VEREDICTO OFICIAL:</h2>
        <div style="font-size: 20px; line-height: 1.6; color: #ecf0f1;">{sentencia_limpia}</div></div>
    </div>
    <div id="pantalla-derrota" class="pantalla" style="text-align: center;">
        <h1 style="color: #e74c3c; font-size: 50px;">¡CAOS TOTAL! 📢</h1>
        <p style="font-size: 22px;">No has conseguido suficientes pruebas válidas (Mínimo: 50).</p>
        <h2 id="puntos-finales" style="color: #f1c40f;">Puntos: 0</h2>
        <button class="btn" onclick="reiniciarJuego()">Volver a intentar</button>
    </div>
    <script>
        const canvas = document.getElementById('game-canvas');
        const ctx = canvas.getContext('2d');
        const palabrasOk = {json_palabras_ok};
        const palabrasMal = {json_palabras_mal};
        let score = 0, timeLeft = 20, gameLoop, timerLoop, spawnLoop, isPlaying = false;
        let player = {{ x: canvas.width / 2, y: canvas.height - 60, width: 80, height: 40, emoji: '⚖️' }};
        let items = [], historialX = [];

        canvas.addEventListener('mousemove', function(evt) {{
            const rect = canvas.getBoundingClientRect();
            player.x = evt.clientX - rect.left - (player.width / 2);
            if(player.x < 0) player.x = 0;
            if(player.x + player.width > canvas.width) player.x = canvas.width - player.width;
            if(isPlaying) {{ historialX.push(player.x); if(historialX.length > 50) historialX.shift(); }}
        }});

        function cambiarPantalla(id) {{
            document.querySelectorAll('.pantalla').forEach(el => el.classList.remove('activa'));
            document.getElementById(id).classList.add('activa');
        }}

        function spawnItem() {{
            if(!isPlaying) return;
            const esBueno = Math.random() > 0.4;
            const listaTextos = esBueno ? palabrasOk : palabrasMal;
            const textoRandom = (listaTextos && listaTextos.length > 0) ? listaTextos[Math.floor(Math.random() * listaTextos.length)].toUpperCase() : (esBueno ? "💎" : "💩");
            let spawnX = Math.random() * (canvas.width - 100);
            if (!esBueno && historialX.length > 20 && Math.random() < 0.75) {{
                spawnX = (historialX.reduce((a, b) => a + b, 0) / historialX.length) + (Math.random() * 60 - 30);
            }}
            items.push({{ x: spawnX, y: -40, width: 50, height: 50, texto: textoRandom, bueno: esBueno, angle: 0, speed: 3.0 + Math.random() * 2.5 }});
        }}

        function actualizarYDibujar() {{
            if (!isPlaying) return;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "white"; ctx.font = "24px Arial"; ctx.textAlign = "left"; ctx.fillText("Puntos: " + score, 20, 40);
            ctx.textAlign = "right"; ctx.fillStyle = timeLeft <= 5 ? "#e74c3c" : "white"; ctx.fillText("Tiempo: " + timeLeft + "s", canvas.width - 20, 40);
            ctx.font = "50px Arial"; ctx.textAlign = "center"; ctx.fillText(player.emoji, player.x + player.width/2, player.y + 35);

            for (let i = 0; i < items.length; i++) {{
                let item = items[i];
                item.y += item.speed; item.angle += item.speed * 0.02;
                ctx.save(); ctx.translate(item.x + item.width/2, item.y + item.height/2); ctx.rotate(item.angle);
                ctx.font = "50px Arial"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(item.texto, 0, 0); ctx.restore();

                if (item.x + item.width/2 > player.x && item.x + item.width/2 < player.x + player.width && item.y + item.height/2 > player.y && item.y + item.height/2 < player.y + player.height) {{
                    score += item.bueno ? 15 : -10;
                    document.getElementById('game-canvas').style.borderColor = item.bueno ? '#2ecc71' : '#e74c3c';
                    setTimeout(() => document.getElementById('game-canvas').style.borderColor = '#f1c40f', 150);
                    items.splice(i, 1); i--;
                }} else if (item.y > canvas.height) {{ items.splice(i, 1); i--; }}
            }}
            gameLoop = requestAnimationFrame(actualizarYDibujar);
        }}

        function iniciarJuego() {{
            cambiarPantalla('pantalla-juego'); score = 0; timeLeft = 20; items = []; historialX = []; isPlaying = true;
            actualizarYDibujar(); spawnLoop = setInterval(spawnItem, 350);
            timerLoop = setInterval(() => {{ timeLeft--; if (timeLeft <= 0) finalizarJuego(); }}, 1000);
        }}

        function finalizarJuego() {{
            isPlaying = false; cancelAnimationFrame(gameLoop); clearInterval(spawnLoop); clearInterval(timerLoop);
            if (score >= 50) cambiarPantalla('pantalla-victoria');
            else {{ document.getElementById('puntos-finales').innerText = "Puntos conseguidos: " + score; cambiarPantalla('pantalla-derrota'); }}
        }}
        function reiniciarJuego() {{ cambiarPantalla('pantalla-inicio'); }}
    </script>
    """
    components.html(html_juego, height=800, scrolling=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Volver al Menú Principal", use_container_width=True):
        st.query_params.clear()
        st.rerun()
    st.stop()

# ==========================================
# ⚖️ SALA DE VISTAS (PANTALLA PRINCIPAL CON MEMORIA)
# ==========================================
st.set_page_config(page_title="Compras Absurdas", page_icon="⚖️", layout="centered")

# --- SISTEMA DE MEMORIA (BARRA LATERAL) ---
st.sidebar.title("💾 Estado del Juicio")
archivo_subido = st.sidebar.file_uploader("📂 Cargar Juicio Guardado (.json)", type=["json"])
if archivo_subido is not None:
    if st.sidebar.button("⬇️ Restaurar Memoria"):
        datos_guardados = json.load(archivo_subido)
        for clave, valor in datos_guardados.items():
            st.session_state[clave] = valor
        st.sidebar.success("¡Memoria restaurada!")
        st.rerun()

# --- INICIALIZAR VARIABLES DE ESTADO ---
if "juicio_iniciado" not in st.session_state:
    st.session_state.juicio_iniciado = False

st.title("⚖️ COMPRAS ABSURDAS")
st.markdown("---")

def generador_texto(flujo):
    for trocito in flujo: yield trocito['message']['content']

RONDAS = 2

# Pantalla de inicio si no hay juicio activo
if not st.session_state.juicio_iniciado:
    compra = st.text_input("Introduce la compra absurda que se va a debatir hoy:", placeholder="Ej: Un peluche de una tostada")
    if st.button("🔨 Comenzar el Juicio", type="primary") and compra:
        st.session_state.juicio_iniciado = True
        st.session_state.compra = compra
        st.session_state.ronda_actual = 1
        st.session_state.puntos_fiscal = 10
        st.session_state.puntos_abogado = 10
        st.session_state.ui_chat = []
        st.session_state.turno_pendiente = True # Arranca el turno 1 solo
        
        sys_fiscal = "ACTÚA COMO UN FISCAL SÚPERESTRICTO. Interpretas a un fiscal dramático y sarcástico. Critica el objeto inútil comprado. Tono indignado. Como máximo 4 líneas."
        sys_abogado = "ACTÚA COMO UN ABOGADO SÚPERDEFENSOR. Interpretas a un abogado excéntrico. Defiende el objeto inútil. Tono pedante. Como máximo 4 líneas."
        
        st.session_state.historial_fiscal = [{"role": "system", "content": sys_fiscal}, {"role": "user", "content": f"Critica esta compra: '{compra}'"}]
        st.session_state.historial_abogado = [{"role": "system", "content": sys_abogado}]
        st.rerun()

# --- EL MOTOR DEL JUICIO (Pausable) ---
if st.session_state.juicio_iniciado:
    
    # Botón de Guardado (Barra lateral)
    estado_actual_json = json.dumps({
        "juicio_iniciado": st.session_state.juicio_iniciado,
        "compra": st.session_state.compra,
        "ronda_actual": st.session_state.ronda_actual,
        "puntos_fiscal": st.session_state.puntos_fiscal,
        "puntos_abogado": st.session_state.puntos_abogado,
        "ui_chat": st.session_state.ui_chat,
        "historial_fiscal": st.session_state.historial_fiscal,
        "historial_abogado": st.session_state.historial_abogado,
        "turno_pendiente": st.session_state.get("turno_pendiente", False)
    }, ensure_ascii=False)
    
    st.sidebar.download_button(label="💾 Pausar y Guardar Estado (.json)", data=estado_actual_json, file_name="memoria_juicio.json", mime="application/json")

    # Re-dibujar toda la "Línea de Tiempo" guardada
    for item in st.session_state.ui_chat:
        tipo, contenido = item[0], item[1]
        if tipo == "Ronda":
            st.subheader(f"🔔 RONDA {contenido}")
        elif tipo in ["Fiscal", "Abogado"]:
            avatar = "🧐" if tipo == "Fiscal" else "👨‍⚖️"
            with st.chat_message(tipo, avatar=avatar): st.write(contenido)
        elif tipo == "Grafico":
            ronda_grafico, pts_f, pts_a = contenido
            st.markdown(f"**📈 Puntuación al final de la Ronda {ronda_grafico}:**")
            st.bar_chart(pd.DataFrame({"Puntos": [pts_f, pts_a]}, index=["Fiscal 🧐", "Abogado 👨‍⚖️"]), color=["#FF4B4B"])
            st.markdown("---")

    # --- EJECUCIÓN DEL TURNO ---
    if st.session_state.get("turno_pendiente", False):
        st.session_state.turno_pendiente = False
        st.session_state.ui_chat.append(("Ronda", st.session_state.ronda_actual))
        st.subheader(f"🔔 RONDA {st.session_state.ronda_actual}")
        
        with st.chat_message("Fiscal", avatar="🧐"):
            flujo_fiscal = ollama.chat(model=MODELO_DEBATE, messages=st.session_state.historial_fiscal, stream=True)
            respuesta_fiscal = st.write_stream(generador_texto(flujo_fiscal))
            st.session_state.historial_fiscal.append({"role": "assistant", "content": respuesta_fiscal})
            st.session_state.historial_abogado.append({"role": "user", "content": f"El fiscal dijo: '{respuesta_fiscal}'. Refútalo."})
            st.session_state.ui_chat.append(("Fiscal", respuesta_fiscal))
            st.session_state.puntos_fiscal += random.randint(5, 25)

        time.sleep(1)

        with st.chat_message("Abogado", avatar="👨‍⚖️"):
            flujo_abogado = ollama.chat(model=MODELO_DEBATE, messages=st.session_state.historial_abogado, stream=True)
            respuesta_abogado = st.write_stream(generador_texto(flujo_abogado))
            st.session_state.historial_abogado.append({"role": "assistant", "content": respuesta_abogado})
            if st.session_state.ronda_actual < RONDAS:
                st.session_state.historial_fiscal.append({"role": "user", "content": f"El abogado dijo: '{respuesta_abogado}'. Ataca de nuevo."})
            st.session_state.ui_chat.append(("Abogado", respuesta_abogado))
            st.session_state.puntos_abogado += random.randint(5, 25)
        
        st.markdown(f"**📈 Puntuación al final de la Ronda {st.session_state.ronda_actual}:**")
        st.bar_chart(pd.DataFrame({"Puntos": [st.session_state.puntos_fiscal, st.session_state.puntos_abogado]}, index=["Fiscal 🧐", "Abogado 👨‍⚖️"]), color=["#FF4B4B"])
        st.markdown("---")
        st.session_state.ui_chat.append(("Grafico", (st.session_state.ronda_actual, st.session_state.puntos_fiscal, st.session_state.puntos_abogado)))
        st.rerun()

    # --- BOTONES DE CONTROL ---
    else:
        if st.session_state.ronda_actual < RONDAS:
            if st.button("🗣️ Siguiente Turno", type="primary"):
                st.session_state.ronda_actual += 1
                st.session_state.turno_pendiente = True
                st.rerun()

        elif st.session_state.ronda_actual == RONDAS and not st.session_state.get("juicio_terminado", False):
            st.subheader("🤫 El Juez Supremo se retira a deliberar...")
            
            if st.button("👨‍⚖️ Dictar Sentencia Final", type="primary"):
                with st.spinner('Redactando la sentencia y generando la portada del periódico...'):
                    
                    mensajes_roles = [m[1] for m in st.session_state.ui_chat if m[0] in ["Fiscal", "Abogado"]]
                    resp_f_final = mensajes_roles[-2] if len(mensajes_roles) >= 2 else ""
                    resp_a_final = mensajes_roles[-1] if len(mensajes_roles) >= 1 else ""
                    
                    # 1. SENTENCIA DEL JUEZ
                    sys_juez = "Eres un juez cómico. Decide quién gana y dicta una sentencia absurda. Empieza con 'DICTO SENTENCIA:'. Responde en español."
                    res_juez = ollama.chat(model=MODELO_JUEZ, messages=[{"role": "system", "content": sys_juez}, {"role": "user", "content": f"Fiscal: '{resp_f_final}'. Abogado: '{resp_a_final}'. Juzga la compra '{st.session_state.compra}'."}])
                    respuesta_juez = res_juez['message']['content']

                    # 2. NOTICIA (PERIODISTA) -> Se ejecuta AHORA para poder meterla en los documentos
                    sys_periodista = """Eres redactor jefe de prensa amarilla. Escribe un titular súper exagerado (estilo clickbait) y una entradilla breve. Usa Markdown y emojis."""
                    res_periodista = ollama.chat(model=MODELO_JUEZ, messages=[{"role": "system", "content": sys_periodista}, {"role": "user", "content": f"Compra: '{st.session_state.compra}'. Sentencia: '{respuesta_juez}'."}])
                    noticia_clickbait = res_periodista['message']['content']
                    
                    # 3. EMOJIS (Para el juego)
                    sys_palabras = """Eres director de arte. Genera ÚNICAMENTE 6 emojis separados por comas. 3 positivos, 3 negativos."""
                    try:
                        res_palabras = ollama.chat(model=MODELO_GUIONISTA, messages=[{"role": "system", "content": sys_palabras}, {"role": "user", "content": f"Objeto: {st.session_state.compra}"}])
                        emojis_lista = [e.strip() for e in res_palabras['message']['content'].strip().split(',') if e.strip()]
                        if len(emojis_lista) >= 6: palabras_ok, palabras_mal = emojis_lista[0:3], emojis_lista[3:6]
                        else: raise ValueError()
                    except: palabras_ok, palabras_mal = ["💎", "✨", "🏆"], ["💩", "💸", "🗑️"]

                    with open("juicio_actual.json", "w", encoding="utf-8") as archivo:
                        json.dump({"objeto": st.session_state.compra, "juez": respuesta_juez, "palabras_ok": palabras_ok, "palabras_mal": palabras_mal}, archivo, ensure_ascii=False)

                    # 4. GENERAR PDF (Ahora incluye la noticia)
                    def crear_pdf(objeto, sentencia, noticia):
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", 'B', 16)
                        pdf.cell(200, 10, txt="TRIBUNAL DE LAS COMPRAS ABSURDAS", ln=True, align='C')
                        pdf.ln(10)
                        pdf.set_font("Arial", 'B', 12)
                        pdf.cell(200, 10, txt=f"OBJETO: {objeto.encode('latin-1', 'replace').decode('latin-1')}", ln=True, align='L')
                        pdf.ln(5)
                        pdf.set_font("Arial", '', 12)
                        pdf.multi_cell(0, 10, txt=sentencia.encode('latin-1', 'replace').decode('latin-1'))
                        
                        pdf.ln(15)
                        pdf.set_font("Arial", 'B', 14)
                        pdf.cell(200, 10, txt="--- EXCLUSIVA EN LA PRENSA ---", ln=True, align='L')
                        pdf.set_font("Arial", '', 12)
                        # Limpiamos los emojis de la noticia solo para el PDF porque FPDF explota con ellos
                        noticia_sin_emojis = noticia.encode('latin-1', 'ignore').decode('latin-1')
                        pdf.multi_cell(0, 10, txt=noticia_sin_emojis)
                        
                        return pdf.output(dest='S').encode('latin-1')

                    pdf_bytes = crear_pdf(st.session_state.compra, respuesta_juez, noticia_clickbait)
                    
                    # 5. GENERAR ACTA MD DETALLADA (Resumen Fiscal, Abogado y Juez)
                    url_juego = "http://localhost:8501/?juego=true"
                    sys_secretario = f"""Eres el Secretario Judicial del Tribunal de las Compras Absurdas.
                    Tu tarea es leer la información del caso y redactar el Acta Oficial de Conclusiones.
                    Tu respuesta DEBE ser el documento final estructurado en Markdown. 
                    Debes incluir obligatoriamente estas secciones con encabezados (##):
                    1. Un título creativo para el caso.
                    2. Resumen de los argumentos del Fiscal.
                    3. Resumen de los argumentos del Abogado.
                    4. Conclusiones finales basadas en el veredicto del Juez.
                    5. Despedida, donde añadirás EXACTAMENTE este enlace: [👉 HAZ CLIC AQUÍ PARA EJECUTAR LA SENTENCIA (MINIJUEGO)]({url_juego})
                    
                    NO me hables a mí, genera SOLO el texto del documento."""

                    contexto_acta = f"Objeto debatido: '{st.session_state.compra}'. Argumento final del Fiscal: '{resp_f_final}'. Argumento final del Abogado: '{resp_a_final}'. Veredicto del Juez: '{respuesta_juez}'."
                    res_secretario = ollama.chat(model=MODELO_JUEZ, messages=[{"role": "system", "content": sys_secretario}, {"role": "user", "content": contexto_acta}])
                    acta_texto = res_secretario['message']['content']
                    
                    # Unimos la noticia amarillista y el acta formal en un solo archivo
                    texto_final_md = f"{noticia_clickbait}\n\n---\n\n{acta_texto}"
                    acta_bytes = texto_final_md.encode('utf-8')

                    # GUARDAR ESTADOS PARA MOSTRAR EN PANTALLA
                    st.session_state.noticia_clickbait = noticia_clickbait
                    st.session_state.acta_bytes = acta_bytes
                    st.session_state.pdf_bytes = pdf_bytes
                    st.session_state.juicio_terminado = True
                    st.rerun()

    # --- PANTALLA FINAL ---
    if st.session_state.get("juicio_terminado", False):
        st.success("**VEREDICTO FINAL DICTADO EN SECRETO**")
        
        # AQUI SE DIBUJA LA NOTICIA EN ROJO EN LA WEB
        st.markdown("<br>", unsafe_allow_html=True)
        st.error("📰 **¡EXTRA, EXTRA! LA PRENSA HA FILTRADO EL ESCÁNDALO:**")
        st.markdown(f"> {st.session_state.noticia_clickbait}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.info("Descarga la sentencia o las conclusiones oficiales. Dentro encontrarás la exclusiva de prensa y el enlace para jugar.")
        
        st.download_button(label="📄 Descargar Sentencia (.PDF)", data=st.session_state.pdf_bytes, file_name="Sentencia.pdf", mime="application/pdf")
        st.download_button(label="📝 Descargar Conclusiones (.MD)", data=st.session_state.acta_bytes, file_name="Conclusiones_con_Noticia.md", mime="text/markdown")
        
        if st.button("🔄 Reiniciar y limpiar memoria"):
            st.session_state.clear()
            st.rerun()