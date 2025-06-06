import json
import os
import datetime

DATA_PATH = "host_db.json"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "project_registration_log.txt")

if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w") as f:
        json.dump({"projects": {}, "uuids": {}, "harbors": []}, f)

def write_log(message):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\\n")

def load_db():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DATA_PATH, "w") as f:
        json.dump(db, f, indent=2)
