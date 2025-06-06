# cli/main.py
import argparse
import subprocess
from commands import register_files, add_files, show_diff_by_file, show_diff_by_folder, show_diff_all
import os

def run_host() :
    subprocess.run(["python", "server/host_server.py"])

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description="CEDGE CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # cedge host
    subparsers.add_parser("host", help="Run as central Host")

    # cedge register [path]
    register_parser = subparsers.add_parser("register", help="Register project files")
    register_parser.add_argument("path", nargs="?", default=".", help="Path to project root (default: .)")

    # cedge add [path]
    add_parser = subparsers.add_parser("add", help="Add or update tracked files")
    add_parser.add_argument("path", nargs="?", default=".")

    # cedge show diff [file|folder|.]
    show_parser = subparsers.add_parser("show", help="Show info or diff")
    show_subparsers = show_parser.add_subparsers(dest="subcommand", required=True)

    show_diff_parser = show_subparsers.add_parser("diff", help="Show diff of files")
    show_diff_parser.add_argument("path", help="File, folder, or '.' for all")
    



    # TODO: cedge push --host http://localhost:8000

    args = parser.parse_args()

    if args.command == "host":
        run_host()

    elif args.command == "register":
        abs_path = os.path.abspath(args.path)
        register_files(abs_path)

    elif args.command == "add" :
        add_files(args.path)

    elif args.command == "show" and args.subcommand == "diff":
        show_path = os.path.abspath(args.path)
        if args.path == ".":
            show_diff_all(".")
        elif os.path.isfile(show_path):
            show_diff_by_file(args.path)
        elif os.path.isdir(show_path):
            show_diff_by_folder(args.path)
        else:
            print(f"❌ 파일 또는 폴더를 찾을 수 없습니다: {args.path}")
