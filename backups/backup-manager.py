import os
import shutil
import tarfile
import zipfile
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import platform
import ssl
import json
from datetime import datetime

client_name = ""
backups = {
    "BkpName1": {
        "src": [
            "/source1/test.bak",
            "/source1/Test",
        ],
        "dst": [
            "/netdst/Test",
            "/dst1/Test",
        ],
    },
    "BkpName2": {
        "src": [
            "/source2/Pictures",
        ],
        "dst": [
            "/netdst2/Pictures",
            "/dst12/Pictures",
        ],
    },
}
log_file = "/logs/backup/log"
influxdb_config = {
    "url": "",
    "bucket": "",
    "token": "",
    "org": "",
}
email_config = {
    "server": "",
    "port": 465,
    "username": "",
    "password": "",
    "to": "",
}
email_body = []

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)


def human_readable_size(size_in_bytes):
    units = ["Bytes", "KB", "MB", "GB", "TB"]

    if size_in_bytes == 0:
        return "0 Bytes"

    index = 0
    while size_in_bytes >= 1024 and index < len(units) - 1:
        size_in_bytes /= 1024.0
        index += 1

    return f"{size_in_bytes:.2f} {units[index]}"


def compress_backup(src, dest, name):
    backup_name = os.path.join(dest, name)
    os.makedirs(backup_name, exist_ok=True)
    status = "ok"
    if os.name == "nt":
        zip_path = os.path.join(
            backup_name, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        )
        if os.path.isdir(src):
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(src):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            zipf.write(file_path, os.path.relpath(file_path, src))
                        except Exception as e:
                            logging.warning(f"Compress error {file_path}: {e}")
                            status = "Failed to compress some files. Check logs for more information."
        else:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                try:
                    zipf.write(src, os.path.basename(src))
                except Exception as e:
                    logging.warning(f"Compress error {src}: {e}")
                    status = (
                        "Failed to compress the file. Check logs for more information."
                    )
        return zip_path, status
    else:
        tar_path = f"{backup_name}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            try:
                tar.add(src, arcname=os.path.basename(src))
            except Exception as e:
                logging.warning(f"Compress error {src}: {e}")
                status = "warning"
        return tar_path, status


def get_free_space(path):
    total, used, free = shutil.disk_usage(path)
    return free


def calculate_history_limit(dest, backup_size):
    free_space = get_free_space(dest)
    logging.info(f"{dest} free space = {human_readable_size(free_space)}")
    return max(2, free_space // backup_size)  # Maintain free space for almost 2 backups


def manage_history(dest, backup_size):
    backups = sorted(
        [f for f in os.listdir(dest) if f.startswith("backup_")], reverse=True
    )
    history_limit = calculate_history_limit(dest, backup_size)
    while len(backups) > history_limit:
        oldest_backup = os.path.join(dest, backups.pop())
        os.remove(oldest_backup)
        logging.info(f"Removing oldest backup: {oldest_backup}")
    return get_free_space(dest)


def send_email(subject, message):
    msg = MIMEMultipart()
    msg["From"] = email_config["username"]
    msg["To"] = email_config["to"]
    msg["Subject"] = subject

    body = json.dumps(message, indent=4, sort_keys=True)
    msg.attach(MIMEText(body, "plain"))
    filename = log_file
    attachment = open(filename, "rb")
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename= {filename}")
    msg.attach(part)

    try:
        context = ssl.create_default_context()
        context.set_ciphers("DEFAULT")
        text = msg.as_string()
        with smtplib.SMTP_SSL(
            email_config["server"], email_config["port"], context=context
        ) as server:
            server.login(email_config["username"], email_config["password"])
            server.sendmail(
                email_config["username"],
                email_config["to"],
                text,
            )
        logging.info("Notification email delivered.")
    except Exception as e:
        logging.error(f"Send email error: {e}")


def send_to_influx(size, src, dest, status, host, log, final_free_space):
    try:
        client = influxdb_client.InfluxDBClient(
            url=influxdb_config["url"],
            token=influxdb_config["token"],
            org=influxdb_config["org"],
        )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        point = [
            {
                "measurement": "backups",
                "fields": {"size": size},
                "tags": {
                    "src": src,
                    "level": status,
                    "host": host,
                    "dest": dest,
                    "log": log,
                    "client": client_name,
                    "final_free_space": final_free_space,
                },
            }
        ]
        write_api.write(
            bucket=influxdb_config["bucket"], org=influxdb_config["org"], record=point
        )
        logging.info("Data to InfluxDB sent successfully.")
    except Exception as e:
        logging.error(f"Send InfluxDB data error: {e}")


def main():
    logging.info("Starting backup...")
    for bkp in backups:
        for src in backups[bkp]["src"]:
            for dest in backups[bkp]["dst"]:
                try:
                    backup_path, status = compress_backup(src, dest, bkp)
                    level = "info" if (status == "ok") else "warning"
                    size = os.path.getsize(backup_path)
                    logging.info(
                        f"Backup finished: {backup_path}, Size: {human_readable_size(size)}"
                    )
                    final_free_space = manage_history(dest, size)
                    send_to_influx(
                        size,
                        src,
                        dest,
                        level,
                        platform.node(),
                        status,
                        final_free_space,
                    )
                    email_body.append(
                        f"Backup generated on {backup_path} with size {human_readable_size(size)}."
                    )
                except Exception as e:
                    logging.info(f"Backup failed: {dest}, Error: {e}")
                    send_to_influx(0, src, dest, "error", platform.node(), e)
                    email_body.append(f"Backup failed: {src} -> {dest} with error {e}.")
    send_email(
        f"Backup finished on {client_name} / {platform.node()}",
        email_body,
    )


if __name__ == "__main__":
    main()
