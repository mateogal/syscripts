# This script is part of (https://github.com/mateogal/Syscripts)
# PORKBUN DOMAIN/RECORD UPDATE API HAS SOME TROUBLES WITH WILDCARD SO WE NEED TO REMOVE AND RE-CREATE RECORDS
# MAYBE IN THE FUTURE THIS GONNA CHANGE

import requests
from pathlib import Path
from datetime import datetime

DOMAIN = "example.com"  # Domain name
RECORDS_NAME = ["*.example.com", "example.com"]  # Array of records names to delete
RECORDS_TYPE = ["A"]  # Array of records types to delete
now = (datetime.now()).strftime("%d/%m/%Y %H:%M:%S")

NEW_RECORDS = [
    {"type": "A", "name": "*", f"notes": "Updated at {now}"},
    {
        "type": "A",
        "name": "",  # Empty for root domain record
        f"notes": "Updated at {now}",  # Optional text
    },
]  # Array of new records to create

RECORDS = []  # Leave it empty
SECRET_KEY = ""  # Your secret api key
API_KEY = ""  # Your api key
API_URL = "https://api.porkbun.com/api/json/v3"  # Porkbun API URL

ip = requests.get("https://api.ipify.org").text  # Current Public IP Addr

f = open(f"{Path.home()}/porkbun.log", "w")  # Logs
f.write(f"Started {now} \n")


def getRecords():
    recCount = 0
    getURL = f"{API_URL}/dns/retrieve/{DOMAIN}"
    myobj = {"secretapikey": f"{SECRET_KEY}", "apikey": f"{API_KEY}"}
    x = requests.post(getURL, json=myobj)
    response = x.json()
    records = response["records"]
    for record in records:
        if record["name"] in RECORDS_NAME and record["type"] in RECORDS_TYPE:
            if record["content"] != format(ip):
                RECORDS.append(record)
            recCount += 1

    f.write(f"Current matched records count: {recCount} \n")
    f.write(f"Records to update: {RECORDS} \n")
    return recCount


def deleteRecords():
    for record in RECORDS:
        f.write(f"Deleting {record['id']} / {record['type']} / {record['name']} \n")
        deleteUrl = f"{API_URL}/dns/delete/{DOMAIN}/{record['id']}"
        myobj = {"secretapikey": f"{SECRET_KEY}", "apikey": f"{API_KEY}"}
        x = requests.post(deleteUrl, json=myobj)
        f.write(f"API Request: {x.status_code} : {x.text} \n")


def createRecords():
    for record in NEW_RECORDS:
        f.write(f"Creating {record['type']} / {record['name']} \n")
        createURL = f"{API_URL}/dns/create/{DOMAIN}"
        myobj = {
            "secretapikey": f"{SECRET_KEY}",
            "apikey": f"{API_KEY}",
            "type": record["type"],
            "name": record["name"],
            "content": format(ip),
            "notes": record["notes"],
        }
        x = requests.post(createURL, json=myobj)
        f.write(f"API Request: {x.status_code} : {x.text} \n")


recCount = getRecords()
if (
    len(RECORDS) > 0 or recCount == 0
):  # If current records = 0 (recCount) create new records anyway
    deleteRecords()
    createRecords()
else:
    f.write(f"No update needed. \n")
f.close()
