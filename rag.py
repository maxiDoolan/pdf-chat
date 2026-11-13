import streamlit as st
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- FUNCIONES ---
def leer_pdf(archivo):
    reader = PdfReader(archivo)
    texto = ""
    for pagina in reader.pages:
        texto += pagina.extract_text()
    return texto

def crear_trozos(texto, tamanio=2000):
    trozos = []
    for i in range(0, len(texto), tamanio):
        trozos.append(texto[i:i+tamanio])
    return trozos

def buscar_relevantes(trozos, pregunta):
    relevantes = []
    palabras = pregunta.lower().split()
    for trozo in trozos:
        if any(palabra in trozo.lower() for palabra in palabras):
            relevantes.append(trozo)
    return relevantes[:3] if relevantes else trozos[:3]

def preguntar(trozos, pregunta, idioma):
    contexto = "\n\n".join(buscar_relevantes(trozos, pregunta))
    
    respuesta = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": f"Respondé preguntas basándote SOLO en el contexto dado. SIEMPRE respondé en {idioma}, sin excepción, sin importar el idioma de la pregunta"},
            {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"}
        ]
    )
    return respuesta.choices[0].message.content

def resumir(trozos, idioma):
    contexto = "\n\n".join(trozos[:5])
    respuesta = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": f"Resumí el documento en 5 puntos clave. Respondé en {idioma}."},
            {"role": "user", "content": contexto}
        ]
    )
    return respuesta.choices[0].message.content

# --- UI ---
st.title("📄 Chat con tu PDF")

with st.sidebar:
    st.header("⚙️ Configuración")
    idioma = st.selectbox("🌐 Idioma de respuesta:", ["Español", "Inglés", "Portugués"])
    st.divider()
    st.caption("👨‍💻 Creado por Maximiliano Doolan")

archivo = st.file_uploader("Subí tu PDF", type="pdf")

if archivo:
    if "trozos" not in st.session_state or st.session_state.archivo != archivo.name:
        with st.spinner("Procesando PDF..."):
            texto = leer_pdf(archivo)
            st.session_state.trozos = crear_trozos(texto)
            st.session_state.archivo = archivo.name
            st.session_state.historial = []
        st.success(f"✅ PDF procesado — {len(st.session_state.trozos)} secciones")

    if st.button("📊 Dame los 5 puntos clave"):
        with st.spinner("Analizando..."):
            resumen = resumir(st.session_state.trozos, idioma)
            st.info(resumen)

    st.divider()
    st.subheader("💬 ¿Qué querés saber sobre este documento?")

    if st.button("🗑️ Limpiar chat"):
        st.session_state.historial = []
        st.rerun()

    if "historial" not in st.session_state:
        st.session_state.historial = []

    for mensaje in st.session_state.historial:
        with st.chat_message(mensaje["role"]):
            st.write(mensaje["content"])

    pregunta = st.chat_input("Hacé una pregunta sobre el PDF...")

    if pregunta:
        st.session_state.historial.append({"role": "user", "content": pregunta})
        
        with st.spinner("Pensando..."):
            respuesta = preguntar(st.session_state.trozos, pregunta, idioma)
        
        st.session_state.historial.append({"role": "assistant", "content": respuesta})
        st.rerun()
else:
    st.info("👆 Subí un PDF para empezar")