import streamlit as st
import grpc
import batalla_pb2
import batalla_pb2_grpc
import time

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Render Free requiere SSL para conexiones externas gRPC
URL_SERVIDOR = 'batallanaval-grcp-online.onrender.com:443'

def iniciar_conexion():
    if 'stub' not in st.session_state:
        try:
            # Conexión SEGURA obligatoria para Render
            credenciales = grpc.ssl_channel_credentials()
            canal = grpc.secure_channel(URL_SERVIDOR, credenciales)
            st.session_state.stub = batalla_pb2_grpc.MotorMultijugadorStub(canal)
            st.session_state.id_jugador = None
        except Exception as e:
            st.error(f"Error al conectar con el servidor: {e}")

# --- INTERFAZ ---
st.set_page_config(page_title="Batalla Naval - UACAM", layout="wide")
st.title("🚢 Batalla Naval Royale Online")
st.write("Facultad de Ingeniería - Sistemas Computacionales")

iniciar_conexion()

# 1. FLUJO DE REGISTRO
if st.session_state.id_jugador is None:
    st.info("Ingresa el número de jugadores para iniciar la batalla.")
    total_j = st.number_input("¿Cuántos jugadores esperan?", min_value=2, max_value=4, value=2)
    
    if st.button("Registrarme y Unirme"):
        try:
            # NOMBRE CORRECTO: PeticionRegistro (verificado en tu pb2.py)
            solicitud = batalla_pb2.PeticionRegistro(total_esperados=total_j)
            respuesta = st.session_state.stub.RegistrarJugador(solicitud)
            
            st.session_state.id_jugador = respuesta.id_jugador
            st.success(f"¡Conectado! Tu ID es: {st.session_state.id_jugador}")
            time.sleep(1.5)
            st.rerun()
            
        except grpc.RpcError as e:
            st.error(f"Error de red gRPC: {e.details()}")
            st.warning("Verifica que el servidor en Render esté 'Live'.")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")

# 2. PANEL DE JUEGO
else:
    id_j = st.session_state.id_jugador
    st.sidebar.success(f"Jugador {id_j} en línea")
    
    col_acc, col_tab = st.columns([1, 2])
    
    with col_acc:
        st.write("### Panel de Control")
        if st.button("Actualizar Tablero"):
            st.rerun()
            
        if st.button("Ver Marcador"):
            try:
                res = st.session_state.stub.ObtenerMarcador(batalla_pb2.Vacio())
                st.info(res.texto)
            except:
                st.error("Servidor no responde.")
                
        if st.button("Cerrar Sesión"):
            st.session_state.id_jugador = None
            st.rerun()

    with col_tab:
        st.write("### Radar de Combate")
        try:
            # Obtenemos la matriz desde el servidor
            tablero = st.session_state.stub.ObtenerEstadoTablero(batalla_pb2.Vacio())
            
            # Dibujamos el tablero de forma visual
            for fila in tablero.filas:
                cols = st.columns(len(fila.valores))
                for i, valor in enumerate(fila.valores):
                    if valor == 0:
                        cols[i].write("🟦") # Agua
                    elif valor == -1:
                        cols[i].write("⚪") # Fallo
                    else:
                        cols[i].write("💥") # ¡Impacto!
        except Exception as e:
            st.warning("Esperando datos del tablero...")

