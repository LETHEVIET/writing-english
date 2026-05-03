from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

_SOUNDS_DIR = Path(__file__).resolve().parent.parent / "resources" / "sounds"


class TypingSoundManager:
    def __init__(self) -> None:
        self._enabled = True
        self._key_sounds: list[QSoundEffect] = []
        self._space_sound: QSoundEffect | None = None
        self._enter_sound: QSoundEffect | None = None
        self._backspace_sound: QSoundEffect | None = None
        self._current_index = 0
        self._initialized = False
        self._current_pack: str | None = None

    def initialize(self, pack_name: str | None = None) -> None:
        if self._initialized:
            return
        
        if pack_name:
            self.change_pack(pack_name)
        self._initialized = True

    def change_pack(self, pack_name: str) -> None:
        if pack_name == self._current_pack:
            return
            
        self._key_sounds.clear()
        self._space_sound = None
        self._enter_sound = None
        self._backspace_sound = None
        self._current_index = 0

        pack_dir = _SOUNDS_DIR / pack_name
        if not pack_dir.exists() or not pack_dir.is_dir():
            return
            
        self._current_pack = pack_name

        for i in range(5):
            path = pack_dir / f"generic_r{i}.wav"
            if path.exists():
                snd = QSoundEffect()
                snd.setSource(QUrl.fromLocalFile(str(path)))
                snd.setVolume(0.5)
                self._key_sounds.append(snd)

        # Fallback if no generic_rX.wav found: load all wav files
        if not self._key_sounds:
            for path in pack_dir.glob("*.wav"):
                if path.name not in ("space.wav", "enter.wav", "backspace.wav"):
                    snd = QSoundEffect()
                    snd.setSource(QUrl.fromLocalFile(str(path)))
                    snd.setVolume(0.5)
                    self._key_sounds.append(snd)

        space_path = pack_dir / "space.wav"
        if space_path.exists():
            self._space_sound = QSoundEffect()
            self._space_sound.setSource(QUrl.fromLocalFile(str(space_path)))
            self._space_sound.setVolume(0.55)

        enter_path = pack_dir / "enter.wav"
        if enter_path.exists():
            self._enter_sound = QSoundEffect()
            self._enter_sound.setSource(QUrl.fromLocalFile(str(enter_path)))
            self._enter_sound.setVolume(0.55)

        backspace_path = pack_dir / "backspace.wav"
        if backspace_path.exists():
            self._backspace_sound = QSoundEffect()
            self._backspace_sound.setSource(QUrl.fromLocalFile(str(backspace_path)))
            self._backspace_sound.setVolume(0.5)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def play_key(self) -> None:
        if not self._enabled or not self._initialized or not self._key_sounds:
            return
        snd = self._key_sounds[self._current_index % len(self._key_sounds)]
        self._current_index = (self._current_index + 1) % len(self._key_sounds)
        snd.play()

    def play_space(self) -> None:
        if not self._enabled or not self._initialized or not self._space_sound:
            return
        self._space_sound.play()

    def play_enter(self) -> None:
        if not self._enabled or not self._initialized or not self._enter_sound:
            return
        self._enter_sound.play()

    def play_backspace(self) -> None:
        if not self._enabled or not self._initialized or not self._backspace_sound:
            return
        self._backspace_sound.play()