from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
HIGHSCORE_FILE = DATA_DIR / "highscore.json"

TILE_SIZE = 40
HUD_HEIGHT = 64

RESOLUTION_PRESETS: List[Tuple[int, int]] = [
    (960, 640),
    (1120, 720),
    (1280, 800),
    (1440, 900),
]

FPS_OPTIONS: List[int] = [30, 60, 120]
CAMERA_MODES: List[str] = ["auto", "fixed", "follow"]
GRAPHICS_QUALITIES: List[str] = ["high", "classic"]

# Original moonlit hedge-and-cobblestone color palette
COLORS = {
    "bg_dark": (9, 15, 29),
    "bg_mid": (15, 23, 42),
    "floor_a": (23, 35, 59),
    "floor_b": (20, 31, 53),
    "floor_grid": (34, 49, 78),
    "wall_base": (20, 83, 45),
    "wall_top": (22, 101, 52),
    "wall_highlight": (21, 128, 61),
    "wall_edge": (34, 197, 94),
    "hud_bg": (15, 23, 42),
    "hud_border": (30, 41, 59),
    "panel_bg": (15, 23, 42),
    "panel_card": (22, 33, 56),
    "panel_border": (51, 65, 85),
    "text_primary": (241, 245, 249),
    "text_muted": (148, 163, 184),
    "accent": (245, 158, 11),
    "accent_hover": (251, 191, 36),
    "accent_dark": (146, 64, 14),
    "success": (16, 185, 129),
    "danger": (239, 68, 68),
    "info": (56, 189, 248),
}


def default_key_bindings() -> Dict[str, List[int]]:
    return {
        "up": [pygame.K_UP, pygame.K_w],
        "down": [pygame.K_DOWN, pygame.K_s],
        "left": [pygame.K_LEFT, pygame.K_a],
        "right": [pygame.K_RIGHT, pygame.K_d],
        "pause": [pygame.K_ESCAPE, pygame.K_p],
        "full_view": [pygame.K_v],
        "mute": [pygame.K_m],
    }


@dataclass
class GameSettings:
    resolution_index: int = 1  # Default 1120x720
    fullscreen: bool = False
    fps_limit: int = 60
    sound_volume: float = 0.75
    music_volume: float = 0.45
    muted: bool = False
    camera_mode: str = "auto"  # "auto" | "fixed" | "follow"
    camera_zoom: float = 1.15
    camera_shake: bool = True
    camera_dead_zone: bool = True
    camera_look_ahead: bool = True
    graphics_quality: str = "high"  # "high" | "classic"
    key_bindings: Dict[str, List[int]] = field(default_factory=default_key_bindings)

    @property
    def resolution(self) -> Tuple[int, int]:
        idx = max(0, min(len(RESOLUTION_PRESETS) - 1, self.resolution_index))
        return RESOLUTION_PRESETS[idx]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict) -> "GameSettings":
        defaults = cls()
        kb = default_key_bindings()
        raw_kb = raw.get("key_bindings", {})
        if isinstance(raw_kb, dict):
            for action, keys in raw_kb.items():
                if action in kb and isinstance(keys, list) and all(isinstance(k, int) for k in keys):
                    kb[action] = keys

        return cls(
            resolution_index=int(raw.get("resolution_index", defaults.resolution_index)),
            fullscreen=bool(raw.get("fullscreen", defaults.fullscreen)),
            fps_limit=int(raw.get("fps_limit", defaults.fps_limit))
            if int(raw.get("fps_limit", defaults.fps_limit)) in FPS_OPTIONS
            else defaults.fps_limit,
            sound_volume=max(0.0, min(1.0, float(raw.get("sound_volume", defaults.sound_volume)))),
            music_volume=max(0.0, min(1.0, float(raw.get("music_volume", defaults.music_volume)))),
            muted=bool(raw.get("muted", defaults.muted)),
            camera_mode=raw.get("camera_mode", defaults.camera_mode)
            if raw.get("camera_mode") in CAMERA_MODES
            else defaults.camera_mode,
            camera_zoom=max(0.75, min(1.5, float(raw.get("camera_zoom", defaults.camera_zoom)))),
            camera_shake=bool(raw.get("camera_shake", defaults.camera_shake)),
            camera_dead_zone=bool(raw.get("camera_dead_zone", defaults.camera_dead_zone)),
            camera_look_ahead=bool(raw.get("camera_look_ahead", defaults.camera_look_ahead)),
            graphics_quality=raw.get("graphics_quality", defaults.graphics_quality)
            if raw.get("graphics_quality") in GRAPHICS_QUALITIES
            else defaults.graphics_quality,
            key_bindings=kb,
        )


@dataclass
class HighScoreData:
    high_score: int = 0
    best_level: int = 1
    total_bones_collected: int = 0
    total_coins_collected: int = 0


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> GameSettings:
    ensure_data_dir()
    if not SETTINGS_FILE.exists():
        settings = GameSettings()
        save_settings(settings)
        return settings
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return GameSettings.from_dict(data)
    except (OSError, ValueError, TypeError):
        return GameSettings()


def save_settings(settings: GameSettings) -> None:
    ensure_data_dir()
    try:
        with SETTINGS_FILE.open("w", encoding="utf-8") as fh:
            json.dump(settings.to_dict(), fh, indent=2)
    except OSError:
        pass


def load_highscore() -> HighScoreData:
    ensure_data_dir()
    if not HIGHSCORE_FILE.exists():
        hs = HighScoreData()
        save_highscore(hs)
        return hs
    try:
        with HIGHSCORE_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return HighScoreData(
            high_score=int(data.get("high_score", 0)),
            best_level=max(1, int(data.get("best_level", 1))),
            total_bones_collected=int(data.get("total_bones_collected", 0)),
            total_coins_collected=int(data.get("total_coins_collected", 0)),
        )
    except (OSError, ValueError, TypeError):
        return HighScoreData()


def save_highscore(data: HighScoreData) -> None:
    ensure_data_dir()
    try:
        with HIGHSCORE_FILE.open("w", encoding="utf-8") as fh:
            json.dump(asdict(data), fh, indent=2)
    except OSError:
        pass


def load_optional_sprite(path: Path, size: Optional[Tuple[int, int]] = None) -> Optional[pygame.Surface]:
    """Load an external replacement image asset if present; return None gracefully otherwise."""
    if not path.exists():
        return None
    try:
        img = pygame.image.load(str(path)).convert_alpha()
        if size is not None:
            img = pygame.transform.smoothscale(img, size)
        return img
    except (pygame.error, OSError):
        return None
