from PySide6.QtCore import QSettings
from pathlib import Path

settings_path = Path.home() / ".local" / "share" / "writing_english" / "settings.ini"
settings_path.parent.mkdir(parents=True, exist_ok=True)

s = QSettings(str(settings_path), QSettings.Format.IniFormat)
s.setValue("rewards/sticker_rewards", True)
s.setValue("rewards/sticker_folder", "/tmp/stickers")
s.sync()

print(f"Saved to {settings_path}")
