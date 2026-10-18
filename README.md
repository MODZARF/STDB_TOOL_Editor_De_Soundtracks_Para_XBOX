# STDB_TOOL

> Herramienta de Python con interfaz gráfica para crear y administrar listas de reproducción de la Xbox Clásica.

Proyecto **Open Source** desarrollado con asistencia de **IA (Meta AI)**. Una solución moderna, visual y sin complicaciones para gestionar tu música en la Xbox Original.

![Version](https://img.shields.io/badge/versión-1.0-green)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Platform](https://img.shields.io/badge/plataforma-Windows-lightgrey)
![License](https://img.shields.io/badge/licencia-MIT-brightgreen)

### 🎨 Del Boceto a la Realidad
Este proyecto nació de una idea simple y se convirtió en una herramienta completa.

### ✨ Características

*   **Interfaz agradable y fácil de usar:** Diseño inspirado en Xbox, intuitivo y sin curva de aprendizaje.
*   **Independiente:** No depende de listas de reproducción creadas previamente en la consola.
*   **Gestión completa de Playlists:** Capacidad de **crear, eliminar y renombrar** listas de reproducción.
*   **Gestión completa de Audios:** Puede **importar, renombrar y eliminar** audios en formato WMA.
*   **Compatibilidad Nativa:** Totalmente compatible con archivos **ST.DB** nativos de la consola creados con el MSDashboard.

### ⚠️ Limitaciones

*   No convierte audios a formato WMA.
*   No puede copiar ni mover audios entre listas de reproducción.

### 🚀 Cómo Usarlo

1.  Ejecuta el archivo `STDB_Tool_BY_ZARF.exe`.
2.  Configura tus ajustes de conexión FTP en el botón **AJUSTES**.
3.  Usa el botón central **CONECTAR** para establecer la conexión con tu Xbox.
4.  **Panel Izquierdo (Lista de Reproducción):** Administra tus listas. Dale **click derecho** para ver las opciones de Crear / Renombrar / Eliminar.
5.  **Panel Derecho (Lista Canciones):** Administra los audios de la lista seleccionada. Dale **click derecho** para Importar / Renombrar / Eliminar.
6.  Una vez hechos los cambios, presiona el botón **TRANSFERIR** para enviar todos los cambios a la consola. ¡Y listo!

### 📦 Instalación (Solo si usas el código fuente .py)

Si ejecutas el `.exe` no necesitas instalar nada.

Si quieres ejecutar los scripts `main.py` y `main_ui.py` directamente, necesitas la dependencia **Pillow**:

```bash
pip install Pillow
```

### 👥 Créditos y Agradecimientos

*   **Diseño y Desarrollo:** **ZARF**
*   **Programación:** **Meta AI**

Hecho con pasión para la comunidad de Xbox Clásica. 💚
