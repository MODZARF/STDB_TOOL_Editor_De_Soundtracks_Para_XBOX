# st_db.py - CORREGIDO BE en disco / LE en ST.DB - FIX file_id 0
import struct
from pathlib import Path
import shutil

def be_hex4(val: int) -> str:
    return f"{val & 0xFFFF:04X}" # 1 -> 0001, 2 -> 0002

def get_duration_ms_wma(filepath):
    try:
        from mutagen.wma import WMA
        return int(WMA(filepath).info.length * 1000)
    except:
        try:
            from mutagen import File
            f = File(str(filepath))
            return int(f.info.length * 1000) if f and f.info else 0
        except:
            return 0

def read_utf16_fixed(data, offset, max_len=160):
    raw = data[offset:offset+max_len]
    try:
        text = raw.decode('utf-16le', errors='ignore')
        if '\x00' in text:
            text = text.split('\x00')[0]
        return text.strip()
    except:
        return ""

def leer_stdb(st_path):
    p = Path(st_path) if st_path else None
    if not p or not p.exists():
        return {"num_playlists":0, "playlists":{}, "max_file_low": -1, "max_folder_id": -1}

    data = p.read_bytes()
    if len(data) < 0x200:
        return {"num_playlists":0, "playlists":{}, "max_file_low": -1, "max_folder_id": -1}

    num_playlists = struct.unpack_from('<I', data, 0x04)[0]
    playlists = {}
    max_file_low = -1
    max_folder_id = -1
    all_file_lows = []

    for i in range(num_playlists):
        off = 0x200 + (i * 512)
        if off+512 > len(data): break
        if data[off:off+4]!= bytes.fromhex("71 13 02 00"): continue
        p_idx = struct.unpack_from('<I', data, off+4)[0]
        num_songs = struct.unpack_from('<I', data, off+8)[0]
        name = read_utf16_fixed(data, off+352, 160) or f"Playlist {p_idx}"
        playlists[p_idx] = {"name": name, "num_songs": num_songs, "off": off, "tracks": []}
        max_folder_id = max(max_folder_id, p_idx)

    base = 0xCA00
    if len(data) > base:
        num_blocks = (len(data) - base)//512
        for bid in range(num_blocks):
            off = base + bid*512
            if data[off:off+4]!= bytes.fromhex("73 10 03 00"): continue
            p_idx = struct.unpack_from('<I', data, off+4)[0]
            if p_idx not in playlists: continue

            for k in range(6):
                file_id = struct.unpack_from('<I', data, off+16 + k*4)[0] # LE en archivo
                ms = struct.unpack_from('<I', data, off+40 + k*4)[0]
                song_name = read_utf16_fixed(data, off+64 + k*64, 64)
                
                # FIX ZARF: file_id 0 es valido (00000000.wma)
                if not song_name: 
                    continue
                # slot realmente vacio: sin nombre y ms 0
                if file_id == 0 and ms == 0 and not song_name:
                    continue

                folder_id = (file_id >> 16) & 0xFFFF
                file_low = file_id & 0xFFFF

                max_folder_id = max(max_folder_id, folder_id)
                # Solo contamos file_low si no es el 0 fantasma de slot vacio (que ya filtramos)
                if not (file_id == 0 and not song_name):
                    max_file_low = max(max_file_low, file_low)
                    all_file_lows.append(file_low)

                filename_be = f"{be_hex4(folder_id)}{be_hex4(file_low)}.wma"
                folder_be = be_hex4(folder_id)

                playlists[p_idx]["tracks"].append({
                    "name": song_name,
                    "ms": ms,
                    "file_id": file_id,
                    "folder_id": folder_id,
                    "file_low": file_low,
                    "filename_phys": filename_be,
                    "folder_phys": folder_be,
                    "file_id_le_hex": struct.pack('<I', file_id).hex().upper()
                })

    for pid in playlists:
        playlists[pid]["tracks"] = playlists[pid]["tracks"][:playlists[pid]["num_songs"]]

    return {"num_playlists": len(playlists), "playlists": playlists, "max_file_low": max_file_low, "max_folder_id": max_folder_id, "all_file_lows": all_file_lows}

