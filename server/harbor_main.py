import os
import json
import argparse
import uuid
import requests

# 🔧 Harbor 로컬 정보 저장 경로
HARBOR_DIR = os.path.join(".cedge", "harbor")
HARBOR_DB = os.path.join(HARBOR_DIR, "harbor_db.json")
HOST_URL = "http://localhost:8000"

# 🔧 로컬 Harbor DB 초기화
def ensure_harbor_db():
    if not os.path.exists(HARBOR_DIR):
        os.makedirs(HARBOR_DIR)
    if not os.path.exists(HARBOR_DB):
        with open(HARBOR_DB, "w") as f:
            json.dump({"project": "", "harbor_name": "", "registered_files": {}}, f)

def load_harbor_db():
    ensure_harbor_db()
    with open(HARBOR_DB, "r") as f:
        return json.load(f)

def save_harbor_db(db):
    with open(HARBOR_DB, "w") as f:
        json.dump(db, f, indent=2)

# 🔧 Harbor 초기 등록 (host에 관리자로 등록됨)
def init_harbor(project, harbor_name, url="http://localhost:9000"):
    db = load_harbor_db()
    db["project"] = project
    db["harbor_name"] = harbor_name
    db["registered_files"] = {}
    save_harbor_db(db)

    # host에 등록 요청
    res = requests.post(f"{HOST_URL}/api/register_harbor", json={
        "name": harbor_name,
        "url": url,
        "manage_project": [project]
    })
    print(f"[HOST RESPONSE] {res.status_code}: {res.text}")

# 🔧 파일 등록
def register_file(filepath):
    db = load_harbor_db()
    project = db.get("project")
    harbor_name = db.get("harbor_name")

    if not project or not harbor_name:
        print("❌ harbor is not initialized. Run `init` first.")
        return

    abs_path = os.path.abspath(filepath)
    if abs_path in db["registered_files"]:
        print(f"⚠️  File already registered: {filepath}")
        return

    file_uuid = str(uuid.uuid4())
    db["registered_files"][abs_path] = {
        "uuid": file_uuid,
        "filename": os.path.basename(filepath)
    }
    save_harbor_db(db)

    # host에 uuid 등록 요청
    res = requests.post(f"{HOST_URL}/api/register_file", json={
        "uuid": file_uuid,
        "project": project,
        "harbor_name": harbor_name
    })

    if res.status_code == 200:
        print(f"✅ Registered: {filepath} → UUID: {file_uuid}")
    else:
        print(f"❌ Failed to register with host: {res.status_code}, {res.text}")

# ✨ CLI
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--project", required=True)
    init_parser.add_argument("--name", required=True)
    init_parser.add_argument("--url", default="http://localhost:9000")

    register_parser = subparsers.add_parser("register-file")
    register_parser.add_argument("filepath")

    args = parser.parse_args()

    if args.command == "init":
        init_harbor(args.project, args.name, args.url)
    elif args.command == "register-file":
        register_file(args.filepath)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()