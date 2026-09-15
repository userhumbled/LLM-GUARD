import os
import subprocess
import sys


def install_deps():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    cmd = [sys.executable, "-m", "pip", "install", "-r", req_path]
    subprocess.check_call(cmd)


def main():
    install_deps()
    server_path = os.path.join(os.path.dirname(__file__), "guard_server.py")
    subprocess.check_call([sys.executable, server_path])


if __name__ == "__main__":
    main()
