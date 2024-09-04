###############################################################################
###############################################################################
##                  Modificar todas las variables de                         ##
##              Respaldos Origen/Destino, ejecucion, logs                    ##
##                      con las que correspondan.                            ##
##                   Los destinos para DEBEN ser                             ##
##               rutas de red absolutas (indicando el disco)                 ##
##                                                                           ##
##                 Modificar la variable CLIENTE con la que                  ##
##                             corresponda                                   ##
###############################################################################
###############################################################################

# Librerias
import platform
import sys
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import json
import ssl
import pathlib
import traceback
import zipfile
import shutil

# Respaldos Origen/Destino, ejecucion y logs
ARCHIVO_LOG = "C:\\scripts\\logs.log"
DIR_EXEC = "C:\\scripts\\"
RESPALDOS = {
    "Completo": {
        "Origen": [
            "\\\\192.168.85.100\\c$\\Intel",
            "C:\\Users\\Mateo\\Pictures\\Screenshots",
            "C:\\Users\\Mateo\\Desktop\\RDP",
        ],
        "Destino": [
            "\\\\192.168.85.100\\c$\\Users\\Mateo\\Desktop",
            "\\\\192.168.85.100\\Prueba",
        ],
    },
    "RDP": {
        "Origen": ["C:\\Program Files (x86)\\Adobe"],
        "Destino": ["\\\\192.168.85.100\\Prueba"],
    },
}

# Tipo de OS, nombre PC, fecha, unidades
OS_TYPE = platform.system()
NOMBRE_PC = platform.node()
CLIENTE = "Mateo"
now = datetime.now()
FECHA = now.strftime("%d/%m/%Y %H:%M:%S")
FECHA_COMP = now.strftime("%d-%m-%Y")
MES = now.strftime("%B")
YEAR = now.strftime("%Y")

# Generar salida directamente al log
sys.stdout = open(ARCHIVO_LOG, "w")


# Funcion de envio de mail
def enviar_mail(info):
    # Iniciamos los parámetros del mail
    destinatarios = ["MAIL"]
    cuerpo = json.dumps(info, indent=4, sort_keys=True)
    nombre_adjunto = "Logs " + NOMBRE_PC + ".log"

    # Creamos el objeto mensaje
    mensaje = MIMEMultipart()

    # Establecemos los atributos del mensaje
    password = "YOUR_PASSWORD"
    mensaje["From"] = "MAIL"
    mensaje["To"] = ", ".join(destinatarios)
    mensaje["Subject"] = "Resultado de los Backups en: " + CLIENTE + " / " + NOMBRE_PC

    # Agregamos el cuerpo del mensaje como objeto MIME de tipo texto
    mensaje.attach(MIMEText(cuerpo, "plain"))

    # Abrimos el archivo que vamos a adjuntar
    archivo_adjunto = open(ARCHIVO_LOG, "rb")
    # Creamos un objeto MIME base
    adjunto_MIME = MIMEBase("application", "octet-stream")
    # Y le cargamos el archivo adjunto
    adjunto_MIME.set_payload((archivo_adjunto).read())
    # Codificamos el objeto en BASE64
    encoders.encode_base64(adjunto_MIME)
    # Agregamos una cabecera al objeto
    adjunto_MIME.add_header(
        "Content-Disposition", "attachment; filename= %s" % nombre_adjunto
    )
    # Y finalmente lo agregamos al mensaje
    mensaje.attach(adjunto_MIME)
    archivo_adjunto.close()

    # creamos servidor
    server = smtplib.SMTP("SMTP", 587)
    # Create context (to specify TLS version)
    sc = ssl.create_default_context()
    sc.set_ciphers("DEFAULT")
    server.starttls(context=sc)

    # Credenciales
    server.login(mensaje["From"], password)

    server.sendmail(mensaje["From"], destinatarios, mensaje.as_string())

    server.quit()


def generar_log(mensaje, resultado):
    now = datetime.now()
    FECHA = now.strftime("%d/%m/%Y %H:%M:%S")
    print(FECHA, " || ", resultado, " || ", mensaje)


print("Script inciado:", FECHA, "\n")

SIZES = []

try:
    print(
        "Respaldos a realizar:\n%s" % json.dumps(RESPALDOS, indent=4, sort_keys=True)
        + "\n"
    )
    for nombre in RESPALDOS:  # Recorro todos los respaldos configurados
        i = 0
        ubicacionZIP = ""
        for destino in RESPALDOS[nombre]["Destino"]:  # Recorro todos los destinos
            try:
                generar_log(nombre + " - " + destino, "Comenzado")
                pathlib.Path(destino + "\\" + nombre).mkdir(parents=True, exist_ok=True)
                pathlib.Path(destino + "\\" + nombre + "\\" + YEAR).mkdir(
                    parents=True, exist_ok=True
                )
                pathlib.Path(destino + "\\" + nombre + "\\" + YEAR + "\\" + MES).mkdir(
                    parents=True, exist_ok=True
                )
                destino = destino + "\\" + nombre + "\\" + YEAR + "\\" + MES
                if i == 0:
                    archivoZIP = zipfile.ZipFile(
                        destino + "\\" + nombre + FECHA_COMP + ".zip", "w"
                    )  # Genero el nuevo ZIP
                    for origen in RESPALDOS[nombre][
                        "Origen"
                    ]:  # Recorro todos los origenes
                        for folder, subfolders, files in os.walk(
                            origen
                        ):  # Recorro el contenido del origen
                            for file in files:  # Recorro todos los archivos
                                try:
                                    archivoZIP.write(
                                        os.path.join(folder, file),
                                        os.path.relpath(
                                            os.path.join(folder, file),
                                            os.path.dirname(origen),
                                        ),
                                        compress_type=zipfile.ZIP_DEFLATED,
                                    )  # Agrego los archivos al ZIP
                                except Exception as e:
                                    generar_log("", "Error")
                                    print(e)
                                    print(traceback.format_exc())
                    archivoZIP.close()  # Cierro la escritura del ZIP
                    zipSize = os.stat(destino + "\\" + nombre + FECHA_COMP + ".zip")
                    ubicacionZIP = destino  # Guardo la ubicacion del primer ZIP de este respaldo para poder copiarlo luego
                    i += 1
                else:
                    shutil.copy2(
                        ubicacionZIP + "\\" + nombre + FECHA_COMP + ".zip", destino
                    )  # Copio el ZIP generado en el primer destino a los demas (para no generar de 0 el ZIP)
                temp = {
                    (nombre + ": " + destino): [
                        "%s %s" % (zipSize.st_size, "Bytes"),
                        "%s %s" % (round(zipSize.st_size / 1024), "KB"),
                        "%s %s" % (round(zipSize.st_size / 1024 / 1024), "MB"),
                        "%s %s" % (round(zipSize.st_size / 1024 / 1024 / 1024), "GB"),
                    ]
                }
                SIZES.append(temp)
                generar_log(nombre + " - " + destino, "Finalizado")
            except Exception as e:
                generar_log("", "Error")
                print(e)
                print(traceback.format_exc())
except Exception as e:
    generar_log("", "Error")
    print(e)
    print(traceback.format_exc())

generar_log("Script", "Finalizado")

sys.stdout.close()
enviar_mail(SIZES)
