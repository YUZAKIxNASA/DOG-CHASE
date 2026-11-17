from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import pygame

from camera import Camera
from settings import COLORS, HUD_HEIGHT


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    size: float


@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    color: Tuple[int, int, int]
    life: float
    max_life: float


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []

    def clear(self) -> None:
        self.particles.clear()
        self.floating_texts.clear()

    def spawn_burst(
        self, x: float, y: float, color: Tuple[int, int, int], count: int = 10
    ) -> None:
        for i in range(count):
            ang = (math.pi * 2.0 * i) / count + random.uniform(-0.3, 0.3)
            spd = random.uniform(45.0, 130.0)
            life = random.uniform(0.32, 0.58)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(ang) * spd,
                    vy=math.sin(ang) * spd,
                    life=life,
                    max_life=life,
                    color=color,
                    size=random.uniform(2.5, 4.8),
                )
            )

    def spawn_text(
        self, x: float, y: float, text: str, color: Tuple[int, int, int]
    ) -> None:
        self.floating_texts.append(
            FloatingText(x=x, y=y, text=text, color=color, life=0.85, max_life=0.85)
        )

    def update(self, dt: float) -> None:
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
        self.particles = [p for p in self.particles if p.life > 0.0]

        for ft in self.floating_texts:
            ft.y -= 28.0 * dt
            ft.life -= dt
        self.floating_texts = [ft for ft in self.floating_texts if ft.life > 0.0]

    def draw(self, surface: pygame.Surface, camera: Camera, font: pygame.font.Font) -> None:
        for p in self.particles:
            alpha = max(0.0, min(1.0, p.life / p.max_life))
            sx, sy = camera.world_to_screen(p.x, p.y)
            r = max(1, int(p.size * camera.zoom * (0.5 + 0.5 * alpha)))
            ps = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p.color, int(255 * alpha)), (r + 1, r + 1), r)
            surface.blit(ps, (int(sx - r - 1), int(sy - r - 1)))

        for ft in self.floating_texts:
            sx, sy = camera.world_to_screen(ft.x, ft.y)
            alpha = max(0, min(255, int(255 * (ft.life / ft.max_life))))
            txt_surf = font.render(ft.text, True, ft.color)
            txt_surf.set_alpha(alpha)
            surface.blit(txt_surf, (int(sx - txt_surf.get_width() / 2), int(sy)))


class UIButton:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        on_click: Callable[[], None],
        primary: bool = False,
    ) -> None:
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.primary = primary
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.primary:
            bg = COLORS["accent_hover"] if self.hovered else COLORS["accent"]
            fg = (15, 23, 42)
            border = COLORS["accent_hover"]
        else:
            bg = (38, 52, 79) if self.hovered else COLORS["panel_card"]
            fg = COLORS["text_primary"]
            border = COLORS["accent"] if self.hovered else COLORS["panel_border"]

        pygame.draw.rect(surface, bg, self.rect, border_radius=10)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=10)
        txt = font.render(self.label, True, fg)
        surface.blit(
            txt,
            (
                int(self.rect.centerx - txt.get_width() / 2),
                int(self.rect.centery - txt.get_height() / 2),
            ),
        )


class HUDRenderer:
    def __init__(self) -> None:
        self.pause_rect = pygame.Rect(0, 0, 92, 36)
        self.mute_rect = pygame.Rect(0, 0, 84, 36)
        self.cam_rect = pygame.Rect(0, 0, 128, 36)

    def draw(
        self,
        surface: pygame.Surface,
        fonts: dict,
        score: int,
        high_score: int,
        lives: int,
        max_lives: int,
        level: int,
        level_name: str,
        bones_collected: int,
        total_bones: int,
        powerup_remaining: float,
        powerup_duration: float,
        camera_label: str,
        muted: bool,
    ) -> None:
        w = surface.get_width()
        bar = pygame.Rect(0, 0, w, HUD_HEIGHT)
        pygame.draw.rect(surface, COLORS["hud_bg"], bar)
        pygame.draw.line(surface, COLORS["hud_border"], (0, HUD_HEIGHT - 1), (w, HUD_HEIGHT - 1), 2)

        # Left: Brand + Level
        brand = fonts["title_sm"].render("DOG CHASE", True, COLORS["accent"])
        surface.blit(brand, (18, 12))
        lvl_txt = fonts["small"].render(f"Level {level} · {level_name}", True, COLORS["text_muted"])
        surface.blit(lvl_txt, (18, 38))

        # Center stats
        cx = max(240, int(w * 0.27))
        stats = [
            ("SCORE", f"{score:,}", COLORS["text_primary"]),
            ("BEST", f"{high_score:,}", COLORS["accent_hover"]),
            ("BONES", f"{bones_collected}/{total_bones}", (254, 243, 199)),
        ]
        for label, val, col in stats:
            lbl_s = fonts["tiny"].render(label, True, COLORS["text_muted"])
            val_s = fonts["mono"].render(val, True, col)
            surface.blit(lbl_s, (cx, 11))
            surface.blit(val_s, (cx, 28))
            cx += max(96, val_s.get_width() + 42)

        # Lives hearts
        lives_lbl = fonts["tiny"].render("LIVES", True, COLORS["text_muted"])
        surface.blit(lives_lbl, (cx, 11))
        for i in range(max_lives):
            hx = cx + 8 + i * 22
            hy = 37
            col = COLORS["danger"] if i < lives else (51, 65, 85)
            pygame.draw.circle(surface, col, (hx - 4, hy), 5)
            pygame.draw.circle(surface, col, (hx + 4, hy), 5)
            pygame.draw.polygon(surface, col, [(hx - 9, hy + 2), (hx + 9, hy + 2), (hx, hy + 11)])
        cx += max_lives * 22 + 24

        # Power-Up bar
        if powerup_remaining > 0.0 and powerup_duration > 0.0 and cx + 110 < w - 330:
            p_lbl = fonts["tiny"].render(f"SHIELD {powerup_remaining:.1f}s", True, COLORS["accent_hover"])
            surface.blit(p_lbl, (cx, 12))
            track = pygame.Rect(cx, 33, 96, 8)
            pygame.draw.rect(surface, (30, 41, 59), track, border_radius=4)
            pct = max(0.0, min(1.0, powerup_remaining / powerup_duration))
            fill = pygame.Rect(cx, 33, int(96 * pct), 8)
            pygame.draw.rect(surface, COLORS["accent"], fill, border_radius=4)

        # Right interactive buttons
        self.pause_rect = pygame.Rect(w - 104, 14, 88, 36)
        self.mute_rect = pygame.Rect(w - 196, 14, 84, 36)
        self.cam_rect = pygame.Rect(w - 332, 14, 128, 36)

        for rect, text, is_accent in (
            (self.cam_rect, f"Cam: {camera_label}", False),
            (self.mute_rect, "Muted" if muted else "Audio On", False),
            (self.pause_rect, "Pause", True),
        ):
            bg = COLORS["accent"] if is_accent else COLORS["panel_card"]
            fg = (15, 23, 42) if is_accent else COLORS["text_primary"]
            border = COLORS["accent"] if is_accent else COLORS["panel_border"]
            pygame.draw.rect(surface, bg, rect, border_radius=8)
            pygame.draw.rect(surface, border, rect, 1, border_radius=8)
            t = fonts["small_bold"].render(text, True, fg)
            surface.blit(t, (int(rect.centerx - t.get_width() / 2), int(rect.centery - t.get_height() / 2)))