def crear_stdb_desde_datos_editor(datos, salida_st: Path, carpeta_temporal_wma: Path):
    salida_st = Path(salida_st)
    carpeta_temporal_wma = Path(carpeta_temporal_wma)
    carpeta_temporal_wma.mkdir(parents=True, exist_ok=True)
    salida_st.parent.mkdir(parents=True, exist_ok=True)

    max_folder_id = datos.get("max_folder_id", -1)

    playlists_ids = sorted(datos["playlists"].keys())
    playlists = [datos["playlists"][pid] for pid in playlists_ids]
    num_playlists = len(playlists)
    total_tracks = sum(len(p["tracks"]) for p in playlists)

    playlist_to_blocks = []
    block_counter = 0
    for pl in playlists:
        needed = (len(pl["tracks"]) + 5)//6 or 1
        blocks = list(range(block_counter, block_counter+needed))
        playlist_to_blocks.append(blocks)
        block_counter += needed

    num_song_blocks = block_counter or 1
    FILE_SIZE = 0xCA00 + (num_song_blocks * 512)
    data = bytearray(FILE_SIZE)

    data[0:4] = bytes.fromhex("01 00 00 00")
    struct.pack_into('<I', data, 0x04, num_playlists)
    struct.pack_into('<I', data, 0x08, num_playlists)
    for i, pid_real in enumerate(playlists_ids):
        struct.pack_into('<I', data, 0x0C + i*4, pid_real)
    struct.pack_into('<I', data, 0x19C, total_tracks)

    # 71 13 02 00
    for idx, (pid_real, pl) in enumerate(zip(playlists_ids, playlists)):
        off = 0x200 + (idx*512)
        data[off:off+4] = bytes.fromhex("71 13 02 00")
        struct.pack_into('<I', data, off+4, pid_real)
        struct.pack_into('<I', data, off+8, len(pl["tracks"]))
        for j, bid in enumerate(playlist_to_blocks[idx]):
            struct.pack_into('<I', data, off+12 + j*4, bid)
        total_ms = sum(t["ms"] for t in pl["tracks"])
        struct.pack_into('<I', data, off+348, total_ms)
        name_bytes = pl["name"][:32].encode('utf-16le')
        data[off+352:off+352+len(name_bytes)] = name_bytes

    # 73 10 03 00
    base = 0xCA00
    bid_global = 0
    usados = set(datos.get("all_file_lows", []))
    # FIX ZARF: empezar en 1
    if usados:
        next_low = max(usados) + 1
    else:
        next_low = 1
    if next_low == 0:
        next_low = 1

    for idx, (pid_real, pl) in enumerate(zip(playlists_ids, playlists)):
        for parte, start in enumerate(range(0, len(pl["tracks"]), 6)):
            chunk = pl["tracks"][start:start+6]
            off = base + bid_global*512
            data[off:off+4] = bytes.fromhex("73 10 03 00")
            struct.pack_into('<I', data, off+4, pid_real)
            struct.pack_into('<I', data, off+8, parte)

            for i in range(6):
                if i < len(chunk):
                    tr = chunk[i]
                    if "file_id" in tr and tr["file_id"] is not None:
                        file_id = tr["file_id"]
                    else:
                        while next_low in usados:
                            next_low += 1
                        file_low = next_low
                        usados.add(file_low)
                        next_low += 1
                        folder_id = pid_real
                        file_id = (folder_id << 16) | (file_low & 0xFFFF)
                        tr["file_id"] = file_id
                        tr["folder_id"] = folder_id
                        tr["file_low"] = file_low
                        tr["folder_phys"] = be_hex4(folder_id)
                        tr["filename_phys"] = f"{be_hex4(folder_id)}{be_hex4(file_low)}.wma"
                else:
                    file_id = 0
                struct.pack_into('<I', data, off+16 + i*4, file_id)

            for i in range(6):
                ms = chunk[i]["ms"] if i < len(chunk) else 0
                struct.pack_into('<I', data, off+40 + i*4, ms)

            for i, track in enumerate(chunk):
                utf16 = track["name"][:32].encode('utf-16le')
                data[off+64 + i*64: off+64 + i*64 + len(utf16)] = utf16

            bid_global += 1

    salida_st.write_bytes(data)

    for pid_real, pl in zip(playlists_ids, playlists):
        folder_be = be_hex4(pid_real)
        dest_folder = carpeta_temporal_wma / folder_be
        dest_folder.mkdir(exist_ok=True)
        for track in pl["tracks"]:
            src = track.get("path_local")
            if not src: continue
            fname = track["filename_phys"]
            try:
                shutil.copy2(src, dest_folder / fname)
            except: pass

    datos["max_file_low"] = max(usados) if usados else -1
    datos["all_file_lows"] = list(usados)

    return str(salida_st), str(carpeta_temporal_wma)