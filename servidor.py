import grpc
from concurrent import futures
import os
import sys
import batalla_pb2
import batalla_pb2_grpc

# Esto es vital para que Render no piense que el proceso está trabado
sys.stdout.reconfigure(line_buffering=True)

class MotorMultijugadorServicer(batalla_pb2_grpc.MotorMultijugadorServicer):
    def __init__(self):
        self.jugadores_conectados = 0
        self.max_jugadores = 0
        self.jugadores_listos = 0
        self.turno_actual = 1
        self.disparos_hechos_este_turno = 0
        self.matriz_disparos = []
        self.flotas = {} 
        self.vidas = {}
        self.puntajes = {}
        self.jugadores_vivos = 0

    def RegistrarJugador(self, request, context):
        if self.max_jugadores == 0:
            self.max_jugadores = request.total_esperados
            tamano_cuadricula = self.max_jugadores * 3 
            self.matriz_disparos = [[0 for _ in range(tamano_cuadricula)] for _ in range(tamano_cuadricula)]
        
        self.jugadores_conectados += 1
        id_jugador = self.jugadores_conectados
        self.flotas[id_jugador] = []
        self.vidas[id_jugador] = 10 
        self.puntajes[id_jugador] = 0
        self.jugadores_vivos += 1
        print(f"--- NUEVO JUGADOR: {id_jugador} ---")
        return batalla_pb2.RespuestaRegistro(id_jugador=id_jugador)

    def ObtenerCantidadConectados(self, request, context): 
        return batalla_pb2.RespuestaEntero(valor=self.jugadores_conectados)

    def ObtenerMaxJugadores(self, request, context): 
        return batalla_pb2.RespuestaEntero(valor=self.max_jugadores)
    
    def ColocarBarco(self, request, context):
        x, y, idJugador = request.x, request.y, request.id_jugador
        if (x, y) not in self.flotas[idJugador]:
            self.flotas[idJugador].append((x, y))
        return batalla_pb2.Vacio()

    def DeclararListo(self, request, context):
        self.jugadores_listos += 1
        return batalla_pb2.Vacio()

    def TodosListos(self, request, context):
        listos = self.jugadores_listos == self.max_jugadores and self.max_jugadores > 0
        return batalla_pb2.RespuestaBooleano(valor=listos)

    def DeQuienEsElTurno(self, request, context):
        return batalla_pb2.RespuestaEntero(valor=self.turno_actual)

    def Disparar(self, request, context):
        idJugador, x, y = request.id_jugador, request.x, request.y
        if idJugador != self.turno_actual or self.jugadores_vivos <= 1:
            return batalla_pb2.RespuestaEntero(valor=8) 

        impacto = False
        ids_impactados = ""
        for enemigo_id, barcos in self.flotas.items():
            if enemigo_id != idJugador and (x, y) in barcos:
                barcos.remove((x, y)) 
                self.vidas[enemigo_id] -= 1
                self.puntajes[idJugador] += 1
                impacto = True
                ids_impactados += str(enemigo_id) 
                if self.vidas[enemigo_id] == 0: self.jugadores_vivos -= 1

        if impacto:
            self.matriz_disparos[x][y] = int(ids_impactados)
            resultado = int(ids_impactados)
        else:
            if self.matriz_disparos[x][y] == 0: self.matriz_disparos[x][y] = -1 
            resultado = 0

        self.disparos_hechos_este_turno += 1
        if self.disparos_hechos_este_turno >= (self.max_jugadores - 1):
            self.disparos_hechos_este_turno = 0
            self.turno_actual = (self.turno_actual % self.max_jugadores) + 1
        return batalla_pb2.RespuestaEntero(valor=resultado)

    def ObtenerEstadoTablero(self, request, context): 
        filas_proto = [batalla_pb2.Fila(valores=f) for f in self.matriz_disparos]
        return batalla_pb2.RespuestaTablero(filas=filas_proto)

    def ObtenerGanador(self, request, context):
        ganador = 0
        if self.jugadores_vivos <= 1 and self.max_jugadores > 0:
            for id_j, v in self.vidas.items():
                if v > 0: ganador = id_j
        return batalla_pb2.RespuestaEntero(valor=ganador)

    def ObtenerMarcador(self, request, context):
        texto = "=== MARCADOR FINAL ===\n"
        for i in range(1, self.max_jugadores + 1):
            texto += f"Jugador {i}: {self.puntajes[i]} puntos\n"
        return batalla_pb2.RespuestaMarcador(texto=texto)

def serve():
    # Render asigna el puerto en la variable PORT
    port = os.environ.get('PORT', '10000')
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    batalla_pb2_grpc.add_MotorMultijugadorServicer_to_server(MotorMultijugadorServicer(), server)
    
    # El host [::] es obligatorio para que Render acepte conexiones de internet
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"--- SERVIDOR CORRIENDO EN PUERTO: {port} ---")
    sys.stdout.flush() # Forzar la impresión en el log de Render
    
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
