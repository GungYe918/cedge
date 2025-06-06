# server/host_server.py
from flask import Flask, request, jsonify
import datetime
import uuid
import json
import os

app = Flask(__name__)
DATA_PATH = "host_db.json"

if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w") as f:
        json.dump({"projects": {}, "uuids": {}}, f)

# 로그 기능 구현
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "project_registration_log.txt")

def write_log(message):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def load_db():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DATA_PATH, "w") as f:
        json.dump(db, f, indent=2)

@app.route("/api/register", methods=["POST"])
def register_uuid():
    data = request.get_json()
    db = load_db()

    uuid_ = data["uuid"]
    project = data["project"]
    host_node = data["host_node"]
    version = data.get("version", 1)

    # 중복 UUID 검사
    if uuid_ in db.get("uuids", {}):
        existing_project = db["uuids"][uuid_]["project"]
        if existing_project != project:
            msg = f"project-registration failed (conflict): uuid={uuid_} already-exsist={existing_project}, requested={project}"
            write_log(msg)
            return jsonify({
                "error": "UUID already registered in another project",
                "uuid": uuid_,
                "existing_project": existing_project,
                "requested_project": project
            }), 409  # Conflict

    # uuid 등록
    db.setdefault("uuids", {})[uuid_] = {
        "project": project,
        "host_node": host_node,
        "version": version
    }

    # 프로젝트 등록
    db.setdefault("projects", {}).setdefault(project, [])
    if uuid_ not in db["projects"][project]:
        db["projects"][project].append(uuid_)

    save_db(db)

    msg = f"project-registration success: uuid={uuid_} project={project}"
    write_log(msg)
    return jsonify({"status": "ok"}), 200

@app.route("/api/project/<name>", methods=["GET"])
def get_project_uuids(name):
    db = load_db()
    return jsonify(db["projects"].get(name, []))

@app.route("/api/uuid/<uuid_>", methods=["GET"])
def get_uuid_info(uuid_):
    db = load_db()
    return jsonify(db["uuids"].get(uuid_, {}))

if __name__ == "__main__":
    print("🔗 CEDGE Host 서버 실행 중... (http://localhost:8000)")
    app.run(host="0.0.0.0", port=8000)
