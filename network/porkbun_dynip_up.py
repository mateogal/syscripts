# PORKBUN DOMAIN/RECORD UPDATE API HAS SOME TROUBLES WITH WILDCARD SO WE NEED TO REMOVE AND RE-CREATE RECORDS
# MAYBE IN THE FUTURE THIS GONNA CHANGE

import requests
from pathlib import Path

DOMAIN = "example.com"  # Domain name
RECORDS_NAME = ["*.example.com", "example.com"]  # Array of records names to delete
RECORDS_TYPE = ["A"]  # Array of records types to delete

NEW_RECORDS = [
    {
        "type": "A",
        "name": "*"
    },
    {
        "type": "A",
        "name": ""  # Empty for root domain record
    }
]  # Array of new records to create

RECORDS = []  # Leave it empty
SECRET_KEY = ""  # Your secret api key
API_KEY = ""  # Your api key
API_URL = "https://api.porkbun.com/api/json/v3"  # Porkbun API URL

ip = requests.get("https://api.ipify.org").text  # Current Public IP Addr

f = open(f"{Path.home()}/porkbun.log", "w")  # Logs


def getRecords():
    getURL = f"{API_URL}/dns/retrieve/{DOMAIN}"
    myobj = {"secretapikey": f"{SECRET_KEY}", "apikey": f"{API_KEY}"}
    x = requests.post(getURL, json=myobj)
    response = x.json()
    records = response["records"]
    for record in records:
        if record["name"] in RECORDS_NAME and record["type"] in RECORDS_TYPE and record["content"] != format(ip):
            RECORDS.append(record)
    f.write(f"Records found: {RECORDS} \n")

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
        }
        x = requests.post(createURL, json=myobj)
        f.write(f"API Request: {x.status_code} : {x.text} \n")

getRecords()
if len(RECORDS) > 0:
    deleteRecords()
    createRecords()
else:
    f.write(f"No need update \n")
f.close()
