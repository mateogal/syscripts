import requests
from pathlib import Path

DOMAIN = "DOMAIN"
RECORDS_ID = ["RECORD_ID"]  # Array of records
SECRET_KEY = "SECRET_KEY"
APIKEY = "API_KEY"

ip = requests.get("https://api.ipify.org").text

f = open(f"{Path.home()}/porkbun.log", "w")

for record in RECORDS_ID:
    url = f"https://api.porkbun.com/api/json/v3/dns/edit/{DOMAIN}/{record}"
    myobj = {
        "secretapikey": f"{SECRET_KEY}",
        "apikey": f"{APIKEY}",
        "type": "A",
        "content": format(ip),
    }
    x = requests.post(url, json=myobj)
    f.write(str(myobj) + "\n")
    f.write(f"{x.status_code} : {x.content} \n")

f.close()
