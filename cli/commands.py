import os
import json
import hashlib
import time
import difflib

def sha1(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]

def generate_uuid(project, filepath):
    project_uuid = sha1(project)
    file_uuid = sha1(filepath)
    time_uuid = str(int(time.time()))
    return f"{project_uuid}-{file_uuid}-{time_uuid}"

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def get_base_uuid(project, filepath):
    return f"{sha1(project)}-{sha1(filepath)}"

def compute_diffs(old_text, new_text, version):
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    diffs = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            diffs.append({
                "type": "+",
                "version": version,
                "start_l": i1 + 1,
                "end_l": i1 + (j2 - j1),
                "old_l": []
            })
        elif tag == "delete":
            diffs.append({
                "type": "-",
                "version": version,
                "start_l": i1 + 1,
                "end_l": i2,
                "old_l": old_lines[i1:i2]
            })
        elif tag == "replace":
            diffs.append({
                "type": "m",
                "version": version,
                "start_l": i1 + 1,
                "end_l": i2,
                "old_l": old_lines[i1:i2]
            })
    return diffs

def load_diff_metadata(path, fallback_content=""):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"\n⚠️ 손상된 diff 파일 발견: {path}")
        print(f"🔍 오류 내용: {str(e)}")
        answer = input("❓ 덮어쓰시겠습니까? [y/N]: ").strip().lower()
        if answer != 'y':
            print("⛔ 작업을 중단합니다.")
            raise RuntimeError("사용자가 diff 파일 덮어쓰기를 거부했습니다.")
        print("🧹 파일을 덮어씁니다.")

        # fallback_content를 last_content로 저장 (예: 현재 파일에서 읽은 내용)
        repaired = {
            "last_content": fallback_content,
            "diffs": []
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(repaired, f, indent=2)

        return repaired

def save_diff_file(base_uuid, new_diff_entries, new_content=None, root_dir="."):
    """
    base_uuid: 파일의 베이스 uuid
    new_diff_entries: 추가할 diff 리스트
    new_content: 변경 후 최신 파일 전체 내용 (필수!)
    root_dir: 프로젝트 루트(디폴트 ".")
    """
    diff_dir = os.path.join(root_dir, ".cedge", "diff")
    os.makedirs(diff_dir, exist_ok=True)
    path = os.path.join(diff_dir, f"{base_uuid}.json")

    existing_diffs = []
    # last_content는 반드시 new_content를 우선 적용
    last_content = new_content if new_content is not None else ""

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                if isinstance(existing_data, dict):
                    existing_diffs = existing_data.get("diffs", [])
                    # 만약 new_content가 None이면 기존 값 유지
                    if last_content == "":
                        last_content = existing_data.get("last_content", "")
        except Exception:
            print(f"\n⚠️ 손상된 diff 파일 발견: {path}")
            answer = input("덮어쓰시겠습니까? [y/N]: ").strip().lower()
            if answer != 'y':
                print(f"⛔ 파일 무시됨: {base_uuid}.json")
                return  # 중단
            else:
                print(f"🧹 기존 손상된 파일 덮어쓰기 진행")
                existing_diffs = []
                # last_content는 new_content 우선

    # diff 병합 및 저장
    merged_data = {
        "last_content": last_content,
        "diffs": existing_diffs + new_diff_entries
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2)



def get_last_content_from_diff(base_uuid, root_dir="."):
    path = os.path.join(root_dir, ".cedge", "diff", f"{base_uuid}.json")
    # 파일이 손상되었을 경우, 최신 파일 내용을 fallback으로 넘겨줌
    tracked_path = os.path.join(root_dir, ".cedge", "tracked", "tracked.json")
    fallback = ""

    if os.path.exists(tracked_path):
        with open(tracked_path, "r", encoding="utf-8") as f:
            tracked = json.load(f)
        for file in tracked.get("files", []):
            if file["base_uuid"] == base_uuid:
                fallback = read_file(file["filename"])
                break

    data = load_diff_metadata(path, fallback_content=fallback)
    return data.get("last_content", "")


def reconstruct_old_content_from_diffs(last_content, diffs):
    """현재(last_content)에서 diff들을 역으로 적용해 이전 버전 복원"""
    lines = last_content.splitlines()
    for diff in reversed(diffs):
        t = diff["type"]
        start = diff["start_l"] - 1  
        end = diff["end_l"]           
        if t == "+":
            del lines[start:end]
        elif t == "-":
            old_l = diff["old_l"]
            lines[start:start] = old_l
        elif t == "m":
            old_l = diff["old_l"]
            lines[start:end] = old_l
    return "\n".join(lines)


# cli commands

def show_diff_by_file(rel_path, root_dir="."):
    full_path = os.path.join(root_dir, rel_path)

    if not os.path.exists(full_path):
        print(f"❌ 파일이 존재하지 않습니다: {rel_path}")
        return

    project = rel_path.split(os.sep)[0]
    base_uuid = get_base_uuid(project, rel_path)
    diff_path = os.path.join(root_dir, ".cedge", "diff", f"{base_uuid}.json")

    # 파일의 버전 로드
    version = None
    tracked_path = os.path.join(root_dir, ".cedge", "tracked", "tracked.json")
    if os.path.exists(tracked_path):
        with open(tracked_path, "r", encoding="utf-8") as f:
            tracked = json.load(f)
            for entry in tracked.get("files", []):
                if entry["filename"] == rel_path:
                    version = entry["version"]
                    break

    if not os.path.exists(diff_path):
        print(f"❌ diff 기록이 존재하지 않습니다: {diff_path}")
        return

    try:
        with open(diff_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            last_content = data.get("last_content", "")
            diffs = data.get("diffs", [])
    except Exception as e:
        print(f"❌ diff 파일을 읽을 수 없습니다: {e}")
        return

    old_content = reconstruct_old_content_from_diffs(last_content, diffs)
    current_content = read_file(full_path)

    if current_content.strip() == old_content.strip():
        return  # 변경 없음

    # 파일 버전 등 출력
    print(f"\n📄 diff content: {rel_path} (v{version})")
    print("=" * 40)

    old_lines = old_content.splitlines()
    new_lines = current_content.splitlines()

    # git의 diff와 가장 유사하게 보여줌
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"{rel_path} (old)",
        tofile=f"{rel_path} (new)",
        lineterm=""
    )
    print("\n".join(diff))


def show_diff_by_folder(folder_path, root_dir="."):
    tracked_path = os.path.join(root_dir, ".cedge", "tracked", "tracked.json")
    if not os.path.exists(tracked_path):
        print("❌ tracked.json이 존재하지 않습니다.")
        return

    abs_folder = os.path.abspath(folder_path)
    with open(tracked_path, "r", encoding="utf-8") as f:
        tracked = json.load(f)
        for entry in tracked.get("files", []):
            file_path = os.path.abspath(os.path.join(root_dir, entry["filename"]))
            if file_path.startswith(abs_folder):
                show_diff_by_file(entry["filename"], root_dir)

def show_diff_all(root_dir="."):
    tracked_path = os.path.join(root_dir, ".cedge", "tracked", "tracked.json")
    if not os.path.exists(tracked_path):
        print("❌ tracked.json이 존재하지 않습니다.")
        return

    with open(tracked_path, "r", encoding="utf-8") as f:
        tracked = json.load(f)
        for entry in tracked.get("files", []):
            rel_path = entry["filename"]
            show_diff_by_file(rel_path, root_dir)


def register_files(root_dir="."):
    cedge_dir = os.path.join(root_dir, ".cedge", "tracked")
    tracked_path = os.path.join(cedge_dir, "tracked.json")

    if os.path.exists(tracked_path):
        print("❌ 이미 등록된 프로젝트입니다.")
        print("👉 대신 `cedge add .` 명령을 사용하세요.")
        return

    os.makedirs(cedge_dir, exist_ok=True)
    tracked_files = []
    host_node = "http://localhost:9001"

    for project in os.listdir(root_dir):
        project_path = os.path.join(root_dir, project)
        if not os.path.isdir(project_path) or project.startswith("."):
            continue

        for dirpath, _, filenames in os.walk(project_path):
            for fname in filenames:
                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, root_dir)
                base_uuid = get_base_uuid(project, rel_path)
                full_uuid = generate_uuid(project, rel_path)
                mtime = os.path.getmtime(full_path)
                content = read_file(full_path)

                save_diff_file(base_uuid, [], content, root_dir)

                entry = {
                    "uuid": full_uuid,
                    "base_uuid": base_uuid,
                    "project": project,
                    "filename": rel_path,
                    "version": 1,
                    "mtime": mtime
                }

                print(f"📦 등록됨: {rel_path} → {entry['uuid']}")
                tracked_files.append(entry)

    with open(tracked_path, "w", encoding="utf-8") as f:
        json.dump({
            "host_node": host_node,
            "files": tracked_files
        }, f, indent=2)

    print(f"\n✅ 총 {len(tracked_files)}개 파일이 .cedge/tracked/tracked.json에 저장되었습니다.")

