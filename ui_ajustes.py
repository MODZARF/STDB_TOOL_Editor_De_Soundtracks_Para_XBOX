# ui_ajustes.py - CON VALIDACION IP
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os, sys
import config_manager
import ipaddress

W, H = 600, 400
INVISIBLE = "#010101"

def resource_path(p):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, p)
    return os.path.abspath(p)

def es_ip_valida(ip_str):
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False

def mostrar_ventana_ajustes(parent_owner=None, on_acerca_de=None):
    if hasattr(mostrar_ventana_ajustes, 'win') and mostrar_ventana_ajustes.win.winfo_exists():
        mostrar_ventana_ajustes.win.lift()
        return

    win = tk.Toplevel()
    win.overrideredirect(True)
    win.config(bg=INVISIBLE)
    win.wm_attributes("-transparentcolor", INVISIBLE)
    win.wm_attributes("-topmost", True)
    win.geometry(f"{W}x{H}+{win.winfo_screenwidth()//2 - W//2}+{win.winfo_screenheight()//2 - H//2}")
    mostrar_ventana_ajustes.win = win

    canvas = tk.Canvas(win, width=W, height=H, bg=INVISIBLE, highlightthickness=0)
    canvas.pack()

    f = Image.open(resource_path("fondazo_ajustes.png")).convert("RGBA").resize((W, H), Image.LANCZOS)
    f_tk = ImageTk.PhotoImage(f)
    canvas.create_image(W//2, H//2, image=f_tk)

    close = canvas.create_text(W-35, 40, text="✕", fill="white", font=("Arial", 16, "bold"))
    canvas.tag_bind(close, "<Button-1>", lambda e: win.destroy())
    canvas.tag_bind(close, "<Enter>", lambda e: canvas.config(cursor="hand2"))
    canvas.tag_bind(close, "<Leave>", lambda e: canvas.config(cursor=""))

    canvas.create_text(W//2, 40, text="AJUSTES FTP", fill="white", font=("Arial", 14, "bold"))

    cfg = config_manager.cargar_config()
    ip_val = cfg['ip'] if cfg else ""
    user_val = cfg['user'] if cfg else "xbox"
    pass_val = cfg['pass'] if cfg else "xbox"

    style_entry = {"bg": "#1C1B20", "fg": "white", "insertbackground": "white",
                   "relief": "flat", "font": ("Arial", 11), "justify": "center"}

    canvas.create_text(W//2, 115, text="IP de la Xbox", fill="#cccccc", font=("Arial", 10))
    entry_ip = tk.Entry(win, **style_entry, width=22)
    entry_ip.insert(0, ip_val)
    canvas.create_window(W//2, 140, window=entry_ip)

    canvas.create_text(W//2, 175, text="Usuario FTP", fill="#cccccc", font=("Arial", 10))
    entry_user = tk.Entry(win, **style_entry, width=22)
    entry_user.insert(0, user_val)
    canvas.create_window(W//2, 200, window=entry_user)

    canvas.create_text(W//2, 235, text="Contraseña", fill="#cccccc", font=("Arial", 10))
    entry_pass = tk.Entry(win, **style_entry, width=22)
    entry_pass.insert(0, pass_val)
    canvas.create_window(W//2, 260, window=entry_pass)

    b_save = Image.open(resource_path("botonazo_guardar.png")).convert("RGBA").resize((180, 55), Image.LANCZOS)
    b_save_tk = ImageTk.PhotoImage(b_save)
    btn_save = canvas.create_image(W//2, 330, image=b_save_tk)

    def alpha_hit(pil, e, cx, cy):
        x = int(e.x - cx + pil.width//2)
        y = int(e.y - cy + pil.height//2)
        if 0 <= x < pil.width and 0 <= y < pil.height:
            return pil.getpixel((x,y))[3] > 10
        return False

    def on_guardar(e=None):
        if not alpha_hit(b_save, e, W//2, 330):
            return
        ip = entry_ip.get().strip()
        user = entry_user.get().strip()
        pwd = entry_pass.get().strip()

        if not ip:
            win.attributes("-topmost", False)
            messagebox.showerror("Dirección IP no válida", "El campo IP no puede estar vacío.", parent=win)
            win.attributes("-topmost", True)
            win.lift()
            entry_ip.focus_set()
            return

        # VALIDACION REAL CON IPADDRESS
        if not es_ip_valida(ip):
            win.attributes("-topmost", False)
            messagebox.showerror("Dirección IP no válida", f"La IP '{ip}' no es válida.", parent=win)
            win.attributes("-topmost", True)
            win.lift()
            win.focus_force()
            entry_ip.focus_set()
            entry_ip.selection_range(0, tk.END)
            return

        config_manager.guardar_config(ip, user, pwd)
        print(f"Config guardada: {ip}")
        win.destroy()

    canvas.tag_bind(btn_save, "<Button-1>", on_guardar)
    canvas.tag_bind(btn_save, "<Enter>", lambda e: canvas.config(cursor="hand2"))
    canvas.tag_bind(btn_save, "<Leave>", lambda e: canvas.config(cursor=""))

    try:
        b_ad = Image.open(resource_path("botonazo_AD.png")).convert("RGBA").resize((90, 28), Image.LANCZOS)
        b_ad_tk = ImageTk.PhotoImage(b_ad)
        btn_ad = canvas.create_image(65, 370, image=b_ad_tk)

        def on_acerca(e=None):
            if not alpha_hit(b_ad, e, 65, 370):
                return
            win.destroy()
            if on_acerca_de:
                on_acerca_de()

        canvas.tag_bind(btn_ad, "<Button-1>", on_acerca)
        canvas.tag_bind(btn_ad, "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(btn_ad, "<Leave>", lambda e: canvas.config(cursor=""))
        win.b_ad_tk = b_ad_tk
        win.b_ad_pil = b_ad
    except Exception as ex:
        print(f"No se pudo cargar botonazo_AD.png: {ex}")

    def press(e): win.ox, win.oy = e.x, e.y
    def drag(e): win.geometry(f"+{win.winfo_x()+e.x-win.ox}+{win.winfo_y()+e.y-win.oy}")
    canvas.bind("<ButtonPress-1>", press)
    canvas.bind("<B1-Motion>", drag)

    win.f_tk = f_tk
    win.b_save_tk = b_save_tk
    win.focus_set()