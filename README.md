# Visualizador de Estados de Procesos Web


<p align="center">
  <img width="2000" height="600" alt="Docs Banner Overview del Proyecto Minimalista Azul (1)" src="https://github.com/user-attachments/assets/3e5a8940-2a3d-40fc-9648-ead00ea61ac4" />

</p>

<p align="center">
  <img src="https://img.shields.io/badge/estado-TERMINADO-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Última%20modificación-octubre%202025-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/JavaScript-yellow?style=for-the-badge&logo=javascript&logoColor=black" />
  <img src="https://img.shields.io/badge/Python-green?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/CSS-blue?style=for-the-badge&logo=css3&logoColor=white" />
  <img src="https://img.shields.io/badge/HTML-orange?style=for-the-badge&logo=html5&logoColor=white" />
  <img src="https://img.shields.io/badge/ Mini Proyecto 1-purple?style=for-the-badge" />
</p>


---

## Índice

- [Descripción del proyecto](#descripción-del-proyecto)  
- [Funcionalidades](#funcionalidades)  
- [Tecnologías utilizadas](#tecnologías-utilizadas)  
- [Requisitos y compatibilidad](#requisitos-y-compatibilidad)  
- [Estructura del proyecto](#estructura-del-proyecto)  
- [Ejecución](#ejecución)  
- [Autor](#autor)  

---

## Descripción del proyecto

Este proyecto implementa una plataforma web para simular y visualizar el estado de múltiples procesos en tiempo real. Permite crear, iniciar, bloquear, desbloquear y detener procesos individuales o en conjunto, además de mostrar un gráfico tipo Gantt que ilustra la ejecución de cada proceso a lo largo del tiempo. La interfaz incluye tarjetas interactivas con información sobre cada proceso, barras de progreso, tiempos de CPU y menús de acción.  

---

## Funcionalidades

- **Gestión de procesos**: Agregar hasta 10 procesos simultáneos. Cada proceso puede ser iniciado, bloqueado, desbloqueado o detenido individualmente.  
- **Controles globales**: Iniciar todos los procesos listos o reiniciar la simulación completa.  
- **Visualización en tiempo real**: Cada proceso tiene una tarjeta que muestra su estado, tiempo de CPU y porcentaje de ejecución. La barra de progreso cambia de color según el estado del proceso.  
- **Gráfica Gantt dinámica**: Permite visualizar la historia de cada proceso con colores diferenciados para estados “En Ejecución”, “Bloqueado” y “Listo”.  
- **Interfaz interactiva**: Menú de acciones desplegable para cada proceso, con controles rápidos y accesibles.  

---

## Tecnologías utilizadas

- HTML5 y CSS3  
- JavaScript  
- Python  
- Canvas API   

---

## Requisitos y compatibilidad
- Navegador   
- Conexión a Internet
  
---

## Estructura del proyecto
```
📦 raiz/
┣ 📂 static/
┃ ┣ 📂 css/
┃ ┃ ┗ 📄 style.css
┃ ┣ 📂 js/
┃ ┃ ┗ 📄 main.js
┣ 📂 templates/
┃ ┗ 📄 index.html
┣ 📄 app.py
┣ 📄 logic.py
┗ 📄 README.md
```

---

## Ejecución

1. Accede al proyecto en línea:  
[Visualizador de Procesos Web](https://mini-proyecto-1-visualizador-de-estados-rvrf.onrender.com)  
> Nota: Al estar en un host gratuito, la primera carga puede tardar unos segundos.

2. Uso de la aplicación:  
- El **botón verde** permite agregar procesos (máximo 10).  
- Cada proceso tiene un menú de **tres puntos** para iniciar, bloquear, desbloquear o detener.  
- **Iniciar todos** permite lanzar todos los procesos listos de manera simultánea.  
- **Gráfica Gantt**: se recomienda activarla al finalizar todos los procesos para una mejor visualización.

3. Para ver un video demostrativo de la aplicación:  
[Video de demostración](https://youtu.be/U_w-Yg7u1rM)  

---

## Autor

| [<img src="https://avatars.githubusercontent.com/u/75911106?v=4" width=115><br><sub>Haziel Ibares Sánchez</sub>](https://github.com/HazielSanchez) |
| :---: |
