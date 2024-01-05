import os

def get_repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
