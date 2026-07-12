import os
import json
import threading
from dataclasses import dataclass, asdict


@dataclass
class Config:
    trigger_key: str = "shift"
    delay_min: float = 0.01
    delay_max: float = 0.03
    hold_min: float = 0.01
    hold_max: float = 0.05
    check_team: bool = True
    enabled: bool = True


class SettingsManager:
    def __init__(self, path="config.json"):
        self.path = path
        self.lock = threading.Lock()
        self.config = self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})
            except Exception as e:
                print(f"[-] Failed to load config: {e}")
                try:
                    backup = self.path + ".bak"
                    os.replace(self.path, backup)
                    print(f"[-] Corrupted config moved to {backup}")
                except Exception:
                    pass
        return Config()

    def save(self):
        with self.lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(asdict(self.config), f, indent=4)
            except Exception as e:
                print(f"[-] Failed to save config: {e}")

    def get(self):
        with self.lock:
            return Config(**asdict(self.config))

    def set(self, **kwargs):
        with self.lock:
            for k, v in kwargs.items():
                if k in Config.__dataclass_fields__:
                    setattr(self.config, k, v)
