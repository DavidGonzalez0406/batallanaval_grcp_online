import streamlit as st
import grpc
import batalla_pb2
import batalla_pb2_grpc
import time

# --- CONFIGURACIÓN DE CONEXIÓN ---
# No incluyas 'https://' ni el puerto ':443'. Render lo gestiona con SSL.
URL_SERVIDOR = 'batallanaval-grcp-online.onrender.com'

def iniciar_conexion():
    if 'stub' not in st.session_state:
        # Render GRATIS requiere conexión SEGURA (SSL) para gRPC externo
        credenciales = grpc.ssl_channel_credentials()
        canal = grpc.secure_channel(URL_SERVIDOR, credenciales)
        st.session_state.stub = batalla_pb2_grpc.MotorMultijugadorStub(canal)
        st.session_state.id_jugador = None

# --- INTERFAZ DE STREAMLIT ---
st.set_page_config(page_title="Batalla Naval Royale - UACAM", layout="wide")
st.title("🚢 Batalla Naval Royale Online")
st.subheader("Proyecto Facultad de Ingeniería - Sistemas")

iniciar_conexion()

# 1. REGISTRO DE JUGADOR
if st.session_state.id_jugador is None:
    st.info("Bienvenido. Para iniciar la partida, regístrate.")
    total_j = st.number_input("¿Cuántos jugadores esperan?", min_value=2, max_value=4, value=2)
    
    if st.button("Registrarme y Unirme"):
        try:
            respuesta = st.session_state.stub.RegistrarJugador(
                batalla_pb2.SolicitudRegistro(total_esperados=total_j)
            )
            st.session_state.id_jugador = respuesta.id_jugador
            st.success(f"¡Registrado con éxito! Eres el Jugador ID: {st.session_state.id_jugador}")
            st.rerun()
        except grpc.RpcError as e:
            st.error(f"Error de conexión con el servidor: {e.details()}")
            st.warning("Asegúrate de que el servidor en Render esté en estado 'Live'.")

# 2. ESPERA Y JUEGO (Si ya está registrado)
else:
    id_j = st.session_state.id_jugador
    st.sidebar.write(f"👤 **Jugador ID:** {id_j}")
    
    # Aquí puedes agregar el resto de tu lógica: 
    # Colocar barcos, Disparar, Obtener Estado del Tablero, etc.
    
    if st.sidebar.button("Cerrar Sesión / Salir"):
        st.session_state.id_jugador = None
        st.rerun()

    # Ejemplo de cómo pedir el estado del tablero
    try:
        tablero = st.session_state.stub.ObtenerEstadoTablero(batalla_pb2.Vacio())
        st.write("### Estado del Mar")
        # Lógica para mostrar la matriz del tablero...
    except Exception as e:
        st.error("Se perdió la conexión con el servidor.")
