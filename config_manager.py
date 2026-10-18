# config_manager.py
import configparser
import os

INI = "config.ini"

def guardar_config(ip, user, pwd):
    c = configparser.ConfigParser()
    c['FTP'] = {'ip': ip, 'user': user, 'pass': pwd}
    with open(INI, 'w') as f:
        c.write(f)

def cargar_config():
    if not os.path.exists(INI):
        return None
    c = configparser.ConfigParser()
    c.read(INI)
    return dict(c['FTP']) if 'FTP' in c else None