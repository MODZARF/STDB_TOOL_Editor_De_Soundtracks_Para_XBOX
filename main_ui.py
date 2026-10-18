# main_ui.py - CON SISTEMA DE ERROR VISUAL + CIRCULO ROJO
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
from PIL import Image, ImageTk
import os, sys
from pathlib import Path
import st_db

W, H = 850, 500
INVISIBLE = "#010101"

PLAYLIST_START = 0x200
PLAYLIST_STRUCT_SIZE = 0x200
MAX_PLAYLISTS_OFFSET = 0xCA00
MAX_PLAYLISTS = 100
MAX_WMAS_X_PLAYLIST = 500
LIMITE_NOMBRE = 20

def resource_path(p):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, p)
    return os.path.abspath(p)

class ActionRing:
    def __init__(self, canvas, x, y, size=140, on_click=None, error_image=None):
        self.canvas = canvas
        self.x, self.y = x, y
        self.size = size
        s = size//2
        self.bg_oval = canvas.create_oval(x-s+8, y-s+8, x+s-8, y+s-8, outline="#222", width=10)
        self.prog = canvas.create_arc(x-s+8, y-s+8, x+s-8, y+s-8, start=90, extent=0, style="arc", outline="#FFFFFF", width=10)
        self.txt = canvas.create_text(x, y, text="CONECTAR", fill="#FFFFFF", font=("Consolas", 14, "bold"), justify="center")
        self.pct = canvas.create_text(x, y+50, text="", fill="#FFFFFF", font=("Consolas", 9, "bold"))
        self.hit = canvas.create_oval(x-s, y-s, x+s, y+s, fill="", outline="", width=0)
        # Imagen de error (círculo rojo)
        self.error_img_id = None
        self.error_img_tk = error_image
        if error_image:
            self.error_img_id = canvas.create_image(x, y, image=error_image, state="hidden")
        
        self.on_click = on_click
        self._click_enabled = True
        self.modo_error = False
        self.ultimo_error = ""
        
        for it in (self.bg_oval, self.prog, self.txt, self.pct, self.hit, self.error_img_id):
            if it is None: continue
            canvas.tag_bind(it, "<Button-1>", lambda e: self._handle_click())
            canvas.tag_bind(it, "<Enter>", lambda e: canvas.config(cursor="hand2"))
            canvas.tag_bind(it, "<Leave>", lambda e: canvas.config(cursor=""))


    def _handle_click(self):
        if self.modo_error:
            try:
                win = self.canvas.winfo_toplevel()
                win.attributes("-topmost", False)
                messagebox.showerror("Detalle del error", self.ultimo_error, parent=win)
                win.attributes("-topmost", True)
                win.lift()
                win.focus_force()
            except:
                messagebox.showerror("Detalle del error", self.ultimo_error)
            self.reset_error()
            return
        if not self._click_enabled: return
        if self.on_click: self.on_click()

    def set_progress(self, p):
        if self.modo_error: return
        self.canvas.itemconfig(self.prog, extent= -(p/100*360))
        self.canvas.itemconfig(self.pct, text=f"{int(p)}%" if p>0 else "")
    
    def set_status(self, t):
        if self.modo_error: return
        self.canvas.itemconfig(self.txt, text=t[:10])

    def reset(self):
        if self.modo_error: return
        self.set_progress(0)
        self.canvas.itemconfig(self.txt, text="CONECTAR", font=("Consolas", 14, "bold"))

    def mostrar_error(self, mensaje_detalle):
        self.modo_error = True
        self.ultimo_error = mensaje_detalle
        self._click_enabled = False

        self.canvas.itemconfig(self.bg_oval, state="hidden")
        self.canvas.itemconfig(self.prog, state="hidden")
        self.canvas.itemconfig(self.pct, state="hidden")

        if self.error_img_id:
            self.canvas.itemconfig(self.error_img_id, state="normal")

        self.canvas.itemconfig(self.txt, text="¡ERROR!\nPresione aquí\npara ver\ndetalles", font=("Consolas", 9, "bold"), fill="white", justify="center")
        self.canvas.tag_raise(self.txt)

    def reset_error(self):
        self.modo_error = False
        self.ultimo_error = ""
        self._click_enabled = True
        if self.error_img_id:
            self.canvas.itemconfig(self.error_img_id, state="hidden")
        self.canvas.itemconfig(self.bg_oval, state="normal")
        self.canvas.itemconfig(self.prog, state="normal")
        self.canvas.itemconfig(self.pct, state="normal")
        self.canvas.itemconfig(self.txt, text="CONECTAR", font=("Consolas", 14, "bold"), fill="white")
        self.set_progress(0)

