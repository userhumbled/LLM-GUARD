import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from guard_server import GuardPipeline, build_guard_interface, start_server, get_pipeline, analyze_input

ProcPipeline = GuardPipeline
build_ui = build_guard_interface
run_server = start_server

if __name__ == "__main__":
    start_server()
