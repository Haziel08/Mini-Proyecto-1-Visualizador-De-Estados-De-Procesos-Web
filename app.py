from flask import Flask, render_template
from flask_socketio import SocketIO
from logic import Planificador
import eventlet

# Inicia el servidor web y la conexión en tiempo real
app = Flask(__name__)
socketio = SocketIO(app)

# --- Funciones de Comunicación ---
# Estas funciones reemplazan los callbacks de Tkinter
def actualizar_frontend(proceso_data):
    """Envía los datos de un proceso actualizado a la página web."""
    socketio.emit('update_process', proceso_data)

def finalizar_frontend(proceso_data):
    """Notifica a la página web que un proceso ha finalizado."""
    socketio.emit('finalize_process', proceso_data)

# Crea la única instancia del planificador, pasándole las nuevas funciones
mi_planificador = Planificador(actualizar_frontend, finalizar_frontend, socketio)

# --- Rutas del Servidor ---
@app.route('/')
def index():
    """Sirve la página web principal (index.html)."""
    return render_template('index.html')

# --- Eventos de Socket.IO (Comunicación en Tiempo Real) ---
@socketio.on('connect')
def handle_connect():
    """Se ejecuta cuando un usuario abre la página web."""
    print('¡Cliente conectado!')
    # Envía el estado actual de todos los procesos al nuevo cliente
    mi_planificador.enviar_estado_completo()

@socketio.on('add_process')
def handle_add_process():
    """Responde a la solicitud del botón '+ Agregar Proceso'."""
    mi_planificador.crear_proceso()

@socketio.on('start_process')
def handle_start_process(data):
    """Responde a la solicitud de iniciar un proceso."""
    pid = data.get('id')
    if pid:
        mi_planificador.iniciar_proceso(pid)

@socketio.on('block_process')
def handle_block_process(data):
    """Responde a la solicitud de bloquear un proceso."""
    pid = data.get('id')
    if pid:
        mi_planificador.bloquear_proceso_por_id(pid)

@socketio.on('unblock_process')
def handle_unblock_process(data):
    """Responde a la solicitud de desbloquear un proceso."""
    pid = data.get('id')
    if pid:
        mi_planificador.desbloquear_proceso_por_id(pid)

@socketio.on('stop_process')
def handle_stop_process(data):
    """Responde a la solicitud de detener un proceso."""
    pid = data.get('id')
    if pid:
        mi_planificador.detener_proceso_por_id(pid)

# --- Eventos para Controles Globales ---
@socketio.on('start_all')
def handle_start_all():
    mi_planificador.iniciar_todos()

@socketio.on('block_all')
def handle_block_all():
    mi_planificador.bloquear_todos_activos()

@socketio.on('unblock_all')
def handle_unblock_all():
    mi_planificador.desbloquear_todos_bloqueados()

@socketio.on('stop_all')
def handle_stop_all():
    mi_planificador.detener_todos_activos()


if __name__ == '__main__':
    print("Iniciando servidor en http://127.0.0.1:5000")
    # Usa eventlet para un rendimiento óptimo con hilos
    socketio.run(app, host='127.0.0.1', port=5000)