def add_files(root_dir="."):
    tracked_path = os.path.join(root_dir, ".cedge", "tracked", "tracked.json")
    if not os.path.exists(tracked_path):
        print("❌ tracked.json이 존재하지 않습니다. 먼저 `cedge register .`를 실행하세요.")
        return

    with open(tracked_path, "r", encoding="utf-8") as f:
        tracked = json.load(f)

    host_node = tracked.get("host_node", "http://localhost:9001")
    old_entries = tracked.get("files", [])
    old_index = {(entry["project"], sha1(entry["filename"])): entry for entry in old_entries}

    changes_made = False

    for project in os.listdir(root_dir):
        project_path = os.path.join(root_dir, project)
        if not os.path.isdir(project_path) or project.startswith("."):
            continue

        for dirpath, _, filenames in os.walk(project_path):
            for fname in filenames:
                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, root_dir)
                file_uuid = sha1(rel_path)
                mtime = os.path.getmtime(full_path)
                key = (project, file_uuid)

                base_uuid = get_base_uuid(project, rel_path)
                new_content = read_file(full_path)

                if key in old_index:
                    entry = old_index[key]
                    if mtime > entry.get("mtime", 0):
                        old_version = entry["version"]
                        # get fallback content for diff recovery
                        fallback_content = read_file(full_path)

                        try:
                            old_content = get_last_content_from_diff(base_uuid, root_dir)
                        except RuntimeError:
                            continue  # 사용자 거절 시 무시

                        # compute and save diffs
                        diffs = compute_diffs(old_content, new_content, old_version + 1)
                        save_diff_file(base_uuid, diffs, new_content, root_dir)

                        # update entry
                        new_uuid = generate_uuid(project, rel_path)
                        entry.update({
                            "uuid": new_uuid,
                            "version": old_version + 1,
                            "mtime": mtime,
                            "filename": rel_path
                        })

                        print(f"🔁 버전 증가: {rel_path} → v{entry['version']}")
                        changes_made = True
                else:
                    # 신규 파일
                    new_uuid = generate_uuid(project, rel_path)
                    save_diff_file(base_uuid, [], new_content, root_dir)

                    new_entry = {
                        "uuid": new_uuid,
                        "base_uuid": base_uuid,
                        "project": project,
                        "filename": rel_path,
                        "version": 1,
                        "mtime": mtime
                    }
                    old_entries.append(new_entry)
                    print(f"🆕 신규 추가: {rel_path}")
                    changes_made = True

    # 최종 반영
    if changes_made:
        with open(tracked_path, "w", encoding="utf-8") as f:
            json.dump({
                "host_node": host_node,
                "files": old_entries
            }, f, indent=2)
        print("\n✅ 변경 사항이 tracked.json에 반영되었습니다.")
    else:
        print("✅ 변경된 파일이 없습니다. tracked.json은 그대로 유지됩니다.")
