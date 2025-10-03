# --- IMPORTS ---
# os: Proporciona funciones para interactuar con el sistema operativo. Se usa aquí para
#     obtener el puerto desde las variables de entorno
# Flask, render_template: Flask es el micro-framework web sobre el que se construye la aplicación.
#                         render_template se usa para cargar y enviar el archivo index.html al navegador.
# SocketIO: La librería principal que extiende Flask para permitir comunicación bidireccional
#           y en tiempo real (WebSockets) entre el servidor y el cliente.
# Planificador: Importa tu clase Planificador desde el archivo logic.py. Este es el "cerebro"
#               de la simulación.
# eventlet: Es una librería de red concurrente. Se necesita para que SocketIO pueda manejar
#           múltiples clientes de manera eficiente sin bloquearse. 
import os
from flask import Flask, render_template
from flask_socketio import SocketIO
from logic import Planificador
import eventlet

# --- CONFIGURACIÓN INICIAL ---
# Se crea la instancia principal de la aplicación Flask.
app = Flask(__name__)
# Se inicializa SocketIO, vinculándolo con la aplicación Flask para que trabajen juntos.
socketio = SocketIO(app)

# --- FUNCIONES CALLBACK ---
# Estas funciones actúan como un "puente" desde la lógica interna (logic.py) hacia el exterior (frontend).
# Se pasarán al Planificador para que este pueda notificar al frontend cuando algo suceda.

def actualizar_frontend(proceso_data):
    """
    Callback que se invoca desde el Planificador cada vez que el estado de un proceso cambia.
    Emite un evento 'update_process' a TODOS los clientes conectados, enviando los datos
    actualizados del proceso.
    """
    socketio.emit('update_process', proceso_data)

def finalizar_frontend(proceso_data):
    """
    Callback que se invoca cuando un proceso ha finalizado su ciclo de vida.
    Emite un evento 'finalize_process' para notificar al frontend que el proceso terminó.
    """
    socketio.emit('finalize_process', proceso_data)

# --- INSTANCIA DEL PLANIFICADOR ---
# Se crea una única instancia global del Planificador. Este será el "cerebro" central
# que gestionará todos los procesos durante toda la vida del servidor.
# Se le pasan las funciones callback y el objeto socketio para que pueda comunicarse.
mi_planificador = Planificador(actualizar_frontend, finalizar_frontend, socketio)

# --- RUTAS DE FLASK ---
# Define las URLs de la aplicación web.

@app.route('/')
def index():
    """
    Esta es la ruta principal. Cuando un usuario visita la URL raíz de la aplicación (ej. "http://localhost:5000/"),
    Flask ejecutará esta función, que renderiza y devuelve el archivo 'index.html'.
    """
    return render_template('index.html')

# --- MANEJADORES DE EVENTOS DE SOCKET.IO ---
# Estas funciones son los "oídos" del servidor. Se ejecutan en respuesta a eventos
# que son enviados desde el cliente (el archivo main.js en el navegador).

@socketio.on('connect')
def handle_connect():
    """
    Se activa automáticamente cuando un nuevo cliente (navegador) establece una conexión
    exitosa con el servidor.
    """
    print('¡Cliente conectado!')
    # Es importante enviar el estado completo de la simulación al nuevo cliente
    # para que su vista se sincronice con la de los demás.
    mi_planificador.enviar_estado_completo()

@socketio.on('add_process')
def handle_add_process():
    """
    Se activa cuando el cliente emite el evento 'add_process' (al hacer clic en el botón 'Agregar Proceso').
    Llama al método correspondiente en el planificador para crear un nuevo proceso.
    """
    mi_planificador.crear_proceso()

@socketio.on('start_process')
def handle_start_process(data):
    """
    Se activa cuando el cliente quiere iniciar un proceso específico.
    Recibe un diccionario 'data' que contiene el 'id' del proceso a iniciar.
    """
    pid = data.get('id')
    if pid: mi_planificador.iniciar_proceso(pid)

@socketio.on('block_process')
def handle_block_process(data):
    """
    Se activa para bloquear un proceso específico. Recibe el 'id' del proceso.
    """
    pid = data.get('id')
    if pid: mi_planificador.bloquear_proceso_por_id(pid)

@socketio.on('unblock_process')
def handle_unblock_process(data):
    """
    Se activa para desbloquear un proceso específico. Recibe el 'id' del proceso.
    """
    pid = data.get('id')
    if pid: mi_planificador.desbloquear_proceso_por_id(pid)

@socketio.on('stop_process')
def handle_stop_process(data):
    """
    Se activa para detener (terminar) un proceso específico. Recibe el 'id' del proceso.
    """
    pid = data.get('id')
    if pid: mi_planificador.detener_proceso_por_id(pid)

# --- MANEJADORES DE EVENTOS GLOBALES ---

@socketio.on('start_all')
def handle_start_all():
    """
    Se activa al presionar el botón 'Iniciar Todos'.
    Llama al método del planificador para iniciar todos los procesos que estén en estado 'Nuevo'.
    """
    mi_planificador.iniciar_todos()

@socketio.on('reset_all')
def handle_reset_all():
    """
    Se activa al presionar el botón 'Reiniciar Simulación'.
    Llama al método del planificador que detiene todos los procesos y limpia el estado de la simulación.
    """
    mi_planificador.reiniciar()

# --- PUNTO DE ENTRADA DE LA APLICACIÓN ---
# El bloque 'if __name__ == "__main__":' asegura que este código solo se ejecute
# cuando el script es corrido directamente (y no cuando es importado).
if __name__ == "__main__":
    # Inicia el servidor web. Se usa 'socketio.run' en lugar del 'app.run' de Flask
    # para asegurar que el servidor sea compatible con WebSockets y eventlet.
    # host="0.0.0.0" hace que el servidor sea accesible desde cualquier IP (necesario para producción).
    # port=... toma el puerto de una variable de entorno o usa 5000 por defecto.
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))