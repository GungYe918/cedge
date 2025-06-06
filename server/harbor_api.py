from flask import Blueprint, request, jsonify
from utils import load_db, save_db, write_log

harbor_bp = Blueprint('harbor', __name__)

@harbor_bp.route("/api/register_harbor", methods=["POST"])
def register_harbor():
    data = request.get_json()
    required = ["name", "url", "manage_project"]

    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    db = load_db()

    for harbor in db["harbors"]:
        if harbor["name"] == data["name"]:
            return jsonify({"error": "Harbor with same name already exists"}), 409

    for project in data["manage_project"]:
        if project not in db["projects"]:
            return jsonify({"error": f"Project '{project}' does not exist"}), 404

    for harbor in db["harbors"]:
        for p in harbor.get("manage_project", []):
            if p in data["manage_project"]:
                return jsonify({
                    "error": f"Project '{p}' already managed by another Harbor",
                    "existing_harbor": harbor["name"]
                }), 409

    db["harbors"].append({
        "name": data["name"],
        "url": data["url"],
        "manage_project": data["manage_project"]
    })

    save_db(db)
    write_log(f"harbor-registered: {data['name']} → manages {data['manage_project']}")
    return jsonify({"status": "Harbor registered"}), 200

@harbor_bp.route("/api/register_file", methods=["POST"])
def register_file():
    data = request.get_json()
    required_keys = ["uuid", "project", "harbor_name"]

    if not all(k in data for k in required_keys):
        return jsonify({"error": "Missing required fields"}), 400

    db = load_db()
    uuid_ = data["uuid"]
    project = data["project"]
    harbor_name = data["harbor_name"]
    version = data.get("version", 1)

    if uuid_ in db.get("uuids", {}):
        return jsonify({
            "error": "UUID already registered",
            "uuid": uuid_,
            "registered_project": db["uuids"][uuid_]["project"]
        }), 409

    if project not in db.get("projects", {}):
        return jsonify({"error": "Project does not exist"}), 404

    valid_harbor = any(
        harbor["name"] == harbor_name and project in harbor.get("manage_project", [])
        for harbor in db.get("harbors", [])
    )
    if not valid_harbor:
        return jsonify({"error": "Harbor does not manage this project"}), 403

    db["uuids"][uuid_] = {
        "project": project,
        "harbor_name": harbor_name,
        "version": version
    }

    db["projects"][project]["files"].append(uuid_)
    save_db(db)

    msg = f"file-registration success: uuid={uuid_} project={project} harbor={harbor_name}"
    write_log(msg)
    return jsonify({"status": "File UUID registered"}), 200

@harbor_bp.route("/api/uuid/<uuid_>", methods=["GET"])
def get_uuid_info(uuid_):
    db = load_db()
    return jsonify(db["uuids"].get(uuid_, {}))