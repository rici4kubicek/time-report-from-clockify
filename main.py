import json
from datetime import datetime

import requests
import os
from dotenv import load_dotenv  # type: ignore
from contextlib import redirect_stdout
import csv


load_dotenv()

WORKSPACE_ID = os.getenv("WORKSPACE_ID")
API_KEY = os.getenv("API_KEY")

interval_from = "2024-10-01T00:00:00Z"
interval_to = "2024-10-31T23:59:59Z"

client = "Elekon"

def convert_timestamp(timestamp):
    return datetime.fromisoformat(timestamp).strftime('%d.%m.%Y')

url = f"https://reports.api.clockify.me/v1/workspaces/{WORKSPACE_ID}/reports/detailed"

request_body = {
    "dateRangeEnd": interval_to,
    "dateRangeStart": interval_from,
    "detailedFilter": {
        "options": {
            "totals": "CALCULATE"
        },
        "page": 1,
        "pageSize": 200,
        "sortColumn": "DATE"
    }
}

headers = {
  'X-Api-Key': API_KEY,
  'Content-Type': 'application/json'
}

response = requests.post(url, data=json.dumps(request_body), headers=headers)

if response.status_code != 200:
    print("Error:", response.status_code)

entries = response.json()
entries = entries["timeentries"]
data = list()
for entry in entries:
    if entry["clientName"] != client:
        continue
    _row = {"date": entry["date"], "duration": entry["timeInterval"]["duration"]}
