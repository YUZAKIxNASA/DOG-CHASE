from __future__ import annotations

from typing import Callable, Dict, List, Optional

import pygame

from settings import (
    CAMERA_MODES,
    COLORS,
    FPS_OPTIONS,
    GRAPHICS_QUALITIES,
    GameSettings,
    HighScoreData,
    RESOLUTION_PRESETS,
    default_key_bindings,
)
from ui import UIButton


def key_label(code: int) -> str:
    return pygame.key.name(code).upper()


class MainMenuScreen:
    def __init__(
        self,
        on_play: Callable[[], None],
        on_how_to_play: Callable[[], None],
        on_settings: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        self.on_play = on_play
        self.on_how_to_play = on_how_to_play
        self.on_settings = on_settings
        self.on_exit = on_exit
        self.buttons: List[UIButton] = []

    def layout(self, width: int, height: int) -> None:
        bw, bh = 260, 48
        cx = width // 2 - bw // 2
        start_y = max(250, height // 2 - 20)
        self.buttons = [
            UIButton(pygame.Rect(cx, start_y, bw, bh), "Play Game", self.on_play, primary=True),
            UIButton(pygame.Rect(cx, start_y + 62, bw, bh), "How to Play", self.on_how_to_play),
            UIButton(pygame.Rect(cx, start_y + 124, bw, bh), "Settings", self.on_settings),
            UIButton(pygame.Rect(cx, start_y + 186, bw, bh), "Exit", self.on_exit),
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            if b.handle_event(event):
                return

    def draw(
        self,
        surface: pygame.Surface,
        fonts: dict,
        highscore: HighScoreData,
        elapsed: float,
    ) -> None:
        w, h = surface.get_size()
        surface.fill(COLORS["bg_dark"])

        # Subtle checkerboard garden backdrop
        card_rect = pygame.Rect(max(32, w // 2 - 340), 48, min(680, w - 64), h - 96)
        pygame.draw.rect(surface, COLORS["panel_bg"], card_rect, border_radius=18)
        pygame.draw.rect(surface, COLORS["panel_border"], card_rect, 1, border_radius=18)

        title = fonts["hero"].render("DOG CHASE", True, COLORS["accent"])
        surface.blit(title, (int(w / 2 - title.get_width() / 2), card_rect.y + 34))

        sub = fonts["body"].render(
            "Collect every bone and golden coin while outsmarting four human chasers",
            True,
            COLORS["text_muted"],
        )
        surface.blit(sub, (int(w / 2 - sub.get_width() / 2), card_rect.y + 92))

        hs_text = fonts["mono"].render(
            f"HIGH SCORE: {highscore.high_score:,}   ·   BEST LEVEL: {highscore.best_level}   ·   BONES: {highscore.total_bones_collected:,}",
            True,
            (254, 243, 199),
        )
        surface.blit(hs_text, (int(w / 2 - hs_text.get_width() / 2), card_rect.y + 132))

        # Animated mini preview dog & bone above buttons
        preview_y = card_rect.y + 178
        pygame.draw.circle(surface, (245, 158, 11), (w // 2 - 48, preview_y), 14)
        pygame.draw.circle(surface, (251, 191, 36), (w // 2 - 36, preview_y - 6), 10)
        pygame.draw.circle(surface, (30, 41, 59), (w // 2 - 26, preview_y - 6), 3)
        bob = int(3 * (0.5 + 0.5 * pygame.math.Vector2(1, 0).rotate(elapsed * 180).y))
        pygame.draw.line(surface, (254, 243, 199), (w // 2 + 18, preview_y + bob), (w // 2 + 44, preview_y + bob), 6)
        pygame.draw.circle(surface, (254, 243, 199), (w // 2 + 18, preview_y - 3 + bob), 4)
        pygame.draw.circle(surface, (254, 243, 199), (w // 2 + 18, preview_y + 3 + bob), 4)
        pygame.draw.circle(surface, (254, 243, 199), (w // 2 + 44, preview_y - 3 + bob), 4)
        pygame.draw.circle(surface, (254, 243, 199), (w // 2 + 44, preview_y + 3 + bob), 4)

        for b in self.buttons:
            b.draw(surface, fonts["body_bold"])


class HowToPlayScreen:
    def __init__(self, on_back: Callable[[], None]) -> None:
        self.on_back = on_back
        self.back_btn = UIButton(pygame.Rect(0, 0, 160, 44), "Back", on_back, primary=True)

    def layout(self, width: int, height: int) -> None:
        self.back_btn.rect = pygame.Rect(width // 2 - 80, height - 90, 160, 44)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_back()
            return
        self.back_btn.handle_event(event)

    def draw(self, surface: pygame.Surface, fonts: dict) -> None:
        w, h = surface.get_size()
        surface.fill(COLORS["bg_dark"])
        panel = pygame.Rect(max(36, w // 2 - 360), 36, min(720, w - 72), h - 72)
        pygame.draw.rect(surface, COLORS["panel_bg"], panel, border_radius=18)
        pygame.draw.rect(surface, COLORS["panel_border"], panel, 1, border_radius=18)

        title = fonts["title"].render("How to Play DOG CHASE", True, COLORS["accent"])
        surface.blit(title, (panel.x + 32, panel.y + 26))

        lines = [
            ("CONTROLS", COLORS["accent_hover"]),
            ("· Arrow Keys or WASD: Move in 4 directions with smooth corner buffering", COLORS["text_primary"]),
            ("· ESC or P: Pause / Resume   |   V: Toggle Full Maze View   |   M: Mute", COLORS["text_primary"]),
            ("", COLORS["text_primary"]),
            ("COLLECTIBLES & POWER-UPS", COLORS["accent_hover"]),
            ("· Bones (+10 pts): Collect all bones in the maze to complete the level.", COLORS["text_primary"]),
            ("· Golden Coins (+50 pts): High-value bonus coins in side lanes.", COLORS["text_primary"]),
            ("· Power Treats (+100 pts): Shield + speed boost! Humans flee and can be", COLORS["text_primary"]),
            ("  tagged for +200 to +1600 combo points while active.", COLORS["text_primary"]),
            ("", COLORS["text_primary"]),
            ("HUMAN ENEMIES (A* AI)", COLORS["accent_hover"]),
            ("· Officer Miller (Blue): Direct A* chaser tracking your position.", (96, 165, 250)),
            ("· Chef Rosa (Red): Ambusher aiming 4 tiles ahead of your movement.", (248, 113, 113)),
            ("· Jogger Leo (Green): Vector flanker cutting off escape corridors.", (74, 222, 128)),
            ("· Inspector Vance (Amber): Long-range hunter who patrols corners up close.", (251, 191, 36)),
        ]
        y = panel.y + 80
        for text, col in lines:
            if text:
                surf = fonts["small"].render(text, True, col)
                surface.blit(surf, (panel.x + 32, y))
            y += 26

        self.back_btn.draw(surface, fonts["body_bold"])


class SettingsScreen:
    def __init__(
        self,
        settings: GameSettings,
        on_apply: Callable[[GameSettings, bool], None],
        on_back: Callable[[], None],
    ) -> None:
        self.settings = settings
        self.on_apply = on_apply
        self.on_back = on_back
        self.listening_action: Optional[str] = None
        self.buttons: List[UIButton] = []

    def layout(self, width: int, height: int) -> None:
        cx = max(44, width // 2 - 340)
        pw = min(680, width - 88)
        col_w = (pw - 24) // 2
        left_x = cx
        right_x = cx + col_w + 24

        res_w, res_h = self.settings.resolution
        self.buttons = [
            UIButton(
                pygame.Rect(left_x, 118, col_w, 38),
                f"Resolution: {res_w}x{res_h}",
                self._cycle_resolution,
            ),
            UIButton(
                pygame.Rect(right_x, 118, col_w, 38),
                f"Fullscreen: {'On' if self.settings.fullscreen else 'Off'}",
                self._toggle_fullscreen,
            ),
            UIButton(
                pygame.Rect(left_x, 168, col_w, 38),
                f"FPS Cap: {self.settings.fps_limit}",
                self._cycle_fps,
            ),
            UIButton(
                pygame.Rect(right_x, 168, col_w, 38),
                f"Graphics: {self.settings.graphics_quality.title()}",
                self._toggle_graphics,
            ),
            UIButton(
                pygame.Rect(left_x, 228, col_w, 38),
                f"Sound Vol: {int(self.settings.sound_volume * 100)}%",
                self._step_sound_vol,
            ),
            UIButton(
                pygame.Rect(right_x, 228, col_w, 38),
                f"Music Vol: {int(self.settings.music_volume * 100)}%",
                self._step_music_vol,
            ),
            UIButton(
                pygame.Rect(left_x, 278, col_w, 38),
                f"Mute Audio: {'Yes' if self.settings.muted else 'No'}",
                self._toggle_mute,
            ),
            UIButton(
                pygame.Rect(right_x, 278, col_w, 38),
                f"Camera Mode: {self.settings.camera_mode.title()}",
                self._cycle_camera_mode,
            ),
            UIButton(
                pygame.Rect(left_x, 338, col_w, 38),
                f"Camera Zoom: {self.settings.camera_zoom:.2f}x",
                self._step_zoom,
            ),
            UIButton(
                pygame.Rect(right_x, 338, col_w, 38),
                f"Camera Shake: {'On' if self.settings.camera_shake else 'Off'}",
                self._toggle_shake,
            ),
            UIButton(
                pygame.Rect(left_x, 388, col_w, 38),
                f"Dead Zone: {'On' if self.settings.camera_dead_zone else 'Off'}",
                self._toggle_dead_zone,
            ),
            UIButton(
                pygame.Rect(right_x, 388, col_w, 38),
                f"Look-Ahead: {'On' if self.settings.camera_look_ahead else 'Off'}",
                self._toggle_look_ahead,
            ),
        ]

        # Keybinding buttons
        bind_labels = [
            ("up", "Up"),
            ("down", "Down"),
            ("left", "Left"),
            ("right", "Right"),
            ("pause", "Pause"),
            ("full_view", "Full View"),
        ]
        bw = (pw - 24) // 3
        for idx, (action, title) in enumerate(bind_labels):
            bx = cx + (idx % 3) * (bw + 12)
            by = 452 + (idx // 3) * 44
            if self.listening_action == action:
                lbl = f"{title}: Press Key..."
            else:
                keys = "/".join(key_label(k) for k in self.settings.key_bindings.get(action, []))
                lbl = f"{title}: {keys}"
            self.buttons.append(
                UIButton(pygame.Rect(bx, by, bw, 36), lbl, lambda a=action: self._listen_key(a))
            )

        self.buttons.append(
            UIButton(pygame.Rect(left_x, height - 86, 170, 42), "Reset Defaults", self._reset_defaults)
        )
        self.buttons.append(
            UIButton(pygame.Rect(cx + pw - 170, height - 86, 170, 42), "Save & Back", self.on_back, primary=True)
        )

    def _cycle_resolution(self) -> None:
        self.settings.resolution_index = (self.settings.resolution_index + 1) % len(RESOLUTION_PRESETS)
        self.on_apply(self.settings, True)

    def _toggle_fullscreen(self) -> None:
        self.settings.fullscreen = not self.settings.fullscreen
        self.on_apply(self.settings, True)

    def _cycle_fps(self) -> None:
        idx = FPS_OPTIONS.index(self.settings.fps_limit)
        self.settings.fps_limit = FPS_OPTIONS[(idx + 1) % len(FPS_OPTIONS)]
        self.on_apply(self.settings, False)

    def _toggle_graphics(self) -> None:
        idx = GRAPHICS_QUALITIES.index(self.settings.graphics_quality)
        self.settings.graphics_quality = GRAPHICS_QUALITIES[(idx + 1) % len(GRAPHICS_QUALITIES)]
        self.on_apply(self.settings, False)

    def _step_sound_vol(self) -> None:
        self.settings.sound_volume = round((self.settings.sound_volume + 0.15) % 1.05, 2)
        if self.settings.sound_volume > 1.0:
            self.settings.sound_volume = 0.0
        self.on_apply(self.settings, False)

    def _step_music_vol(self) -> None:
        self.settings.music_volume = round((self.settings.music_volume + 0.15) % 1.05, 2)
        if self.settings.music_volume > 1.0:
            self.settings.music_volume = 0.0
        self.on_apply(self.settings, False)

    def _toggle_mute(self) -> None:
        self.settings.muted = not self.settings.muted
        self.on_apply(self.settings, False)

    def _cycle_camera_mode(self) -> None:
        idx = CAMERA_MODES.index(self.settings.camera_mode)
        self.settings.camera_mode = CAMERA_MODES[(idx + 1) % len(CAMERA_MODES)]
        self.on_apply(self.settings, False)

    def _step_zoom(self) -> None:
        z = round(self.settings.camera_zoom + 0.1, 2)
        self.settings.camera_zoom = 0.85 if z > 1.45 else z
        self.on_apply(self.settings, False)

    def _toggle_shake(self) -> None:
        self.settings.camera_shake = not self.settings.camera_shake
        self.on_apply(self.settings, False)

    def _toggle_dead_zone(self) -> None:
        self.settings.camera_dead_zone = not self.settings.camera_dead_zone
        self.on_apply(self.settings, False)

    def _toggle_look_ahead(self) -> None:
        self.settings.camera_look_ahead = not self.settings.camera_look_ahead
        self.on_apply(self.settings, False)

    def _listen_key(self, action: str) -> None:
        self.listening_action = None if self.listening_action == action else action

    def _reset_defaults(self) -> None:
        fresh = GameSettings()
        self.settings.resolution_index = fresh.resolution_index
        self.settings.fullscreen = fresh.fullscreen
        self.settings.fps_limit = fresh.fps_limit
        self.settings.sound_volume = fresh.sound_volume
        self.settings.music_volume = fresh.music_volume
        self.settings.muted = fresh.muted
        self.settings.camera_mode = fresh.camera_mode
        self.settings.camera_zoom = fresh.camera_zoom
        self.settings.camera_shake = fresh.camera_shake
        self.settings.camera_dead_zone = fresh.camera_dead_zone
        self.settings.camera_look_ahead = fresh.camera_look_ahead
        self.settings.graphics_quality = fresh.graphics_quality
        self.settings.key_bindings = default_key_bindings()
        self.listening_action = None
        self.on_apply(self.settings, True)

    def handle_event(self, event: pygame.event.Event, width: int, height: int) -> None:
        if event.type == pygame.KEYDOWN:
            if self.listening_action is not None:
                existing = self.settings.key_bindings.get(self.listening_action, [])
                if event.key not in existing:
                    self.settings.key_bindings[self.listening_action] = [event.key] + existing[:1]
                self.listening_action = None
                self.on_apply(self.settings, False)
                self.layout(width, height)
                return
            if event.key == pygame.K_ESCAPE:
                self.on_back()
                return

        for b in self.buttons:
            if b.handle_event(event):
                self.layout(width, height)
                return

    def draw(self, surface: pygame.Surface, fonts: dict) -> None:
        w, h = surface.get_size()
        surface.fill(COLORS["bg_dark"])
        panel = pygame.Rect(max(24, w // 2 - 365), 24, min(730, w - 48), h - 48)
        pygame.draw.rect(surface, COLORS["panel_bg"], panel, border_radius=18)
        pygame.draw.rect(surface, COLORS["panel_border"], panel, 1, border_radius=18)

        title = fonts["title"].render("Settings", True, COLORS["accent"])
        surface.blit(title, (panel.x + 28, panel.y + 20))
        sub = fonts["small"].render(
            "Click any option to cycle/toggle. Click a keybinding button then press a new key.",
            True,
            COLORS["text_muted"],
        )
        surface.blit(sub, (panel.x + 28, panel.y + 56))

        kb_title = fonts["small_bold"].render("KEYBOARD CONTROLS", True, COLORS["accent_hover"])
        surface.blit(kb_title, (panel.x + 28, 430))

        for b in self.buttons:
            b.draw(surface, fonts["small_bold"])


class OverlayMenu:
    """Reusable modal menu for Pause, Victory, and Game Over screens."""

    def __init__(self, title: str, subtitle: str, actions: List[tuple]) -> None:
        self.title = title
        self.subtitle = subtitle
        self.actions = actions  # (label, callback, primary)
        self.buttons: List[UIButton] = []

    def layout(self, width: int, height: int) -> None:
        bw = 240
        cx = width // 2 - bw // 2
        start_y = height // 2 + 10
        self.buttons = [
            UIButton(
                pygame.Rect(cx, start_y + i * 52, bw, 42),
                lbl,
                cb,
                primary=is_pri,
            )
            for i, (lbl, cb, is_pri) in enumerate(self.actions)
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            if b.handle_event(event):
                return

    def draw(self, surface: pygame.Surface, fonts: dict, stats_line: str = "") -> None:
        w, h = surface.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((5, 9, 18, 195))
        surface.blit(dim, (0, 0))

        card_h = 200 + len(self.buttons) * 52
        card = pygame.Rect(w // 2 - 210, h // 2 - card_h // 2 + 12, 420, card_h)
        pygame.draw.rect(surface, COLORS["panel_bg"], card, border_radius=16)
        pygame.draw.rect(surface, COLORS["panel_border"], card, 1, border_radius=16)

        t_surf = fonts["title"].render(self.title, True, COLORS["accent"])
        surface.blit(t_surf, (int(w / 2 - t_surf.get_width() / 2), card.y + 28))

        s_surf = fonts["small"].render(self.subtitle, True, COLORS["text_muted"])
        surface.blit(s_surf, (int(w / 2 - s_surf.get_width() / 2), card.y + 68))

        if stats_line:
            st_surf = fonts["mono"].render(stats_line, True, COLORS["text_primary"])
            surface.blit(st_surf, (int(w / 2 - st_surf.get_width() / 2), card.y + 100))

        for b in self.buttons:
            b.draw(surface, fonts["body_bold"])
