import json
from datetime import datetime

import requests
import os
from dotenv import load_dotenv  # type: ignore
from contextlib import redirect_stdout
import csv
import sys
import pandas as pd

load_dotenv()

WORKSPACE_ID = os.getenv("WORKSPACE_ID")
API_KEY = os.getenv("API_KEY")

interval_from = "2024-10-01T00:00:00Z"
interval_to = "2024-10-31T23:59:59Z"

client = "Elekon"

def convert_timestamp(timestamp):
    return datetime.fromisoformat(timestamp).strftime('%d.%m.%Y')

def duration_to_hours(duration: int) -> float:
    return duration / 3600

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
    _row = {"date": convert_timestamp(entry["timeInterval"]["start"]), "duration": entry["timeInterval"]["duration"],
            "description": entry["description"], "project": entry["projectName"]}
    data.append(_row)

df = pd.DataFrame(data)

grouped_df = df.groupby(['date', 'description', 'project'], as_index=False).agg({'duration': 'sum'})

with redirect_stdout(sys.stdout) as csv_output:
    writer = csv.writer(csv_output,)
    writer.writerow(['Datum', 'Popis (Projekt a úkol)', 'Odpracovaný čas'])

    for index, row in grouped_df.iterrows():
        writer.writerow([row["date"], row["description"], row["duration"]])
