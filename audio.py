from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

from settings import ASSETS_DIR, GameSettings

SAMPLE_RATE = 22050


def _write_wav(path: Path, samples: List[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            frames.extend(struct.pack("<h", int(clamped * 32767)))
        wf.writeframes(bytes(frames))


def _synth_notes(
    notes: List[Tuple[float, float, float, str]],
    volume: float = 0.5,
) -> List[float]:
    """Synthesize (freq_start, freq_end, duration_sec, wave_type) sequentially."""
    out: List[float] = []
    for f0, f1, dur, shape in notes:
        n_samples = max(1, int(SAMPLE_RATE * dur))
        phase = 0.0
        for i in range(n_samples):
            t = i / n_samples
            freq = f0 + (f1 - f0) * t
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            if shape == "square":
                val = 1.0 if math.sin(phase) >= 0 else -1.0
            elif shape == "triangle":
                val = 2.0 / math.pi * math.asin(math.sin(phase))
            elif shape == "saw":
                val = 2.0 * ((phase / (2.0 * math.pi)) % 1.0) - 1.0
            else:
                val = math.sin(phase)
            env = min(1.0, i / (SAMPLE_RATE * 0.01)) * max(0.0, 1.0 - t)
            out.append(val * env * volume)
    return out


def ensure_default_audio_assets() -> None:
    """Create original procedural WAV sound effects & music if custom audio files do not exist."""
    sounds_dir = ASSETS_DIR / "sounds"
    music_dir = ASSETS_DIR / "music"

    sfx_recipes: Dict[str, List[Tuple[float, float, float, str]]] = {
        "bone.wav": [(540, 760, 0.08, "triangle")],
        "coin.wav": [(880, 880, 0.07, "sine"), (1174.66, 1174.66, 0.13, "sine")],
        "powerup.wav": [
            (392, 392, 0.08, "square"),
            (493.88, 493.88, 0.08, "square"),
            (587.33, 587.33, 0.08, "square"),
            (783.99, 783.99, 0.16, "triangle"),
        ],
        "scare.wav": [(440, 880, 0.08, "triangle"), (880, 1320, 0.12, "sine")],
        "hit.wav": [(260, 110, 0.18, "saw"), (170, 75, 0.22, "square")],
        "level_complete.wav": [
            (523.25, 523.25, 0.11, "triangle"),
            (659.25, 659.25, 0.11, "triangle"),
            (783.99, 783.99, 0.11, "triangle"),
            (1046.50, 1046.50, 0.24, "sine"),
        ],
        "game_over.wav": [
            (392.0, 370.0, 0.16, "saw"),
            (349.23, 330.0, 0.16, "saw"),
            (311.13, 290.0, 0.16, "saw"),
            (261.63, 220.0, 0.30, "saw"),
        ],
    }

    for filename, recipe in sfx_recipes.items():
        target = sounds_dir / filename
        if not target.exists():
            _write_wav(target, _synth_notes(recipe, volume=0.42))

    bgm_target = music_dir / "bgm.wav"
    if not bgm_target.exists():
        bass = [
            130.81, 130.81, 164.81, 196.0, 174.61, 164.81, 146.83, 196.0,
            130.81, 130.81, 164.81, 196.0, 220.0, 196.0, 164.81, 146.83,
        ]
        lead = [
            523.25, 0.0, 659.25, 587.33, 523.25, 0.0, 392.0, 440.0,
            523.25, 587.33, 659.25, 0.0, 783.99, 659.25, 587.33, 493.88,
        ]
        samples: List[float] = []
        step_dur = 0.21
        n_step = int(SAMPLE_RATE * step_dur)
        for idx in range(len(bass)):
            bf = bass[idx]
            lf = lead[idx]
            for i in range(n_step):
                t = i / n_step
                env = min(1.0, i / (SAMPLE_RATE * 0.015)) * (1.0 - 0.65 * t)
                b_val = (2.0 / math.pi * math.asin(math.sin(2.0 * math.pi * bf * (i / SAMPLE_RATE)))) * 0.22
                l_val = (math.sin(2.0 * math.pi * lf * (i / SAMPLE_RATE)) * 0.18) if lf > 0 else 0.0
                samples.append((b_val + l_val) * env)
        _write_wav(bgm_target, samples)


class AudioManager:
    def __init__(self, settings: GameSettings) -> None:
        self.settings = settings
        self.enabled = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_loaded = False
        self.music_playing = False

        ensure_default_audio_assets()
        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self.enabled = True
        except pygame.error:
            self.enabled = False
            return

        sound_files = {
            "bone": ASSETS_DIR / "sounds" / "bone.wav",
            "coin": ASSETS_DIR / "sounds" / "coin.wav",
            "powerup": ASSETS_DIR / "sounds" / "powerup.wav",
            "scare": ASSETS_DIR / "sounds" / "scare.wav",
            "hit": ASSETS_DIR / "sounds" / "hit.wav",
            "level_complete": ASSETS_DIR / "sounds" / "level_complete.wav",
            "game_over": ASSETS_DIR / "sounds" / "game_over.wav",
        }
        for key, path in sound_files.items():
            if path.exists():
                try:
                    self.sounds[key] = pygame.mixer.Sound(str(path))
                except pygame.error:
                    pass

        bgm_path = ASSETS_DIR / "music" / "bgm.wav"
        if bgm_path.exists():
            try:
                pygame.mixer.music.load(str(bgm_path))
                self.music_loaded = True
            except pygame.error:
                self.music_loaded = False

        self.apply_settings(self.settings)

    def apply_settings(self, settings: GameSettings) -> None:
        self.settings = settings
        if not self.enabled:
            return
        sfx_vol = 0.0 if settings.muted else settings.sound_volume
        music_vol = 0.0 if settings.muted else settings.music_volume
        for snd in self.sounds.values():
            try:
                snd.set_volume(sfx_vol)
            except pygame.error:
                pass
        try:
            pygame.mixer.music.set_volume(music_vol)
        except pygame.error:
            pass

    def play(self, name: str) -> None:
        if not self.enabled or self.settings.muted:
            return
        snd = self.sounds.get(name)
        if snd is not None:
            try:
                snd.play()
            except pygame.error:
                pass

    def start_music(self) -> None:
        if not self.enabled or not self.music_loaded or self.music_playing:
            return
        try:
            pygame.mixer.music.play(-1)
            self.music_playing = True
        except pygame.error:
            pass

    def stop_music(self) -> None:
        if not self.enabled or not self.music_playing:
            return
        try:
            pygame.mixer.music.stop()
            self.music_playing = False
        except pygame.error:
            pass
