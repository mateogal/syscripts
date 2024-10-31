import subprocess
import os
import requests
import re
import signal

EXEC_PATH = ""
SAVE_PATH = ""
RAW_LOG = SAVE_PATH + "\\log.txt"

SERVER_DATA = {
    "name": "",
    "ip": "",
    "port": "",
    "world": "",
    "password": "",
}

os.environ["SteamAppId"] = "892970"
connection_list = []

open(RAW_LOG, "w").close()


def handleWebhook(content):
    hook_url = ""

    raw_log = open(RAW_LOG, "a")
    raw_log.write(content + "\n")
    raw_log.close()

    if "Console" not in content:
        # Server start
        match = re.search(
            r"Valheim version: (\d+)\.(\d+)\.(\d+)", content, re.IGNORECASE
        )
        if match:
            print("Server Start match")
            embed_object = {
                "color": 5763719,
                "title": f"Servidor Valheim Iniciado",
                "description": f"Servidor {SERVER_DATA["name"]} iniciado!",
            }
            payload = {"embeds": [embed_object]}
            requests.post(hook_url, json=payload)
            return

        # Server stop
        if "Game - OnApplicationQuit" in content:
            print("Server Stop match")
            embed_object = {
                "color": 15548997,
                "title": f"Servidor Valheim detenido",
                "description": f"Servidor {SERVER_DATA["name"]} ha sido detenido.",
            }
            payload = {"embeds": [embed_object]}
            requests.post(hook_url, json=payload)
            return

        # Monitor for initiation of new connection
        match = re.search(r"Got handshake from client (\d+)", content)
        if match:
            print("Match new Connection handshake")
            connection_list.append({"SteamID": match.group(1), "PlayerName": ""})
            print(connection_list)
            return

        # Player Connection and player death
        match = re.search(r"Got character ZDOID from (.+) : (-?\d+:-?\d+)", content)
        if match:
            print("Match character ZDOID")
            player_name = match.group(1)
            if match.group(2) == "0:0":
                print("Match Player Dead")
                color = 15105570
                title = "Muerte de Jugador en Valheim"
                description = (
                    f"El jugador {player_name} ha muerto en {SERVER_DATA["name"]}!"
                )
            else:
                print("Match Player connection")
                connection_list[-1]["PlayerName"] = player_name
                color = 3447003
                title = "Conexion de Jugador en Valheim"
                description = f"El jugador {player_name} se ha conectado a {SERVER_DATA["name"]}!"

            embed_object = {"color": color, "title": title, "description": description}
            payload = {"embeds": [embed_object]}
            requests.post(hook_url, json=payload)
            return

        # Player disconnection
        match = re.search(r"Closing socket (\d{2,})", content)
        if match:
            print("Match player disconnect")
            steam_id = match.group(1)
            color = 16776960
            title = "Desconexion de Jugador en Valheim"
            for player in connection_list:
                if steam_id == player["SteamID"]:
                    description = f"El jugador {player['PlayerName']} se ha desconectado de {SERVER_DATA["name"]}."
                    connection_list.remove(player)
                    break
            print(connection_list)
            embed_object = {"color": color, "title": title, "description": description}
            payload = {"embeds": [embed_object]}
            requests.post(hook_url, json=payload)
            return


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

try:
    for line in iter(p.stdout.readline, ""):
        handleWebhook(line.strip())
except Exception as e:
    print(f"Error: {e}")
except KeyboardInterrupt:
    out, err = p.communicate(signal.CTRL_C_EVENT)
    for line in out.splitlines():
        handleWebhook(line.strip())
finally:
    p.stdout.close()
    p.wait()
