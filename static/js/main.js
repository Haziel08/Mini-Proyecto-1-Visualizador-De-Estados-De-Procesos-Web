document.addEventListener('DOMContentLoaded', () => {
    // Conexión correcta a SocketIO para producción
    const socket = io();

    const processContainer = document.getElementById('process-container');
    const addProcessBtn = document.getElementById('add-process-btn');
    const showChartBtn = document.getElementById('show-chart-btn');
    const chartModal = document.getElementById('chart-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const ganttChartCanvas = document.getElementById('gantt-chart');
    const chartLegend = document.getElementById('chart-legend');
    const resetBtn = document.getElementById('reset-btn');
    const startAllBtn = document.getElementById('start-all-btn');

    let allProcesses = {};
    const MAX_PROCESSES = 10;
    let chartUpdateInterval = null;

    // --- Función para crear o actualizar tarjeta de proceso ---
    const createOrUpdateProcessCard = (process) => {
        let card = document.getElementById(`process-${process.id}`);
        if (!card) {
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

            // Abrir/cerrar menú de acciones
            const menuBtn = card.querySelector('.action-menu-btn');
            const menu = card.querySelector('.action-menu');
            menuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const isVisible = menu.style.display === 'block';
                document.querySelectorAll('.action-menu').forEach(m => m.style.display = 'none');
                document.querySelectorAll('.process-card').forEach(c => c.classList.remove('is-active'));
                if (!isVisible) {
                    menu.style.display = 'block';
                    card.classList.add('is-active');
                }
            });

            // Botones de acción por proceso
            card.querySelector('.start-btn').addEventListener('click', () => socket.emit('start_process', { id: process.id }));
            card.querySelector('.block-btn').addEventListener('click', () => socket.emit('block_process', { id: process.id }));
            card.querySelector('.unblock-btn').addEventListener('click', () => socket.emit('unblock_process', { id: process.id }));
            card.querySelector('.stop-btn').addEventListener('click', () => socket.emit('stop_process', { id: process.id }));
        }

        const percentage = process.tiempo_total > 0 ? (process.tiempo_ejecutado / process.tiempo_total) * 100 : 0;
        const progressBar = card.querySelector('.progress-bar');
        
        card.querySelector('.status-badge').textContent = process.estado;
        card.querySelector('.cpu-time').textContent = `${process.last_execution_time_ms.toFixed(0)} ms`;
        progressBar.style.width = `${Math.min(percentage, 100)}%`;
        card.querySelector('.percentage').textContent = `${Math.min(percentage, 100).toFixed(0)}%`;

        progressBar.classList.remove('blocked', 'finalized');
        if (process.estado === 'Bloqueado') progressBar.classList.add('blocked');
        else if (process.estado === 'Finalizado' || process.estado === 'Detenido') progressBar.classList.add('finalized');

        const menu = card.querySelector('.action-menu');
        if (menu && process.estado !== 'Nuevo') {
            const startBtn = menu.querySelector('.start-btn');
            if(startBtn) startBtn.disabled = true;
        }
    };

    const finalizeProcessCard = (process) => {
        const card = document.getElementById(`process-${process.id}`);
        if (card) {
            card.classList.add('finalized');
            const menuBtn = card.querySelector('.action-menu-btn');
            if(menuBtn) menuBtn.disabled = true;
        }
    };

    // --- SocketIO listeners ---
    socket.on('update_process', (process) => {
        allProcesses[process.id] = process;
        createOrUpdateProcessCard(process);
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
        processContainer.innerHTML = '';
        allProcesses = {};
        addProcessBtn.style.display = 'inline-block';
        resetBtn.style.display = 'none';
    });

    // --- Event listeners botones ---
    addProcessBtn.addEventListener('click', () => socket.emit('add_process'));
    resetBtn.addEventListener('click', () => socket.emit('reset_all'));
    startAllBtn.addEventListener('click', () => socket.emit('start_all'));

    document.addEventListener('click', () => {
        document.querySelectorAll('.action-menu').forEach(m => m.style.display = 'none');
        document.querySelectorAll('.process-card').forEach(c => c.classList.remove('is-active'));
    });

    showChartBtn.addEventListener('click', () => {
        chartModal.style.display = 'flex';
        if (chartUpdateInterval) clearInterval(chartUpdateInterval);
        chartUpdateInterval = setInterval(drawGanttChart, 1000);
        drawGanttChart();
    });

    const closeModal = () => {
        chartModal.style.display = 'none';
        clearInterval(chartUpdateInterval);
        chartUpdateInterval = null;
    };

    closeModalBtn.addEventListener('click', closeModal);
    chartModal.addEventListener('click', (e) => {
        if (e.target === chartModal) closeModal();
    });

    // --- Función para dibujar Gantt ---
    function drawGanttChart() {
        const ctx = ganttChartCanvas.getContext('2d');
        const processes = Object.values(allProcesses);
        const container = ganttChartCanvas.parentElement;
        ganttChartCanvas.width = container.clientWidth;
        ganttChartCanvas.height = container.clientHeight - 50;
        ctx.clearRect(0, 0, ganttChartCanvas.width, ganttChartCanvas.height);

        if (processes.length === 0 || !processes.some(p => p.history.length > 1)) {
            ctx.fillStyle = '#666';
            ctx.font = '16px Poppins';
            ctx.textAlign = 'center';
            ctx.fillText('Inicie al menos un proceso para ver la gráfica.', ganttChartCanvas.width / 2, ganttChartCanvas.height / 2);
            return;
        }

        const PADDING_Y = 30;
        const ROW_HEIGHT = 40;
        const PADDING_X = 100;

        const startTime = Math.min(...processes.filter(p => p.history.length > 0).map(p => p.history[0][0]));
        const allFinished = processes.every(p => ['Finalizado', 'Detenido'].includes(p.estado));
        const endTime = allFinished 
            ? Math.max(...processes.filter(p => p.history.length > 0).map(p => p.history[p.history.length - 1][0]))
            : Date.now() / 1000;
        
        let totalDuration = endTime - startTime;
        if (totalDuration < 10) totalDuration = 10;

        const pixelsPerSecond = (ganttChartCanvas.width - PADDING_X - 20) / totalDuration;

        processes.forEach((proc, i) => {
            const yBase = PADDING_Y + i * ROW_HEIGHT;
            ctx.fillStyle = '#333';
            ctx.font = 'bold 12px Poppins';
            ctx.textAlign = 'right';
            ctx.fillText(`Proceso ${proc.id}`, PADDING_X - 10, yBase + ROW_HEIGHT / 2 + 4);
        });

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

        processes.forEach((proc, i) => {
            const yBase = PADDING_Y + i * ROW_HEIGHT;
            for (let j = 0; j < proc.history.length; j++) {
                const [ts, state] = proc.history[j];
                const startX = PADDING_X + (ts - startTime) * pixelsPerSecond;
                const endTs = (j + 1 < proc.history.length) ? proc.history[j + 1][0] : endTime;
                const endX = PADDING_X + (endTs - startTime) * pixelsPerSecond;
                
                                switch (state) {
                    case 'En Ejecución':
                        ctx.fillStyle = '#00F260';
                        ctx.fillRect(startX, yBase + 5, endX - startX, ROW_HEIGHT - 10);
                        break;
                    case 'Bloqueado':
                        ctx.fillStyle = '#FF512F';
                        ctx.fillRect(startX, yBase + 12, endX - startX, ROW_HEIGHT - 24);
                        break;
                    case 'Listo':
                        ctx.strokeStyle = '#888';
                        ctx.lineWidth = 3;
                        ctx.setLineDash([3, 3]);
                        ctx.beginPath();
                        ctx.moveTo(startX, yBase + ROW_HEIGHT / 2);
                        ctx.lineTo(endX, yBase + ROW_HEIGHT / 2);
                        ctx.stroke();
                        ctx.setLineDash([]);
                        break;
                }
            }
        });

        chartLegend.innerHTML = `
            <div class="legend-item"><div class="legend-color" style="background: #00F260;"></div> En Ejecución</div>
            <div class="legend-item"><div class="legend-color" style="background: #FF512F; height: 6px; margin-top: 2px;"></div> Bloqueado</div>
            <div class="legend-item"><div class="legend-color" style="background: #888; height: 3px; margin-top: 4px; border-top: 3px dotted #888;"></div> Listo</div>
        `;
    }
});