def crear_app_unificada(on_ajustes, on_iniciar, on_conectar):
    owner = tk.Tk()
    owner.title("ST.DB Tool")
    owner.geometry("1x1+0+0")
    owner.attributes("-alpha", 0.0)

    try:
        ico = resource_path("icono.ico")
        if os.path.exists(ico):
            owner.iconbitmap(ico)
    except Exception as e:
        print(f"[ICONO] {e}")

    win = tk.Toplevel(owner)
    win.overrideredirect(True)
    win.geometry(f"{W}x{H}+{win.winfo_screenwidth()//2 - W//2}+{win.winfo_screenheight()//2 - H//2}")
    win.config(bg=INVISIBLE)
    win.wm_attributes("-transparentcolor", INVISIBLE)
    win.wm_attributes("-alpha", 0.97)
    win.wm_attributes("-topmost", True)

    canvas = tk.Canvas(win, width=W, height=H, bg=INVISIBLE, highlightthickness=0)
    canvas.pack()

    f = Image.open(resource_path("fondazo.png")).convert("RGBA").resize((760, 420), Image.LANCZOS)
    f_tk = ImageTk.PhotoImage(f)
    canvas.create_image(W//2, H//2, image=f_tk)

    b1 = Image.open(resource_path("botonazo_1.png")).convert("RGBA").resize((210, 65), Image.LANCZOS)
    b1_tk = ImageTk.PhotoImage(b1)
    btn_ajustes = canvas.create_image(W//2, 72, image=b1_tk)

    b2 = Image.open(resource_path("botonazo_3.png")).convert("RGBA").resize((210, 65), Image.LANCZOS)
    b2_tk = ImageTk.PhotoImage(b2)
    btn_iniciar = canvas.create_image(W//2, H-73, image=b2_tk)

    try:
        b_err = Image.open(resource_path("botonazo_Error.png")).convert("RGBA").resize((140, 140), Image.LANCZOS)
        b_err_tk = ImageTk.PhotoImage(b_err)
    except:
        b_err_tk = None

    action_ring = ActionRing(canvas, W//2, H//2, size=140, on_click=on_conectar, error_image=b_err_tk)

    left_container = tk.Frame(win, bg="#0f0f0f")
    canvas.create_window(220, H//2+5, window=left_container, width=200, height=260)
    right_container = tk.Frame(win, bg="#0f0f0f")
    canvas.create_window(W-220, H//2+5, window=right_container, width=200, height=260)

    list_play = tk.Listbox(left_container, bg="#1a1a1a", fg="white", relief="flat", font=("Arial", 10), exportselection=False, borderwidth=0)
    list_play.pack(fill="both", expand=True, padx=4, pady=4)
    list_songs = tk.Listbox(right_container, bg="#1a1a1a", fg="white", relief="flat", font=("Consolas", 9), exportselection=False, borderwidth=0)
    list_songs.pack(fill="both", expand=True, padx=4, pady=4)

    hint_bg = canvas.create_rectangle(W//2-170, H-38, W//2+170, H-18, fill="#0f0f0f", outline="#7CFF01", state="hidden")
    hint_txt = canvas.create_text(W//2, H-28, text="", fill="#7CFF01", font=("Consolas", 8, "bold"), state="hidden")

    def mostrar_hint(texto):
        if estado_creditos["activo"] or action_ring.modo_error: return
        canvas.itemconfig(hint_txt, text=texto)
        canvas.itemconfig(hint_bg, state="normal")
        canvas.itemconfig(hint_txt, state="normal")
        canvas.tag_raise(hint_bg)
        canvas.tag_raise(hint_txt)
    def ocultar_hint(e=None):
        canvas.itemconfig(hint_bg, state="hidden")
        canvas.itemconfig(hint_txt, state="hidden")
    #Si modifica el programa por favor mantén los créditos originales :)
    creditos_textos = ["Hecho por\nZARF","Programado\ncon Meta AI","ST.DB Tool\nv1.0","Para XBOX\n<3"]
    estado_creditos = {"activo": False, "idx": 0, "job": None}

    def press(e):
        if estado_creditos["activo"]:
            detener_creditos()
            return
        win.ox, win.oy = e.x, e.y
    def drag(e):
        if estado_creditos["activo"] or action_ring.modo_error: return
        win.geometry(f"+{win.winfo_x()+e.x-win.ox}+{win.winfo_y()+e.y-win.oy}")

    def detener_creditos(event=None):
        if not estado_creditos["activo"]: return
        if estado_creditos["job"]: win.after_cancel(estado_creditos["job"])
        estado_creditos["activo"] = False
        estado_creditos["job"] = None
        canvas.itemconfig(action_ring.bg_oval, state="normal")
        canvas.itemconfig(action_ring.prog, state="normal")
        canvas.itemconfig(action_ring.pct, state="normal")
        canvas.itemconfig(action_ring.txt, text="CONECTAR", font=("Consolas", 14, "bold"))
        action_ring._click_enabled = True
        ocultar_hint()

    def rotar_texto():
        if not estado_creditos["activo"]: return
        txt = creditos_textos[estado_creditos["idx"] % len(creditos_textos)]
        canvas.itemconfig(action_ring.txt, text=txt, font=("Arial", 12, "bold"), justify="center")
        estado_creditos["idx"] += 1
        estado_creditos["job"] = win.after(1000, rotar_texto)

    def iniciar_creditos():
        if estado_creditos["activo"] or action_ring.modo_error: return
        estado_creditos["activo"] = True
        estado_creditos["idx"] = 0
        action_ring._click_enabled = False
        canvas.itemconfig(action_ring.prog, state="hidden")
        canvas.itemconfig(action_ring.pct, state="hidden")
        rotar_texto()

    win.iniciar_creditos = iniciar_creditos
    win.detener_creditos = detener_creditos
    win.mostrar_error = lambda msg: action_ring.mostrar_error(msg)
    win.datos = None
    win.action_ring = action_ring
    win.list_play = list_play
    win.list_songs = list_songs

    def cargar_stdb(path):
        win.stdb_path = path
        win.datos = st_db.leer_stdb(path)
        win.datos.setdefault("carpetas_a_eliminar", [])
        win.datos.setdefault("wmas_a_eliminar", [])
        list_play.delete(0, "end")
        for pid in sorted(win.datos["playlists"].keys()):
            list_play.insert("end", win.datos["playlists"][pid]['name'][:LIMITE_NOMBRE])
        if win.datos["num_playlists"]==0:
            list_play.insert("end", "sin listas de reproducción")
    win.cargar_stdb = cargar_stdb

    def get_pid():
        sel = list_play.curselection()
        if not sel: return None
        try: return sorted(win.datos["playlists"].keys())[sel[0]]
        except: return None

    def refrescar_derecha():
        pid = get_pid()
        list_songs.delete(0, "end")
        if pid is None: return
        ANCHO_NOMBRE = 16
        for i, t in enumerate(win.datos["playlists"][pid]["tracks"], start=1):
            m = int(t["ms"]//60000); s = int((t["ms"]%60000)//1000)
            nombre = t['name'][:LIMITE_NOMBRE]
            nombre_vis = nombre[:ANCHO_NOMBRE]
            linea = f"{i:2d}. {nombre_vis:<{ANCHO_NOMBRE}} {m:02d}:{s:02d}"
            list_songs.insert("end", linea)

    list_play.bind("<<ListboxSelect>>", lambda e: refrescar_derecha())

    def crear_lista(nombre_forzado=None):
        if win.datos is None: win.datos = {"num_playlists":0, "playlists":{}, "carpetas_a_eliminar":[], "wmas_a_eliminar":[]}
        num_actual = len(win.datos["playlists"])
        proximo_offset = PLAYLIST_START + (num_actual * PLAYLIST_STRUCT_SIZE)
        if proximo_offset >= MAX_PLAYLISTS_OFFSET or num_actual >= MAX_PLAYLISTS:
            win.mostrar_error(f"Límite físico alcanzado.\nOffset {hex(proximo_offset)} >= {hex(MAX_PLAYLISTS_OFFSET)}\nMáximo {MAX_PLAYLISTS} listas.")
            return
        if win.datos["num_playlists"]==0 and list_play.size()>0 and "sin listas" in list_play.get(0).lower(): list_play.delete(0)
        nombre = nombre_forzado or simpledialog.askstring("Crear", f"Nombre (max {LIMITE_NOMBRE} chars):", parent=win)
        if not nombre: return
        nombre = nombre[:LIMITE_NOMBRE]
        nid = max(win.datos["playlists"].keys())+1 if win.datos["playlists"] else 0
        win.datos["playlists"][nid] = {"name": nombre, "num_songs": 0, "tracks": []}
        win.datos["num_playlists"] = len(win.datos["playlists"])
        list_play.insert("end", nombre)

    def renombrar_playlist():
        pid=get_pid();
        if pid is None: return
        nuevo=simpledialog.askstring("Renombrar", f"Nuevo (max {LIMITE_NOMBRE}):", initialvalue=win.datos["playlists"][pid]["name"][:LIMITE_NOMBRE], parent=win)
        if nuevo:
            nuevo = nuevo[:LIMITE_NOMBRE]
            win.datos["playlists"][pid]["name"]=nuevo
            idx=sorted(win.datos["playlists"].keys()).index(pid)
            list_play.delete(idx); list_play.insert(idx,nuevo); list_play.selection_set(idx)

    def eliminar_playlist():
        pid=get_pid()
        if pid is None: return
        if not messagebox.askyesno("Confirmar", f"Eliminar '{win.datos['playlists'][pid]['name']}'?", parent=win): return
        folder_be = f"{pid:04X}"
        if folder_be not in win.datos["carpetas_a_eliminar"]:
            win.datos["carpetas_a_eliminar"].append(folder_be)
        win.datos["wmas_a_eliminar"] = [x for x in win.datos["wmas_a_eliminar"] if x[0] != folder_be]
        win.datos["playlists"].pop(pid); win.datos["num_playlists"]=len(win.datos["playlists"])
        list_play.delete(list_play.curselection()); list_songs.delete(0,"end")

    def importar_wma():
        pid=get_pid()
        if pid is None:
            win.mostrar_error("Debes seleccionar una lista de reproducción antes de importar audios.")
            return
        actual = len(win.datos["playlists"][pid]["tracks"])
        if actual >= MAX_WMAS_X_PLAYLIST:
            win.mostrar_error(f"Esta lista ya tiene {actual} audios.\nMáximo {MAX_WMAS_X_PLAYLIST} por lista.")
            return
        files=filedialog.askopenfilenames(parent=win, filetypes=[("WMA","*.wma")])
        if not files: return
        if actual + len(files) > MAX_WMAS_X_PLAYLIST:
            win.mostrar_error(f"Solo puedes agregar {MAX_WMAS_X_PLAYLIST - actual} audios más.\nIntentas agregar {len(files)}.")
            return
        for ff in files:
            nombre_corto = Path(ff).stem[:LIMITE_NOMBRE]
            win.datos["playlists"][pid]["tracks"].append({"name": nombre_corto, "ms": st_db.get_duration_ms_wma(ff), "path_local": ff})
        win.datos["playlists"][pid]["num_songs"]=len(win.datos["playlists"][pid]["tracks"]); refrescar_derecha()

    def renombrar_audio():
        pid=get_pid()
        if pid is None or not list_songs.curselection(): return
        idx=list_songs.curselection()[0]
        actual=win.datos["playlists"][pid]["tracks"][idx]["name"][:LIMITE_NOMBRE]
        nuevo=simpledialog.askstring("Renombrar audio", f"Nuevo (max {LIMITE_NOMBRE}):", initialvalue=actual, parent=win)
        if nuevo:
            win.datos["playlists"][pid]["tracks"][idx]["name"]=nuevo[:LIMITE_NOMBRE]
            refrescar_derecha()

    def eliminar_audio():
        pid=get_pid()
        if pid is None or not list_songs.curselection(): return
        idx=list_songs.curselection()[0]
        track=win.datos["playlists"][pid]["tracks"][idx]
        if not messagebox.askyesno("Confirmar", f"Eliminar '{track['name']}'?", parent=win): return
        if "filename_phys" in track and "folder_phys" in track:
            entry = (track["folder_phys"], track["filename_phys"])
            if entry not in win.datos["wmas_a_eliminar"]:
                win.datos["wmas_a_eliminar"].append(entry)
        win.datos["playlists"][pid]["tracks"].pop(idx); refrescar_derecha()

    menu_izq=tk.Menu(win,tearoff=0)
    menu_izq.add_command(label="Crear nueva lista",command=crear_lista)
    menu_izq.add_command(label="Renombrar",command=renombrar_playlist)
    menu_izq.add_command(label="Eliminar",command=eliminar_playlist)
    menu_der=tk.Menu(win,tearoff=0)
    menu_der.add_command(label="Importar WMA",command=importar_wma)
    menu_der.add_command(label="Renombrar",command=renombrar_audio)
    menu_der.add_command(label="Eliminar",command=eliminar_audio)

    def popup_izq(e):
        idx = list_play.nearest(e.y)
        if idx >= 0:
            list_play.selection_clear(0, "end"); list_play.selection_set(idx); list_play.activate(idx)
        menu_izq.tk_popup(e.x_root, e.y_root)
        ocultar_hint()
    def popup_der(e):
        idx = list_songs.nearest(e.y)
        if idx >= 0:
            list_songs.selection_clear(0, "end"); list_songs.selection_set(idx); list_songs.activate(idx)
            list_songs.event_generate("<<ListboxSelect>>")
        menu_der.tk_popup(e.x_root, e.y_root)
        ocultar_hint()

    list_play.bind("<Enter>", lambda e: mostrar_hint("Click derecho → Crear / Renombrar / Eliminar lista"))
    list_play.bind("<Leave>", ocultar_hint)
    list_songs.bind("<Enter>", lambda e: mostrar_hint("Click derecho → Importar / Renombrar / Eliminar audio"))
    list_songs.bind("<Leave>", ocultar_hint)
    list_play.bind("<Button-3>", popup_izq)
    list_songs.bind("<Button-3>", popup_der)

    def alpha_hit(pil, e, cx, cy):
        x=int(e.x-cx+pil.width//2); y=int(e.y-cy+pil.height//2)
        return 0<=x<pil.width and 0<=y<pil.height and pil.getpixel((x,y))[3]>10
    canvas.tag_bind(btn_ajustes, "<Button-1>", lambda e: on_ajustes() if alpha_hit(b1, e, W//2, 70) else None)
    canvas.tag_bind(btn_iniciar, "<Button-1>", lambda e: on_iniciar() if alpha_hit(b1, e, W//2, H-75) else None)

    close_bg = canvas.create_rectangle(W-74, 2, W-44, 28, fill="#1e1e1e", outline="")
    close_txt = canvas.create_text(W-59, 15, text="✕", fill="#7CFF01", font=("Arial", 13, "bold"))
    mini_bg = canvas.create_rectangle(W-108, 2, W-76, 28, fill="#1e1e1e", outline="")
    mini_txt = canvas.create_text(W-92, 15, text="—", fill="#7CFF01", font=("Arial", 13, "bold"))

    def set_hand_close(e): 
        canvas.config(cursor="hand2")
        canvas.itemconfig(close_bg, fill="#e81123")
    def set_hand_mini(e):
        canvas.config(cursor="hand2")
        canvas.itemconfig(mini_bg, fill="#3a3a3a")
    def set_arrow_close(e): 
        canvas.config(cursor="")
        canvas.itemconfig(close_bg, fill="#1e1e1e")
    def set_arrow_mini(e):
        canvas.config(cursor="")
        canvas.itemconfig(mini_bg, fill="#1e1e1e")

    for item in (close_bg, close_txt):
        canvas.tag_bind(item, "<Enter>", set_hand_close)
        canvas.tag_bind(item, "<Leave>", set_arrow_close)
        canvas.tag_bind(item, "<Button-1>", lambda e: owner.destroy())
    for item in (mini_bg, mini_txt):
        canvas.tag_bind(item, "<Enter>", set_hand_mini)
        canvas.tag_bind(item, "<Leave>", set_arrow_mini)
        canvas.tag_bind(item, "<Button-1>", lambda e: (win.withdraw(), owner.iconify()))

    for btn in (btn_ajustes, btn_iniciar):
        canvas.tag_bind(btn, "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(btn, "<Leave>", lambda e: canvas.config(cursor=""))

    owner.bind("<Unmap>", lambda e: win.withdraw() if owner.state() == 'iconic' else None)
    owner.bind("<Map>", lambda e: win.deiconify())

    canvas.bind("<ButtonPress-1>", press)
    canvas.bind("<B1-Motion>", drag)

    win.f_tk, win.b1_tk, win.b2_tk, win.b_err_tk = f_tk, b1_tk, b2_tk, b_err_tk
    return owner, win