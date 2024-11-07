from jinja2 import Environment, FileSystemLoader
import pdfkit
import json
from datetime import datetime
import requests
import os
from dotenv import load_dotenv  # type: ignore
from contextlib import redirect_stdout
import csv
import sys
import pandas as pd
from os.path import join, basename, exists
from os import mkdir

TARGETDIR = "dist/"

load_dotenv()

WORKSPACE_ID = os.getenv("WORKSPACE_ID")
API_KEY = os.getenv("API_KEY")

interval_from = "2024-10-01T00:00:00Z"
interval_to = "2024-10-31T23:59:59Z"

client = "Elekon"

def convert_timestamp(timestamp):
    return datetime.fromisoformat(timestamp).strftime('%d.%m.%Y')

def duration_to_hours(duration: int) -> float:
    hours = duration / 3600
    hours = round(hours * 4) / 4
    return hours

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
output_data = list()
for entry in entries:
    if entry["clientName"] != client:
        continue
    _row = {"date": convert_timestamp(entry["timeInterval"]["start"]), "duration": entry["timeInterval"]["duration"],
            "description": entry["description"], "project": entry["projectName"]}
    data.append(_row)

df = pd.DataFrame(data)

grouped_df = df.groupby(['date', 'description', 'project'], as_index=False).agg({'duration': 'sum'})

duration_sum = 0

with redirect_stdout(sys.stdout) as csv_output:
    writer = csv.writer(csv_output,)
    writer.writerow(['Datum', 'Popis (Projekt a úkol)', 'Odpracovaný čas [h]'])

    for index, row in grouped_df.iterrows():
        row["duration"] = duration_to_hours(row["duration"])
        writer.writerow([row["date"], row["description"], row["duration"]])
        duration_sum += row["duration"]
        output_data.append(row)

if not exists(TARGETDIR):
    mkdir(TARGETDIR)

# Load the template from file
file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader)
template = env.get_template('template.html')

# Define a macro
output = template.render(entries=output_data, duration_sum=duration_sum)

with open(f'{TARGETDIR}/result.html', 'w') as res:
    res.write(output)

pdfkit.from_string(output, output_path=f'{TARGETDIR}/odpracovany_cas.pdf')
