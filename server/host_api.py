from flask import Blueprint, request, jsonify
import uuid
from utils import load_db, save_db, write_log

host_bp = Blueprint('host', __name__)

@host_bp.route("/api/create_project", methods=["POST"])
def create_project():
    data = request.get_json()
    name = data.get("name")
    if not name:
        return jsonify({"error": "Project name required"}), 400

    db = load_db()
    if name in db["projects"]:
        return jsonify({"error": "Project already exists"}), 409

    new_uuid = str(uuid.uuid4())
    db["projects"][name] = {
        "uuid": new_uuid,
        "files": []
    }

    save_db(db)
    write_log(f"project-created: {name} uuid={new_uuid}")
    return jsonify({"status": "Project created", "uuid": new_uuid}), 200

@host_bp.route("/api/project/<name>", methods=["GET"])
def get_project(name):
    db = load_db()
    return jsonify(db["projects"].get(name, {}))

@host_bp.route("/api/stats", methods=["GET"])
def get_stats():
    db = load_db()
    return jsonify({
        "total_projects": len(db["projects"]),
        "total_uuids": len(db["uuids"]),
        "total_harbors": len(db["harbors"])
    })