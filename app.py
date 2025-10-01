from flask import Flask, render_template
from flask_socketio import SocketIO
from logic import Planificador
import eventlet

app = Flask(__name__)
socketio = SocketIO(app)

def actualizar_frontend(proceso_data):
    socketio.emit('update_process', proceso_data)

def finalizar_frontend(proceso_data):
    socketio.emit('finalize_process', proceso_data)

mi_planificador = Planificador(actualizar_frontend, finalizar_frontend, socketio)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('¡Cliente conectado!')
    mi_planificador.enviar_estado_completo()

@socketio.on('add_process')
def handle_add_process():
    mi_planificador.crear_proceso()

@socketio.on('start_process')
def handle_start_process(data):
    pid = data.get('id')
    if pid: mi_planificador.iniciar_proceso(pid)

@socketio.on('block_process')
def handle_block_process(data):
    pid = data.get('id')
    if pid: mi_planificador.bloquear_proceso_por_id(pid)

@socketio.on('unblock_process')
def handle_unblock_process(data):
    pid = data.get('id')
    if pid: mi_planificador.desbloquear_proceso_por_id(pid)

@socketio.on('stop_process')
def handle_stop_process(data):
    pid = data.get('id')
    if pid: mi_planificador.detener_proceso_por_id(pid)

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

# --- CORRECCIÓN: Añadido el manejador para el evento de reinicio ---
@socketio.on('reset_all')
def handle_reset_all():
    mi_planificador.reiniciar()

if __name__ == '__main__':
    print("Iniciando servidor en http://127.0.0.1:5000")
    socketio.run(app, host='127.0.0.1', port=5000)

