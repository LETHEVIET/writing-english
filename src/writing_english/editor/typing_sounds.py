from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

_SOUNDS_DIR = Path(__file__).resolve().parent.parent / "resources" / "sounds"


class _SoundPool:
    """Small pool of QSoundEffect instances to allow rapid overlapping playback."""

    def __init__(self, path: Path, volume: float, count: int = 2) -> None:
        self._instances: list[QSoundEffect] = []
        self._next_index = 0
        for _ in range(count):
            snd = QSoundEffect()
            snd.setSource(QUrl.fromLocalFile(str(path)))
            snd.setVolume(volume)
            self._instances.append(snd)

    def play(self) -> None:
        # Try to find an instance that isn't currently playing;
        # fallback to round-robin so we never drop a keystroke.
        for i, snd in enumerate(self._instances):
            if not snd.isPlaying():
                snd.play()
                self._next_index = (i + 1) % len(self._instances)
                return
        snd = self._instances[self._next_index]
        snd.stop()
        snd.play()
        self._next_index = (self._next_index + 1) % len(self._instances)

    def __bool__(self) -> bool:
        return bool(self._instances)


class TypingSoundManager:
    def __init__(self) -> None:
        self._enabled = True
        self._key_sounds: list[_SoundPool] = []
        self._space_pool: _SoundPool | None = None
        self._enter_pool: _SoundPool | None = None
        self._backspace_pool: _SoundPool | None = None
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
        self._space_pool = None
        self._enter_pool = None
        self._backspace_pool = None

        pack_dir = _SOUNDS_DIR / pack_name
        if not pack_dir.exists() or not pack_dir.is_dir():
            return

        self._current_pack = pack_name

        for i in range(5):
            path = pack_dir / f"generic_r{i}.wav"
            if path.exists():
                self._key_sounds.append(_SoundPool(path, 0.5, count=2))

        # Fallback if no generic_rX.wav found: load all wav files
        if not self._key_sounds:
            for path in pack_dir.glob("*.wav"):
                if path.name not in ("space.wav", "enter.wav", "backspace.wav"):
                    self._key_sounds.append(_SoundPool(path, 0.5, count=2))

        space_path = pack_dir / "space.wav"
        if space_path.exists():
            self._space_pool = _SoundPool(space_path, 0.55, count=2)

        enter_path = pack_dir / "enter.wav"
        if enter_path.exists():
            self._enter_pool = _SoundPool(enter_path, 0.55, count=2)

        backspace_path = pack_dir / "backspace.wav"
        if backspace_path.exists():
            self._backspace_pool = _SoundPool(backspace_path, 0.5, count=2)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def play_key(self) -> None:
        if not self._enabled or not self._initialized or not self._key_sounds:
            return
        pool = random.choice(self._key_sounds)
        pool.play()

    def play_space(self) -> None:
        if not self._enabled or not self._initialized or not self._space_pool:
            return
        self._space_pool.play()

    def play_enter(self) -> None:
        if not self._enabled or not self._initialized or not self._enter_pool:
            return
        self._enter_pool.play()

    def play_backspace(self) -> None:
        if not self._enabled or not self._initialized or not self._backspace_pool:
            return
        self._backspace_pool.play()
