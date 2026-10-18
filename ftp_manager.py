# ftp_manager.py - FIX 553 + NO RE-SUBIR + BORRADO SELECTIVO + PROGRESO ANILLO + AUTO-CREAR RUTA
import ftplib
from pathlib import Path

XBOX_MUSIC_PATH = "E:/TData/fffe0000/music"
TEMP_DIR = Path("temp_xbox")
TEMP_DIR.mkdir(exist_ok=True)

class FTPManager:
    def __init__(self):
        self.ftp = None
        self.last_error = ""

    def conectar(self, ip, user="xbox", pwd="xbox", timeout=10):
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(ip, 21, timeout=timeout)
            self.ftp.login(user, pwd)
            self.ftp.set_pasv(False)
            self.last_error = ""
            self._asegurar_ruta_music()
            return True
        except Exception as e:
            self.last_error = str(e)
            self.ftp = None
            return False

    def _asegurar_ruta_music(self):
        if not self.ftp:
            return False
        try:
            try: self.ftp.cwd("/")
            except: pass
            def entrar_o_crear(nombre):
                try:
                    self.ftp.cwd(nombre)
                    return True
                except ftplib.error_perm:
                    try: self.ftp.mkd(nombre)
                    except: pass
                    try:
                        self.ftp.cwd(nombre)
                        return True
                    except Exception as e2:
                        self.last_error = str(e2)
                        return False
            if not entrar_o_crear("E:"):
                try: self.ftp.cwd("E")
                except:
                    try: self.ftp.mkd("E")
                    except: pass
                    try: self.ftp.cwd("E")
                    except: pass
            entrar_o_crear("TData")
            entrar_o_crear("fffe0000")
            entrar_o_crear("music")
            return True
        except Exception as e:
            for ruta in ["E:/TData", "E:/TData/fffe0000", "E:/TData/fffe0000/music", "/E/TData/fffe0000/music"]:
                try: self.ftp.mkd(ruta)
                except: pass
            try:
                self.ftp.cwd("E:/TData/fffe0000/music")
                return True
            except:
                try:
                    self.ftp.cwd("/E/TData/fffe0000/music")
                    return True
                except Exception as e2:
                    self.last_error = str(e2)
                    return False

    def _ir_a_music(self):
        if not self._asegurar_ruta_music():
            try:
                try: self.ftp.cwd("/")
                except: pass
                self.ftp.cwd("E:")
                self.ftp.cwd("TData")
                self.ftp.cwd("fffe0000")
                self.ftp.cwd("music")
                return True
            except:
                try:
                    self.ftp.cwd("/E/TData/fffe0000/music")
                    return True
                except Exception as e2:
                    self.last_error = str(e2)
                    return False
        return True

    def _listar_archivos(self, folder_phys):
        try:
            self._ir_a_music()
            self.ftp.cwd(folder_phys)
            return self.ftp.nlst()
        except:
            return []

    def descargar_stdb(self):
        if not self.ftp: return None, False
        local_path = TEMP_DIR / "ST.DB"
        if not self._ir_a_music(): return None, False
        try:
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary('RETR ST.DB', f.write)
            return str(local_path), True
        except ftplib.error_perm as e:
            if "550" in str(e): return None, False
            self.last_error = str(e)
            return None, False

    def eliminar_wma_xbox(self, folder_phys, filename_phys):
        try:
            if not self._ir_a_music(): return False
            self.ftp.cwd(folder_phys)
            self.ftp.delete(filename_phys)
            print(f"[BORRADO] {folder_phys}/{filename_phys}")
            return True
        except Exception as e:
            print(f"[NO BORRADO] {folder_phys}/{filename_phys}: {e}")
            return False

    def eliminar_carpeta_playlist_xbox(self, folder_phys):
        # Borrado robusto: vacia todo antes de rmd
        try:
            if not self._ir_a_music(): return False
            files = []
            try:
                self.ftp.cwd(folder_phys)
                files = self.ftp.nlst()
            except:
                files = []
            for ar in files:
                try:
                    # algunos listan "." ".."
                    if ar in (".",".."): continue
                    self.ftp.delete(ar)
                    print(f"[BORRADO INTERNO] {folder_phys}/{ar}")
                except Exception as e:
                    print(f"[NO BORRADO INTERNO] {ar}: {e}")
            try: self.ftp.cwd("..")
            except: self._ir_a_music()
            try:
                self.ftp.rmd(folder_phys)
                print(f"[CARPETA BORRADA] {folder_phys}")
                return True
            except Exception as e:
                print(f"[NO BORRADA] {folder_phys}: {e}")
                return False
        except Exception as e:
            print(f"[ERROR CARPETA] {folder_phys}: {e}")
            return False

    def subir_stdb_y_wmas(self, stdb_local, carpeta_wmas_local, carpetas_a_eliminar=None, wmas_a_eliminar=None, progress_cb=None):
        if not self.ftp: return False
        try:
            if not self._ir_a_music():
                raise Exception(f"No se pudo crear/entrar a {XBOX_MUSIC_PATH}")

            # === BORRADO SELECTIVO - ANTES DE SUBIR NADA ===
            if wmas_a_eliminar:
                print(f"[BORRANDO {len(wmas_a_eliminar)} WMAs]")
                for folder, fname in wmas_a_eliminar:
                    self.eliminar_wma_xbox(folder, fname)
            if carpetas_a_eliminar:
                print(f"[BORRANDO {len(carpetas_a_eliminar)} CARPETAS]")
                for folder in carpetas_a_eliminar:
                    self.eliminar_carpeta_playlist_xbox(folder)

            if not self._ir_a_music():
                raise Exception(f"No se pudo entrar a {XBOX_MUSIC_PATH}")
            print(f"Subiendo ST.DB...")
            with open(stdb_local, 'rb') as f:
                self.ftp.storbinary('STOR ST.DB', f)
            print("ST.DB OK")

            base = Path(carpeta_wmas_local)
            if not base.exists():
                if progress_cb: progress_cb(1, 1, "OK")
                return True

            todos = []
            for c in base.iterdir():
                if c.is_dir():
                    todos.extend(list(c.glob("*.wma")))
            total = len(todos) if todos else 1
            actual = 0

            for carpeta_hex in base.iterdir():
                if not carpeta_hex.is_dir(): continue
                wmas_nuevos = list(carpeta_hex.glob("*.wma"))
                if not wmas_nuevos: continue

                existentes = self._listar_archivos(carpeta_hex.name)
                self._ir_a_music()
                try: self.ftp.mkd(carpeta_hex.name)
                except: pass

                for wma in wmas_nuevos:
                    if wma.name in existentes:
                        continue
                    actual += 1
                    if progress_cb:
                        progress_cb(actual, total, wma.name)
                    self._ir_a_music()
                    self.ftp.cwd(carpeta_hex.name)
                    with open(wma, 'rb') as fw:
                        self.ftp.storbinary(f'STOR {wma.name}', fw)

            if progress_cb:
                progress_cb(total, total, "COMPLETO")
            return True
        except Exception as e:
            self.last_error = str(e)
            print(f"Error: {e}")
            return False

    def desconectar(self):
        if self.ftp:
            try: self.ftp.quit()
            except: pass
            self.ftp = None

ftp_client = FTPManager()