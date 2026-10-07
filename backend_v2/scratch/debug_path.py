import os
import sys

def get_backend_root():
    # Simulate the logic in src/core/utils.py
    # Assuming this script is in backend_v2/test_root.py
    # But utils.py is in backend_v2/src/core/utils.py
    # So depth is 3 levels: core -> src -> root
    # If I run it from here, I should adjust.
    return os.path.dirname(os.path.abspath(__file__))

print(f"Current file: {os.path.abspath(__file__)}")
print(f"Backend root: {get_backend_root()}")
print(f"Join: {os.path.join(get_backend_root(), 'resources/label_templates', 'carton_base.btw')}")
