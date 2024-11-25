import yaml
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent.parent / 'config.yaml'
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config from {config_path}: {e}")
        raise 