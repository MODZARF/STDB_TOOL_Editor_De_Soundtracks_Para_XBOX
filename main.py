# main.py - VENTANA UNIFICADA + ANILLO ACTION
import ui_ajustes
import config_manager
import st_db
from ftp_manager import ftp_client
from main_ui import crear_app_unificada
import threading
import shutil
import atexit
from pathlib import Path

TEMP_DIR = Path("temp_xbox")
TEMP_STDB = TEMP_DIR / "ST.DB"
TEMP_WMA = TEMP_DIR / "wmas"

def limpiar_temp_completa():
    try:
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
            print(f"[TEMP] Carpeta {TEMP_DIR} eliminada")
    except Exception as e:
        print(f"[TEMP] No se pudo eliminar {TEMP_DIR}: {e}")

def preparar_temp():
    limpiar_temp_completa()
    try:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        TEMP_WMA.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[TEMP] Error preparando carpeta: {e}")

# 1. LIMPIEZA AL ABRIR
preparar_temp()
atexit.register(limpiar_temp_completa)

app = None
owner = None

def abrir_ajustes():
    global app
    if app and hasattr(app, 'iniciar_creditos'):
        ui_ajustes.mostrar_ventana_ajustes(on_acerca_de=app.iniciar_creditos)
    else:
        ui_ajustes.mostrar_ventana_ajustes()

def accion_iniciar():
    global app
    if not app or not hasattr(app, 'datos') or not app.datos:
        if app and hasattr(app, 'mostrar_error'):
            app.mostrar_error("No hay ST.DB cargado.\nPrimero debes CONECTAR al Xbox y cargar un ST.DB.")
        return
    
    print("INICIANDO SUBIDA...")
    app.action_ring.set_status("PREPARANDO")
    app.action_ring.set_progress(10)

    try:
        if TEMP_WMA.exists():
            shutil.rmtree(TEMP_WMA, ignore_errors=True)
        TEMP_WMA.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[TEMP] Error limpiando wmas temp: {e}")

    try:
        stdb_path, wma_path = st_db.crear_stdb_desde_datos_editor(app.datos, TEMP_STDB, TEMP_WMA)
    except Exception as e:
        app.mostrar_error(f"Error creando ST.DB local:\n\n{e}")
        return

    carpetas_del = app.datos.get("carpetas_a_eliminar", [])
    wmas_del = app.datos.get("wmas_a_eliminar", [])

    def trabajo_subida():
        def progreso(actual, total, nombre):
            def upd():
                pct = 20 + int((actual/total*80)) if total>0 else 90
                app.action_ring.set_progress(pct)
                app.action_ring.set_status(f"{nombre[:8]}")
            app.after(0, upd)
        
        try:
            ok = ftp_client.subir_stdb_y_wmas(stdb_path, wma_path, carpetas_a_eliminar=carpetas_del, wmas_a_eliminar=wmas_del, progress_cb=progreso)
        except Exception as e:
            def err_exception():
                app.mostrar_error(f"Error durante la subida FTP:\n\n{e}\n\n{getattr(ftp_client, 'last_error', '')}")
            app.after(0, err_exception)
            return

        def fin():
            if ok:
                app.action_ring.set_progress(100)
                app.action_ring.set_status("¡LISTO!")
                print("¡SUBIDA COMPLETA!")
                app.datos["carpetas_a_eliminar"]=[]
                app.datos["wmas_a_eliminar"]=[]
                app.after(2000, lambda: app.action_ring.reset())
            else:
                msg = getattr(ftp_client, 'last_error', 'Error desconocido en FTP')
                app.mostrar_error(f"Fallo la subida al Xbox:\n\n{msg}")
                print(f"Error: {msg}")
        app.after(0, fin)

    threading.Thread(target=trabajo_subida, daemon=True).start()

def accion_conectar():
    global app
    cfg = config_manager.cargar_config()
    if not cfg:
        abrir_ajustes()
        return
    
    app.action_ring.set_status("CONECTANDO")
    app.action_ring.set_progress(15)

    def trabajo():
        try:
            ok = ftp_client.conectar(cfg['ip'], cfg['user'], cfg['pass'])
        except Exception as e:
            def err_conn_exception():
                app.mostrar_error(f"No se pudo conectar al Xbox:\n\n{e}\n\nVerifica IP, usuario, clave y que el Xbox esté encendido con FTP.")
            app.after(0, err_conn_exception)
            return

        if not ok:
            def err():
                # ERROR AL CIRCULO ROJO
                detalle = getattr(ftp_client, 'last_error', 'No se pudo conectar')
                app.mostrar_error(f"Error de conexión FTP:\n\n{detalle}")
                print(f"ERROR: {detalle}")
            app.after(0, err)
            return
        
        try:
            ruta, existe = ftp_client.descargar_stdb()
        except Exception as e:
            def err_descarga():
                app.mostrar_error(f"Error descargando ST.DB del Xbox:\n\n{e}")
            app.after(0, err_descarga)
            return

        def mostrar():
            if existe:
                try:
                    app.cargar_stdb(ruta)
                    if "carpetas_a_eliminar" not in app.datos:
                        app.datos["carpetas_a_eliminar"]=[]
                    if "wmas_a_eliminar" not in app.datos:
                        app.datos["wmas_a_eliminar"]=[]
                    app.action_ring.set_status("LISTO")
                except Exception as e:
                    app.mostrar_error(f"ST.DB descargado pero está corrupto o no se pudo leer:\n\n{e}")
                    return
            else:
                TEMP_DIR.mkdir(exist_ok=True)
                app.datos = {"num_playlists":0, "playlists":{}}
                if "carpetas_a_eliminar" not in app.datos:
                    app.datos["carpetas_a_eliminar"]=[]
                if "wmas_a_eliminar" not in app.datos:
                    app.datos["wmas_a_eliminar"]=[]
                app.list_play.delete(0,"end")
                app.list_play.insert("end", "sin listas de reproducción")
                app.action_ring.set_status("NUEVO")
            app.action_ring.set_progress(100)
            app.after(1500, lambda: app.action_ring.reset())
        app.after(0, mostrar)

    threading.Thread(target=trabajo, daemon=True).start()

def on_app_close():
    print("[APP] Cerrando, limpiando temporales...")
    try:
        ftp_client.desconectar()
    except:
        pass
    limpiar_temp_completa()
    if owner:
        owner.destroy()

owner, app = crear_app_unificada(abrir_ajustes, accion_iniciar, accion_conectar)
owner.protocol("WM_DELETE_WINDOW", on_app_close)
owner.mainloop()