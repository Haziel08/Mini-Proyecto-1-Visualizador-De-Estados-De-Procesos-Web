# --- IMPORTS ---
# threading: Permite crear y gestionar hilos. Cada proceso se ejecutará en su propio hilo
#            para simular la concurrencia real de un sistema operativo.
# time: Se usa para obtener marcas de tiempo (timestamps) y registrar cuándo ocurren los cambios de estado.
# random: Se utiliza para generar duraciones aleatorias para los procesos
import threading
import time
import random

# --- DEFINICIÓN DE ESTADOS ---
# Se definen constantes para los nombres de los estados de un proceso.
# Usar constantes en lugar de cadenas de texto directas ("Nuevo", "Listo", etc.)
NUEVO, LISTO, EJECUCION, BLOQUEADO, FINALIZADO, DETENIDO = "Nuevo", "Listo", "En Ejecución", "Bloqueado", "Finalizado", "Detenido"

# --- CLASE Proceso ---
# Representa un único proceso en la simulación. Hereda de 'threading.Thread',
# lo que significa que cada instancia de esta clase es un hilo que puede ejecutarse
# de forma independiente y concurrente.
class Proceso(threading.Thread):
    # El método constructor, se llama al crear una nueva instancia de Proceso.
    def __init__(self, id_proceso, planificador_callbacks, socketio):
        super().__init__()  # Llama al constructor de la clase padre (threading.Thread).
        
        # --- ATRIBUTOS DEL PROCESO ---
        self.id = id_proceso  # Identificador numérico único para el proceso.
        self.estado = NUEVO   # El estado inicial de todo proceso es 'Nuevo'.
        # El tiempo total que el proceso necesita en CPU para completarse. Se elige un valor aleatorio.
        self.tiempo_total = random.randint(8, 15)
        self.tiempo_ejecutado = 0  # Contador que acumula el tiempo que el proceso ha estado en 'Ejecución'.
        
        # 'Callbacks' son funciones que el proceso puede "llamar de vuelta" para notificar al exterior.
        # Esto permite que la lógica del proceso (aquí) se comunique con el servidor (app.py).
        self.callbacks = planificador_callbacks
        
        # Se guarda una referencia al objeto socketio para usar su función 'sleep',
        # que es compatible con eventlet y no bloquea todo el servidor.
        self.socketio = socketio
        
        # Banderas (flags) para controlar el flujo de ejecución desde el exterior.
        self.bloqueado = False  # Si es True, el proceso entrará en estado 'Bloqueado'.
        self.detener = False    # Si es True, el proceso terminará su ejecución prematuramente.

        # Atributos para medir el tiempo de ráfaga de CPU.
        self.execution_start_time = None  # Guarda el momento en que el proceso entra en 'Ejecución'.
        self.last_execution_time_ms = 0   # Guarda la duración de la última ráfaga de CPU en milisegundos.
        
        # Un historial de todos los estados por los que ha pasado el proceso, con su timestamp.
        # Es crucial para poder dibujar la gráfica de Gantt en el frontend.
        self.history = [(time.time(), self.estado)]

    # Convierte los atributos importantes del proceso a un diccionario.
    # Esto es útil para serializar el objeto y enviarlo como JSON al frontend.
    def to_dict(self):
        return {
            'id': self.id, 'estado': self.estado, 'tiempo_total': self.tiempo_total,
            'tiempo_ejecutado': self.tiempo_ejecutado, 'last_execution_time_ms': self.last_execution_time_ms,
            'history': self.history
        }

    # Método centralizado para cambiar el estado de un proceso.
    def _set_estado(self, nuevo_estado):
        # Si el nuevo estado es el mismo que el actual, no hace nada para evitar notificaciones innecesarias.
        if self.estado == nuevo_estado:
            return
        
        timestamp = time.time()  # Obtiene la marca de tiempo actual.
        
        # Si el proceso estaba en 'Ejecución', calcula cuánto tiempo duró esa ráfaga.
        if self.estado == EJECUCION and self.execution_start_time:
            self.last_execution_time_ms = (timestamp - self.execution_start_time) * 1000
        
        # Si el nuevo estado es 'Ejecución', registra el tiempo de inicio de la ráfaga.
        if nuevo_estado == EJECUCION:
            self.execution_start_time = timestamp
            
        self.estado = nuevo_estado  # Actualiza el estado.
        self.history.append((timestamp, self.estado))  # Añade el nuevo estado y su timestamp al historial.
        self._notificar()  # Notifica al frontend sobre el cambio.

    # Este es el corazón del proceso, el método que se ejecuta cuando el hilo comienza.
    # Define el ciclo de vida completo del proceso.
    def run(self):
        # El proceso pasa de 'Nuevo' a 'Listo' para entrar en la cola de planificación.
        self._set_estado(LISTO)
        self.socketio.sleep(random.uniform(0.5, 1.5)) # Simula un tiempo de espera antes de empezar.

        # Bucle principal: se ejecuta mientras el proceso no haya completado su tiempo total y no haya sido detenido.
        while self.tiempo_ejecutado < self.tiempo_total and not self.detener:
            
            # --- MANEJO DEL ESTADO BLOQUEADO ---
            if self.bloqueado:
                self._set_estado(BLOQUEADO)
                # Bucle interno: el proceso se queda aquí mientras la bandera 'bloqueado' sea True.
                while self.bloqueado and not self.detener:
                    self.socketio.sleep(0.1) # Pausa no bloqueante.
                
                # Si el proceso no fue detenido mientras estaba bloqueado, vuelve a 'Listo'.
                if not self.detener:
                    self._set_estado(LISTO)
                continue # Vuelve al inicio del bucle principal.

            # --- SIMULACIÓN DE EJECUCIÓN EN CPU ---
            self._set_estado(EJECUCION)
            # Un 'quantum' es una pequeña porción de tiempo que se le asigna a un proceso en la CPU.
            quantum = random.uniform(0.8, 1.2)
            
            quantum_start_time = time.time()
            # Bucle para simular el trabajo durante el quantum.
            while time.time() - quantum_start_time < quantum:
                # Si durante el quantum el proceso es detenido o bloqueado, se interrumpe la ráfaga.
                if self.detener or self.bloqueado:
                    break
                # Pausa muy corta para hacer el bucle no bloqueante y permitir interrupciones.
                self.socketio.sleep(0.05)
            
            # Acumula el tiempo que realmente se ejecutó en el contador.
            time_spent_in_quantum = time.time() - quantum_start_time
            self.tiempo_ejecutado += time_spent_in_quantum

            # Si el quantum fue interrumpido, vuelve al inicio del bucle principal para re-evaluar el estado.
            if self.detener or self.bloqueado:
                continue

            # Si después del quantum aún le queda trabajo por hacer, vuelve al estado 'Listo'.
            if self.tiempo_ejecutado < self.tiempo_total and not self.detener:
                self._set_estado(LISTO)
                # Espera un corto tiempo simulando que está en la cola de listos.
                self.socketio.sleep(random.uniform(0.2, 0.5))

        # --- FINALIZACIÓN DEL PROCESO ---
        # Determina el estado final basado en si el proceso terminó su trabajo o fue detenido.
        final_state = FINALIZADO if not self.detener else DETENIDO
        # Asegura que la barra de progreso llegue al 100% si finalizó normalmente.
        if not self.detener:
            self.tiempo_ejecutado = self.tiempo_total
        self._set_estado(final_state) # Establece y notifica el estado final.
        
        # Llama al callback 'finalizar' para que el planificador pueda realizar tareas de limpieza si es necesario.
        if self.callbacks['finalizar']:
            self.callbacks['finalizar'](self.to_dict())

    # Método ayudante para invocar el callback de actualización.
    def _notificar(self):
        if self.callbacks['actualizar']:
            self.callbacks['actualizar'](self.to_dict())

    # --- MÉTODOS PÚBLICOS DE CONTROL ---
    # Estos métodos son llamados por el Planificador para cambiar las banderas y controlar el proceso.
    def bloquear(self):
        self.bloqueado = True

    def desbloquear(self):
        self.bloqueado = False

    def terminar(self):
        self.detener = True


