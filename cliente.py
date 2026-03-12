import streamlit as st
import grpc
import batalla_pb2
import batalla_pb2_grpc
import time

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Render requiere SSL (secure_channel) para conexiones externas
URL_SERVIDOR = 'batallanaval-grcp-online.onrender.com'

def iniciar_conexion():
    if 'stub' not in st.session_state:
        try:
            # Conexión SEGURA obligatoria para Render Free
            credenciales = grpc.ssl_channel_credentials()
            canal = grpc.secure_channel(URL_SERVIDOR, credenciales)
            st.session_state.stub = batalla_pb2_grpc.MotorMultijugadorStub(canal)
            st.session_state.id_jugador = None
        except Exception as e:
            st.error(f"Fallo al crear el canal de comunicación: {e}")

# --- INTERFAZ ---
st.set_page_config(page_title="Batalla Naval - UACAM", layout="wide")
st.title("🚢 Batalla Naval Royale Online")
st.write("Facultad de Ingeniería - Ingeniería en Sistemas Computacionales")

iniciar_conexion()

# 1. FLUJO DE REGISTRO
if st.session_state.id_jugador is None:
    st.info("Regístrate para entrar a la partida.")
    total_j = st.number_input("¿Cuántos jugadores serán en total?", min_value=2, max_value=4, value=2)
    
    if st.button("Registrarme y Unirme"):
        try:
            # IMPORTANTE: El nombre del mensaje debe ser EXACTO al de tu .proto
            # Si en tu .proto se llama de otra forma, cámbialo aquí:
            solicitud = batalla_pb2.SolicitudRegistro(total_esperados=total_j)
            respuesta = st.session_state.stub.RegistrarJugador(solicitud)
            
            st.session_state.id_jugador = respuesta.id_jugador
            st.success(f"¡Conectado! Eres el Jugador ID: {st.session_state.id_jugador}")
            time.sleep(1)
            st.rerun()
            
        except grpc.RpcError as e:
            st.error(f"Error de red: {e.code()} - {e.details()}")
            st.warning("Verifica que el servidor en Render esté 'Live'.")
        except AttributeError:
            st.error("Error: 'SolicitudRegistro' no coincide con tu archivo batalla_pb2.py")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")

# 2. PANEL DE JUEGO (Si ya está conectado)
else:
    id_actual = st.session_state.id_jugador
    st.sidebar.success(f"Conectado como Jugador {id_actual}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### Acciones")
        if st.button("Ver Marcador"):
            res = st.session_state.stub.ObtenerMarcador(batalla_pb2.Vacio())
            st.text(res.texto)
            
        if st.button("Salir de la partida"):
            st.session_state.id_jugador = None
            st.rerun()

    with col2:
        st.write("### Tablero de Batalla")
        try:
            tablero = st.session_state.stub.ObtenerEstadoTablero(batalla_pb2.Vacio())
            # Aquí va tu lógica para dibujar la matriz...
            st.write("Conectado al servidor de Render correctamente.")
        except:
            st.error("Error al obtener el tablero.")
