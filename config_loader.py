# config_loader.py
import json
import pathlib

CONFIG_PATH = pathlib.Path("config.json")


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


config = load_config()
