import streamlit as st
import grpc
import batalla_pb2
import batalla_pb2_grpc

# Configuración visual de la página
st.set_page_config(page_title="Batalla Naval Royale - UACAM", layout="wide")
st.title("🚢 Batalla Naval Royale (gRPC Web)")

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Reemplaza con tu URL real de Render sin el https://
URL_RENDER = "batallanaval-grcp-online.onrender.com" 

if 'stub' not in st.session_state:
    try:
        # Render requiere conexión segura (SSL) en el puerto 443 para gRPC externo
        credenciales = grpc.ssl_channel_credentials()
        canal = grpc.secure_channel(f"{URL_RENDER}:443", credenciales)
        st.session_state.stub = batalla_pb2_grpc.MotorMultijugadorStub(canal)
        st.session_state.mi_id = None
        st.session_state.mis_barcos = []
    except Exception as e:
        st.error(f"Error de conexión inicial: {e}")

stub = st.session_state.stub

# --- LÓGICA DE REGISTRO ---
if st.session_state.mi_id is None:
    st.subheader("¡Bienvenido a la Flota!")
    if st.button("Unirse a la Partida"):
        try:
            max_jugadores = stub.ObtenerMaxJugadores(batalla_pb2.Vacio()).valor
            if max_jugadores == 0:
                max_jugadores = 2 # Valor por defecto si eres el primero
            
            res = stub.RegistrarJugador(batalla_pb2.PeticionRegistro(total_esperados=max_jugadores))
            st.session_state.mi_id = res.id_jugador
            st.success(f"Te has unido como Jugador {st.session_state.mi_id}")
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo conectar al servidor: {e}")
else:
    # --- PANEL DE CONTROL ---
    st.sidebar.title(f"🎮 Jugador {st.session_state.mi_id}")
    
    # Consultar estado del servidor
    todos_listos = stub.TodosListos(batalla_pb2.Vacio()).valor
    turno_actual = stub.DeQuienEsElTurno(batalla_pb2.Vacio()).valor
    tablero = stub.ObtenerEstadoTablero(batalla_pb2.Vacio())
    ganador = stub.ObtenerGanador(batalla_pb2.Vacio()).valor

    if ganador > 0:
        st.balloons()
        st.header(f"🏆 ¡EL JUGADOR {ganador} HA GANADO!")
        st.text(stub.ObtenerMarcador(batalla_pb2.Vacio()).texto)
        if st.button("Salir"): st.session_state.mi_id = None; st.rerun()
    
    elif not todos_listos:
        st.warning("Fase de Posicionamiento: Coloca tus 10 barcos en el tablero de la izquierda.")
        if len(st.session_state.mis_barcos) >= 10:
            if st.button("Confirmar Flota y Declarar Listo"):
                stub.DeclararListo(batalla_pb2.PeticionJugador(id_jugador=st.session_state.mi_id))
                st.rerun()
    else:
        if turno_actual == st.session_state.mi_id:
            st.info("🎯 ¡ES TU TURNO! Ataca en el panel derecho.")
        else:
            st.write(f"Esperando al Jugador {turno_actual}...")

    # --- DIBUJAR TABLEROS ---
    col1, col2 = st.columns(2)
    tamano = len(tablero.filas)

    with col1:
        st.subheader("Tu Flota (Defensa)")
        for i in range(tamano):
            cols = st.columns(tamano)
            for j in range(tamano):
                valor = tablero.filas[i].valores[j]
                # Lógica de colores según el estado
                if (i, j) in st.session_state.mis_barcos:
                    label = "🚢"
                    if valor > 0 and str(st.session_state.mi_id) in str(valor): label = "💥"
                else:
                    label = "🌊"
                    if valor == -1: label = "💨"
                
                if cols[j].button(label, key=f"def_{i}_{j}"):
                    if not todos_listos and len(st.session_state.mis_barcos) < 10:
                        if (i, j) not in st.session_state.mis_barcos:
                            stub.ColocarBarco(batalla_pb2.PeticionCoordenada(id_jugador=st.session_state.mi_id, x=i, y=j))
                            st.session_state.mis_barcos.append((i, j))
                            st.rerun()

    with col2:
        st.subheader("Radar de Ataque")
        for i in range(tamano):
            cols = st.columns(tamano)
            for j in range(tamano):
                valor = tablero.filas[i].valores[j]
                label = "❓"
                if valor == -1: label = "💨"
                elif valor > 0: label = f"🔥J{valor}"
                
                if cols[j].button(label, key=f"atk_{i}_{j}", disabled=(not todos_listos or turno_actual != st.session_state.mi_id)):
                    res_tiro = stub.Disparar(batalla_pb2.PeticionCoordenada(id_jugador=st.session_state.mi_id, x=i, y=j)).valor
                    if res_tiro == 8: st.warning("Tiro inválido")
                    st.rerun()

    if st.button("🔄 Actualizar"): st.rerun()
