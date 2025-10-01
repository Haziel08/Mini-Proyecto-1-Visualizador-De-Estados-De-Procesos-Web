import threading, time, random

# --- Estados ---
NUEVO = "Nuevo"
LISTO = "Listo"
EJECUCION = "En Ejecución"
BLOQUEADO = "Bloqueado"
FINALIZADO = "Finalizado"
DETENIDO = "Detenido"

class Proceso(threading.Thread):
    def __init__(self, id_proceso, planificador_callbacks, socketio):
        super().__init__()
        self.id = id_proceso
        self.estado = NUEVO
        self.tiempo_total = random.randint(8, 15)
        self.tiempo_ejecutado = 0
        self.callbacks = planificador_callbacks
        self.socketio = socketio
        self.bloqueado = False
        self.detener = False
        self.execution_start_time = None
        self.last_execution_time_ms = 0
        self.history = [(time.time(), self.estado)]
    
    def to_dict(self):
        """Convierte los datos del proceso a un formato enviable (JSON)."""
        return {
            'id': self.id,
            'estado': self.estado,
            'tiempo_total': self.tiempo_total,
            'tiempo_ejecutado': self.tiempo_ejecutado,
            'last_execution_time_ms': self.last_execution_time_ms,
            'history': self.history
        }

    def _set_estado(self, nuevo_estado):
        if self.estado == nuevo_estado and self.estado != EJECUCION:
            return
        timestamp = time.time()
        if self.estado == EJECUCION and self.execution_start_time:
            duration = timestamp - self.execution_start_time
            self.last_execution_time_ms = duration * 1000
        if nuevo_estado == EJECUCION:
            self.execution_start_time = timestamp
        self.estado = nuevo_estado
        self.history.append((timestamp, self.estado))
        self._notificar()

    def run(self):
        self._set_estado(LISTO)
        self.socketio.sleep(random.uniform(0.5, 1.5))
        while self.tiempo_ejecutado < self.tiempo_total and not self.detener:
            if self.bloqueado:
                self._set_estado(BLOQUEADO)
                self.socketio.sleep(random.uniform(1, 2))
                if not self.detener: self._set_estado(LISTO)
                continue
            self._set_estado(EJECUCION)
            quantum = random.uniform(0.8, 1.2)
            self.socketio.sleep(quantum)
            self.tiempo_ejecutado += quantum
            if self.tiempo_ejecutado < self.tiempo_total and not self.detener:
                self._set_estado(LISTO)
                self.socketio.sleep(random.uniform(0.2, 0.5))
        
        final_state = FINALIZADO if not self.detener else DETENIDO
        if not self.detener:
            self.tiempo_ejecutado = self.tiempo_total
        self._set_estado(final_state)
        
        if self.callbacks['finalizar']:
            self.callbacks['finalizar'](self.to_dict())

    def _notificar(self):
        if self.callbacks['actualizar']:
            self.callbacks['actualizar'](self.to_dict())

    def bloquear(self): self.bloqueado = True
    def desbloquear(self): self.bloqueado = False
    def terminar(self): self.detener = True

class Planificador:
    def __init__(self, callback_actualizacion, callback_finalizado, socketio):
        self.procesos = {}
        self.callbacks = {'actualizar': callback_actualizacion, 'finalizar': callback_finalizado}
        self.socketio = socketio
        self.contador_id = 0
        self.lock = threading.Lock()

    def crear_proceso(self):
        with self.lock:
            self.contador_id += 1
            p = Proceso(self.contador_id, self.callbacks, self.socketio)
            self.procesos[self.contador_id] = p
            p._notificar() # Notifica su creación
            return p

    def iniciar_proceso(self, id_proceso):
        with self.lock:
            p = self.procesos.get(id_proceso)
            if p and not p.is_alive():
                self.socketio.start_background_task(target=p.run)

    def enviar_estado_completo(self):
        with self.lock:
            for p in self.procesos.values():
                p._notificar()

    def bloquear_proceso_por_id(self, id_proceso):
        with self.lock:
            p = self.procesos.get(id_proceso)
            if p: p.bloquear()

    def desbloquear_proceso_por_id(self, id_proceso):
        with self.lock:
            p = self.procesos.get(id_proceso)
            if p: p.desbloquear()

    def detener_proceso_por_id(self, id_proceso):
        with self.lock:
            p = self.procesos.get(id_proceso)
            if p: p.terminar()

    def iniciar_todos(self):
        with self.lock:
            for p in self.procesos.values():
                if not p.is_alive() and p.estado == NUEVO:
                    self.socketio.start_background_task(target=p.run)

    def bloquear_todos_activos(self):
        with self.lock:
            for p in self.procesos.values():
                if p.is_alive() and not p.bloqueado and p.estado not in (FINALIZADO, DETENIDO, BLOQUEADO):
                    p.bloquear()

    def desbloquear_todos_bloqueados(self):
        with self.lock:
            for p in self.procesos.values():
                if p.bloqueado:
                    p.desbloquear()

    def detener_todos_activos(self):
        with self.lock:
            for p in self.procesos.values():
                if p.is_alive() and p.estado not in (FINALIZADO, DETENIDO):
                    p.terminar()
