document.addEventListener('DOMContentLoaded', () => {
    // Conexión al servidor mediante Socket.IO
    const socket = io();

    // --- Referencias a elementos del DOM ---
    const processContainer = document.getElementById('process-container');
    const addProcessBtn = document.getElementById('add-process-btn');
    const showChartBtn = document.getElementById('show-chart-btn');
    const chartModal = document.getElementById('chart-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const ganttChartCanvas = document.getElementById('gantt-chart');
    const chartLegend = document.getElementById('chart-legend');
    const resetBtn = document.getElementById('reset-btn');
    const startAllBtn = document.getElementById('start-all-btn');

    // --- Variables de control ---
    let allProcesses = {}; // Guarda todos los procesos activos
    const MAX_PROCESSES = 10; // Límite máximo de procesos simultáneos
    let chartUpdateInterval = null; // Intervalo para actualizar la gráfica Gantt

    // --- Crear o actualizar tarjeta de proceso ---
    const createOrUpdateProcessCard = (process) => {
        // Buscar si ya existe la tarjeta del proceso
        let card = document.getElementById(`process-${process.id}`);
        if (!card) {
            // Si no existe, se crea la tarjeta con su estructura
            card = document.createElement('div');
            card.className = 'process-card';
            card.id = `process-${process.id}`;
            card.innerHTML = `
                <div class="card-header">
                    <span class="process-id">Proceso ${process.id}</span>
                    <div class="status-info">
                        <span class="cpu-time-label">T. CPU (ms): </span>
                        <span class="cpu-time">0 ms</span>
                        <span class="status-badge"></span>
                    </div>
                </div>
                <div class="card-footer">
                    <div class="progress-bar-container">
                        <div class="progress-bar"></div>
                    </div>
                    <span class="percentage">0%</span>
                    <div class="action-menu-container">
                        <button class="action-menu-btn">⋮</button>
                        <div class="action-menu">
                            <button class="start-btn">▶ Iniciar</button>
                            <button class="block-btn">⏸ Bloquear</button>
                            <button class="unblock-btn">▶ Desbloquear</button>
                            <button class="stop-btn">⏹ Detener</button>
                        </div>
                    </div>
                </div>
            `;
            processContainer.appendChild(card);

            // --- Menú de acciones (⋮) ---
            const menuBtn = card.querySelector('.action-menu-btn');
            const menu = card.querySelector('.action-menu');
            menuBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Evita que cierre el menú por clic global
                const isVisible = menu.style.display === 'block';

                // Ocultar todos los menús abiertos
                document.querySelectorAll('.action-menu').forEach(m => m.style.display = 'none');
                document.querySelectorAll('.process-card').forEach(c => c.classList.remove('is-active'));

                // Mostrar solo el menú del proceso seleccionado
                if (!isVisible) {
                    menu.style.display = 'block';
                    card.classList.add('is-active');
                }
            });

            // --- Botones de acción (emitir eventos al backend) ---
            card.querySelector('.start-btn').addEventListener('click', () => socket.emit('start_process', { id: process.id }));
            card.querySelector('.block-btn').addEventListener('click', () => socket.emit('block_process', { id: process.id }));
            card.querySelector('.unblock-btn').addEventListener('click', () => socket.emit('unblock_process', { id: process.id }));
            card.querySelector('.stop-btn').addEventListener('click', () => socket.emit('stop_process', { id: process.id }));
        }

        // --- Actualización de progreso del proceso ---
        const percentage = process.tiempo_total > 0 
            ? (process.tiempo_ejecutado / process.tiempo_total) * 100 
            : 0;
        const progressBar = card.querySelector('.progress-bar');

        // Estado y tiempos
        card.querySelector('.status-badge').textContent = process.estado;
        card.querySelector('.cpu-time').textContent = `${process.last_execution_time_ms.toFixed(0)} ms`;
        progressBar.style.width = `${Math.min(percentage, 100)}%`;
        card.querySelector('.percentage').textContent = `${Math.min(percentage, 100).toFixed(0)}%`;

        // Colores de la barra según estado
        progressBar.classList.remove('blocked', 'finalized');
        if (process.estado === 'Bloqueado') progressBar.classList.add('blocked');
        else if (process.estado === 'Finalizado' || process.estado === 'Detenido') progressBar.classList.add('finalized');

        // Desactivar botón "Iniciar" si ya no está en estado "Nuevo"
        const menu = card.querySelector('.action-menu');
        if (menu && process.estado !== 'Nuevo') {
            const startBtn = menu.querySelector('.start-btn');
            if(startBtn) startBtn.disabled = true;
        }
    };

    // --- Marcar un proceso como finalizado en la UI ---
    const finalizeProcessCard = (process) => {
        const card = document.getElementById(`process-${process.id}`);
        if (card) {
            card.classList.add('finalized');
            const menuBtn = card.querySelector('.action-menu-btn');
            if(menuBtn) menuBtn.disabled = true;
        }
    };

    // --- Eventos desde el servidor ---
    socket.on('update_process', (process) => {
        // Actualizar o crear tarjeta
        allProcesses[process.id] = process;
        createOrUpdateProcessCard(process);

        // Ocultar botón "Agregar" si ya se alcanzó el límite
        const numProcesses = Object.keys(allProcesses).length;
        if (numProcesses >= MAX_PROCESSES) {
            addProcessBtn.style.display = 'none';
            resetBtn.style.display = 'inline-block';
        }
    });

    socket.on('finalize_process', (process) => {
        allProcesses[process.id] = process;
        finalizeProcessCard(process);
    });

    socket.on('reset_ui', () => {
        // Resetear todo el contenedor
        processContainer.innerHTML = '';
        allProcesses = {};
        addProcessBtn.style.display = 'inline-block';
        resetBtn.style.display = 'none';
    });

    // --- Botones globales ---
    addProcessBtn.addEventListener('click', () => socket.emit('add_process'));
    resetBtn.addEventListener('click', () => socket.emit('reset_all'));
    startAllBtn.addEventListener('click', () => socket.emit('start_all'));

    // Cerrar menús al hacer clic fuera
    document.addEventListener('click', () => {
        document.querySelectorAll('.action-menu').forEach(m => m.style.display = 'none');
        document.querySelectorAll('.process-card').forEach(c => c.classList.remove('is-active'));
    });

    // --- Mostrar ventana con gráfica Gantt ---
    showChartBtn.addEventListener('click', () => {
        chartModal.style.display = 'flex';
        if (chartUpdateInterval) clearInterval(chartUpdateInterval);
        chartUpdateInterval = setInterval(drawGanttChart, 1000); // Actualizar cada segundo
        drawGanttChart();
    });

    // --- Cerrar ventana de gráfica ---
    const closeModal = () => {
        chartModal.style.display = 'none';
        clearInterval(chartUpdateInterval);
        chartUpdateInterval = null;
    };
    closeModalBtn.addEventListener('click', closeModal);
    chartModal.addEventListener('click', (e) => {
        if (e.target === chartModal) closeModal(); // Clic fuera del contenido cierra modal
    });

    // --- Dibujar gráfica de Gantt ---
    function drawGanttChart() {
        const ctx = ganttChartCanvas.getContext('2d');
        const processes = Object.values(allProcesses);

        // Ajustar tamaño del canvas dinámicamente
        const container = ganttChartCanvas.parentElement;
        ganttChartCanvas.width = container.clientWidth;
        ganttChartCanvas.height = container.clientHeight - 50;
        ctx.clearRect(0, 0, ganttChartCanvas.width, ganttChartCanvas.height);

        // Mensaje si no hay datos para graficar
        if (processes.length === 0 || !processes.some(p => p.history.length > 1)) {
            ctx.fillStyle = '#666';
            ctx.font = '16px Poppins';
            ctx.textAlign = 'center';
            ctx.fillText('Inicie al menos un proceso para ver la gráfica.', ganttChartCanvas.width / 2, ganttChartCanvas.height / 2);
            return;
        }

        // Parámetros de la gráfica
        const PADDING_Y = 30;
        const ROW_HEIGHT = 40;
        const PADDING_X = 100;

        // Tiempo inicial y final para escalar la gráfica
        const startTime = Math.min(...processes.filter(p => p.history.length > 0).map(p => p.history[0][0]));
        const allFinished = processes.every(p => ['Finalizado', 'Detenido'].includes(p.estado));
        const endTime = allFinished 
            ? Math.max(...processes.filter(p => p.history.length > 0).map(p => p.history[p.history.length - 1][0]))
            : Date.now() / 1000;

        let totalDuration = endTime - startTime;
        if (totalDuration < 10) totalDuration = 10; // Mínimo de escala

        const pixelsPerSecond = (ganttChartCanvas.width - PADDING_X - 20) / totalDuration;

        // Dibujar etiquetas de procesos
        processes.forEach((proc, i) => {
            const yBase = PADDING_Y + i * ROW_HEIGHT;
            ctx.fillStyle = '#333';
            ctx.font = 'bold 12px Poppins';
            ctx.textAlign = 'right';
            ctx.fillText(`Proceso ${proc.id}`, PADDING_X - 10, yBase + ROW_HEIGHT / 2 + 4);
        });

        // Dibujar marcas de tiempo (ticks)
        const tickInterval = totalDuration <= 30 ? 2 : totalDuration <= 120 ? 10 : 30;
        for (let t = 0; t <= totalDuration; t += tickInterval) {
            const x = PADDING_X + t * pixelsPerSecond;
            ctx.strokeStyle = '#ccc';
            ctx.beginPath();
            ctx.moveTo(x, PADDING_Y - 10);
            ctx.lineTo(x, PADDING_Y + processes.length * ROW_HEIGHT);
            ctx.stroke();

            ctx.fillStyle = '#666';
            ctx.font = '10px Poppins';
            ctx.textAlign = 'center';
            ctx.fillText(`${t}s`, x, PADDING_Y - 15);
        }

        // Dibujar historial de estados de cada proceso
        processes.forEach((proc, i) => {
            const yBase = PADDING_Y + i * ROW_HEIGHT;
            for (let j = 0; j < proc.history.length; j++) {
                const [ts, state] = proc.history[j];
                const startX = PADDING_X + (ts - startTime) * pixelsPerSecond;
                const endTs = (j + 1 < proc.history.length) ? proc.history[j + 1][0] : endTime;
                const endX = PADDING_X + (endTs - startTime) * pixelsPerSecond;

                switch (state) {
                    case 'En Ejecución':
                        ctx.fillStyle = '#00F260'; // Verde
                        ctx.fillRect(startX, yBase + 5, endX - startX, ROW_HEIGHT - 10);
                        break;
                    case 'Bloqueado':
                        ctx.fillStyle = '#FF512F'; // Rojo
                        ctx.fillRect(startX, yBase + 12, endX - startX, ROW_HEIGHT - 24);
                        break;
                    case 'Listo':
                        ctx.strokeStyle = '#888'; // Gris
                        ctx.lineWidth = 3;
                        ctx.setLineDash([3, 3]); // Línea punteada
                        ctx.beginPath();
                        ctx.moveTo(startX, yBase + ROW_HEIGHT / 2);
                        ctx.lineTo(endX, yBase + ROW_HEIGHT / 2);
                        ctx.stroke();
                        ctx.setLineDash([]);
                        break;
                }
            }
        });

        // Leyenda de colores
        chartLegend.innerHTML = `
            <div class="legend-item"><div class="legend-color" style="background: #00F260;"></div> En Ejecución</div>
            <div class="legend-item"><div class="legend-color" style="background: #FF512F; height: 6px; margin-top: 2px;"></div> Bloqueado</div>
            <div class="legend-item"><div class="legend-color" style="background: #888; height: 3px; margin-top: 4px; border-top: 3px dotted #888;"></div> Listo</div>
        `;
    }
});
