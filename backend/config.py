import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config

def get_huggingface_config():
    return load_config().get("huggingface", {})

def get_local_storage_config():
    return load_config().get("local_storage", {})