# --- CLASE Planificador ---
# Es el "cerebro" o "gestor" de la simulación. Se encarga de crear,
# administrar y controlar todos los objetos de tipo Proceso.
class Planificador:
    def __init__(self, callback_actualizacion, callback_finalizado, socketio):
        # Un diccionario para almacenar todas las instancias de procesos, usando su ID como clave.
        self.procesos = {}
        # Almacena las funciones callback pasadas desde app.py para comunicarse con el frontend.
        self.callbacks = {'actualizar': callback_actualizacion, 'finalizar': callback_finalizado}
        self.socketio = socketio
        self.contador_id = 0  # Un contador simple para generar IDs únicos.
        # Un 'Lock' (cerrojo) es un mecanismo para prevenir problemas de concurrencia.
        # Asegura que solo un hilo a la vez pueda modificar la lista de procesos.
        self.lock = threading.Lock()

    def crear_proceso(self):
        with self.lock: # 'with self.lock' adquiere el cerrojo y lo libera automáticamente al salir.
            self.contador_id += 1
            # Crea una nueva instancia de Proceso, pasándole su ID y los callbacks.
            p = Proceso(self.contador_id, self.callbacks, self.socketio)
            self.procesos[self.contador_id] = p # Lo guarda en el diccionario.
            p._notificar() # Notifica al frontend que se ha creado un nuevo proceso.
            return p

    def iniciar_proceso(self, id_proceso):
        with self.lock:
            p = self.procesos.get(id_proceso) # Busca el proceso por su ID.
            # Se asegura que el proceso exista y que no se haya iniciado ya (is_alive).
            if p and not p.is_alive():
                # Inicia el hilo del proceso en segundo plano de una manera compatible con SocketIO.
                self.socketio.start_background_task(target=p.run)

    # Envía el estado de todos los procesos al frontend. Útil cuando un nuevo cliente se conecta.
    def enviar_estado_completo(self):
        with self.lock:
            for p in self.procesos.values():
                p._notificar()

    # Los siguientes métodos son "pasamanos": reciben una orden con un ID,
    # buscan el proceso y le delegan la acción.
    def bloquear_proceso_por_id(self, id_proceso):
        with self.lock:
            p = self.procesos.get(id_proceso)
            if p:
                p.bloquear()

    def desbloquear_proceso_por_id(self, id_proceso):
        with self.lock:
            p = self.procesos.get(id_proceso)
            if p:
                p.desbloquear()

    def detener_proceso_por_id(self, id_proceso):
        with self.lock:
            p = self.procesos.get(id_proceso)
            if p:
                p.terminar()

    # Itera sobre todos los procesos e inicia aquellos que están en estado 'Nuevo'.
    def iniciar_todos(self):
        with self.lock:
            for p in self.procesos.values():
                if not p.is_alive() and p.estado == NUEVO:
                    self.socketio.start_background_task(target=p.run)
    
    # Detiene todos los procesos en ejecución, limpia la lista de procesos y reinicia los contadores.
    def reiniciar(self):
        with self.lock:
            # Pide a todos los hilos vivos que terminen.
            for p in self.procesos.values():
                if p.is_alive():
                    p.terminar()
            self.procesos.clear()  # Vacía el diccionario de procesos.
            self.contador_id = 0   # Reinicia el contador de IDs.
            # Emite un evento especial al frontend para que también limpie su interfaz.
            self.socketio.emit('reset_ui')