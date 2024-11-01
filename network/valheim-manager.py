import subprocess
import os
import requests
import re
import signal
import sys
from datetime import datetime

EXEC_PATH = ""
SAVE_PATH = ""
RAW_LOG = SAVE_PATH + "\\log.txt"
MANAGER_LOG = SAVE_PATH + "\\manager_log.txt"

SERVER_DATA = {
    "name": "",
    "ip": "",
    "port": "",
    "world": "",
    "password": "",
}

os.environ["SteamAppId"] = "892970"
connection_list = []
newConnection_count = int(0)
hook_url = ""

open(RAW_LOG, "w").close()

p = subprocess.Popen(
    [
        EXEC_PATH,
        "-nographics",
        "-batchmode",
        "-name",
        f"{SERVER_DATA["name"]}",
        "-port",
        f"{SERVER_DATA["port"]}",
        "-world",
        f"{SERVER_DATA["world"]}",
        "-password",
        f"{SERVER_DATA["password"]}",
        "-public",
        "1",
        "-savedir",
        f"{SAVE_PATH}",
        "-modifier",
        "portals",
        "casual",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)


def close_cleanup():
    global newConnection_count
    out, err = p.communicate(signal.CTRL_C_EVENT)
    for line in out.splitlines():
        newConnection_count = handleWebhook(line.strip(), newConnection_count)
        file_manager.flush()
    file_manager.write(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : Cleanup finalizado. \n"
    )
    file_manager.close()


def handle_shutdown_event(sig, frame):
    file_manager.write(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : Evento de cierre detectado \n"
    )
    file_manager.flush()
    close_cleanup()
    sys.exit(0)


def handleWebhook(content, newConnection_count):
    raw_log = open(RAW_LOG, "a")
    raw_log.write(content + "\n")
    raw_log.close()

    if "Console" not in content:
        # Server start
        match = re.search(
            r"Valheim version: (\d+)\.(\d+)\.(\d+)", content, re.IGNORECASE
        )
        if match:
            file_manager.write(
                f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Server Start match \n"
            )
            embed_object = {
                "color": 5763719,
                "title": f"Servidor Valheim Iniciado",
                "description": f"Servidor {SERVER_DATA["name"]} iniciado!",
            }
            payload = {"embeds": [embed_object]}
            requests.post(hook_url, json=payload)
            return newConnection_count

        # Server stop
        if "Game - OnApplicationQuit" in content:
            file_manager.write(
                f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Server Stop match \n"
            )
            embed_object = {
                "color": 15548997,
                "title": f"Servidor Valheim detenido",
                "description": f"Servidor {SERVER_DATA["name"]} ha sido detenido.",
            }
            payload = {"embeds": [embed_object]}
            requests.post(hook_url, json=payload)
            return newConnection_count

        # Monitor for initiation of new connection
        match = re.search(r"Got handshake from client (\d+)", content)
        if match:
            file_manager.write(
                f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Match new Connection handshake {match.group(1)} \n"
            )
            file_manager.flush()
            connection_list.append({"SteamID": match.group(1), "PlayerName": ""})
            newConnection_count += 1
            file_manager.write(f"connection count: {newConnection_count} \n")
            return newConnection_count

        # Player Connection and player death
        match = re.search(r"Got character ZDOID from (.+) : (-?\d+:-?\d+)", content)
        if match:
            file_manager.write(
                f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Match character ZDOID {match.group(1)} \n"
            )
            file_manager.flush()
            player_name = match.group(1)
            if match.group(2) == "0:0":
                file_manager.write(
                    f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Match Player Dead \n"
                )
                color = 15105570
                title = "Muerte de Jugador en Valheim"
                description = f"{player_name} ha muerto en {SERVER_DATA["name"]}!"
                embed_object = {
                    "color": color,
                    "title": title,
                    "description": description,
                }
                payload = {"embeds": [embed_object]}
                requests.post(hook_url, json=payload)
            elif newConnection_count > 0:
                file_manager.write(
                    f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Match Player connection \n"
                )
                file_manager.flush()
                file_manager.write(f"Players: {connection_list} \n")
                file_manager.flush()
                connection_list[-1]["PlayerName"] = player_name
                color = 3447003
                title = "Conexion de Jugador en Valheim"
                description = f"{player_name} se ha conectado a {SERVER_DATA["name"]}!"
                newConnection_count -= 1
                file_manager.write(f"connection count: {newConnection_count} \n")
                embed_object = {
                    "color": color,
                    "title": title,
                    "description": description,
                }
                payload = {"embeds": [embed_object]}
                requests.post(hook_url, json=payload)
            return newConnection_count

        # Player disconnection
        match = re.search(r"Closing socket (\d{2,})", content)
        if match:
            steam_id = match.group(1)
            color = 16776960
            title = "Desconexion de Jugador en Valheim"
            for player in connection_list:
                if steam_id == player["SteamID"]:
                    file_manager.write(
                        f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Match player disconnect {player['PlayerName']} \n"
                    )
                    file_manager.flush()
                    file_manager.write(f"Players: {connection_list} \n")
                    description = f"{player['PlayerName']} se ha desconectado de {SERVER_DATA["name"]}."
                    connection_list.remove(player)
                    break
            embed_object = {"color": color, "title": title, "description": description}
            payload = {"embeds": [embed_object]}
            requests.post(hook_url, json=payload)
            return newConnection_count
    return newConnection_count


signal.signal(signal.SIGINT, handle_shutdown_event)

with open(MANAGER_LOG, "w") as file_manager:
    file_manager.write(
        f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Manager iniciado. \n"
    )
    file_manager.flush()
    try:
        for line in iter(p.stdout.readline, ""):
            newConnection_count = handleWebhook(line.strip(), newConnection_count)
            file_manager.flush()
    except Exception as e:
        file_manager.write(
            f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Error: {e} \n"
        )
        file_manager.flush()
    finally:
        file_manager.write(
            f"{(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")} : Finally \n"
        )
        file_manager.flush()
        close_cleanup()
