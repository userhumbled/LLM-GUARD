import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from deberta_tox_models import DebertaToxEngine, get_compute_device, resolve_model_path

TechModell = DebertaToxEngine
get_universal_device = get_compute_device
resolve_mod_path = resolve_model_path
