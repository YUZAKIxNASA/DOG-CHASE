from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import pygame

from camera import Camera
from settings import ASSETS_DIR, TILE_SIZE, load_optional_sprite


class CollectibleKind(str, Enum):
    BONE = "bone"
    COIN = "coin"
    POWERUP = "powerup"


SCORE_VALUES = {
    CollectibleKind.BONE: 10,
    CollectibleKind.COIN: 50,
    CollectibleKind.POWERUP: 100,
}


@dataclass
class Collectible:
    kind: CollectibleKind
    tile_x: int
    tile_y: int
    collected: bool = False

    @property
    def phase_offset(self) -> float:
        return (self.tile_x * 0.45 + self.tile_y * 0.7) % (math.pi * 2)


@dataclass
class CollectEvent:
    kind: CollectibleKind
    points: int
    world_x: float
    world_y: float


class CollectibleManager:
    def __init__(self) -> None:
        self.bone_sprite: Optional[pygame.Surface] = load_optional_sprite(
            ASSETS_DIR / "collectibles" / "bone.png", (26, 26)
        )
        self.coin_sprite: Optional[pygame.Surface] = load_optional_sprite(
            ASSETS_DIR / "collectibles" / "coin.png", (26, 26)
        )
        self.power_sprite: Optional[pygame.Surface] = load_optional_sprite(
            ASSETS_DIR / "collectibles" / "powerup.png", (28, 28)
        )

    def try_collect(
        self, collectibles: List[Collectible], player_x: float, player_y: float
    ) -> Optional[CollectEvent]:
        pickup_radius = TILE_SIZE * 0.45
        for item in collectibles:
            if item.collected:
                continue
            cx = (item.tile_x + 0.5) * TILE_SIZE
            cy = (item.tile_y + 0.5) * TILE_SIZE
            if math.hypot(player_x - cx, player_y - cy) <= pickup_radius:
                item.collected = True
                return CollectEvent(
                    kind=item.kind,
                    points=SCORE_VALUES[item.kind],
                    world_x=cx,
                    world_y=cy,
                )
        return None

    def draw(
        self,
        surface: pygame.Surface,
        collectibles: List[Collectible],
        camera: Camera,
        elapsed: float,
        high_quality: bool = True,
    ) -> None:
        z = camera.zoom
        for item in collectibles:
            if item.collected:
                continue
            wx = (item.tile_x + 0.5) * TILE_SIZE
            wy = (item.tile_y + 0.5) * TILE_SIZE
            bob = math.sin(elapsed * 4.0 + item.phase_offset) * 2.2
            sx, sy = camera.world_to_screen(wx, wy + bob)
            if (
                sx < -40
                or sy < -40
                or sx > surface.get_width() + 40
                or sy > surface.get_height() + 40
            ):
                continue

            if item.kind == CollectibleKind.BONE:
                self._draw_bone(surface, sx, sy, z, self.bone_sprite)
            elif item.kind == CollectibleKind.COIN:
                self._draw_coin(surface, sx, sy, z, elapsed, item.phase_offset, high_quality, self.coin_sprite)
            else:
                self._draw_powerup(surface, sx, sy, z, elapsed, item.phase_offset, high_quality, self.power_sprite)

    def _draw_bone(
        self,
        surface: pygame.Surface,
        sx: float,
        sy: float,
        z: float,
        sprite: Optional[pygame.Surface],
    ) -> None:
        if sprite is not None:
            w = max(8, int(24 * z))
            img = pygame.transform.smoothscale(sprite, (w, w))
            surface.blit(img, (int(sx - w / 2), int(sy - w / 2)))
            return

        # Clean bone vector geometry (tilted dog bone)
        r = max(2, int(3.0 * z))
        half_len = max(4, int(6.5 * z))
        thick = max(2, int(2.4 * z))
        p1 = (int(sx - half_len), int(sy + half_len * 0.32))
        p2 = (int(sx + half_len), int(sy - half_len * 0.32))
        pygame.draw.line(surface, (146, 64, 14), p1, p2, thick * 2 + 2)
        pygame.draw.line(surface, (254, 243, 199), p1, p2, thick * 2)

        for end_x, end_y in (p1, p2):
            for ox, oy in ((-1.5 * z, -2.0 * z), (1.5 * z, 2.0 * z)):
                pygame.draw.circle(surface, (146, 64, 14), (int(end_x + ox), int(end_y + oy)), r + 1)
                pygame.draw.circle(surface, (254, 243, 199), (int(end_x + ox), int(end_y + oy)), r)

    def _draw_coin(
        self,
        surface: pygame.Surface,
        sx: float,
        sy: float,
        z: float,
        elapsed: float,
        phase: float,
        high_quality: bool,
        sprite: Optional[pygame.Surface],
    ) -> None:
        if sprite is not None:
            w = max(10, int(26 * z))
            img = pygame.transform.smoothscale(sprite, (w, w))
            surface.blit(img, (int(sx - w / 2), int(sy - w / 2)))
            return

        spin = 0.55 + 0.45 * abs(math.cos(elapsed * 4.5 + phase))
        rad_y = max(4, int(9.5 * z))
        rad_x = max(2, int(rad_y * spin))

        if high_quality:
            glow_r = max(6, int(14 * z))
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (251, 191, 36, 45), (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (int(sx - glow_r), int(sy - glow_r)))

        rect = pygame.Rect(int(sx - rad_x), int(sy - rad_y), rad_x * 2, rad_y * 2)
        pygame.draw.ellipse(surface, (251, 191, 36), rect)
        pygame.draw.ellipse(surface, (180, 83, 9), rect, max(1, int(1.6 * z)))

        if rad_x >= 5:
            inner = rect.inflate(-max(2, int(5 * z)), -max(2, int(5 * z)))
            if inner.w > 2 and inner.h > 2:
                pygame.draw.ellipse(surface, (254, 240, 138), inner, 1)

    def _draw_powerup(
        self,
        surface: pygame.Surface,
        sx: float,
        sy: float,
        z: float,
        elapsed: float,
        phase: float,
        high_quality: bool,
        sprite: Optional[pygame.Surface],
    ) -> None:
        if sprite is not None:
            w = max(12, int(28 * z))
            img = pygame.transform.smoothscale(sprite, (w, w))
            surface.blit(img, (int(sx - w / 2), int(sy - w / 2)))
            return

        pulse = 1.0 + 0.14 * math.sin(elapsed * 7.0 + phase)
        outer_r = max(6, int(12.5 * z * pulse))
        inner_r = max(3, int(5.8 * z * pulse))

        if high_quality:
            glow_r = max(10, int(20 * z * pulse))
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (245, 158, 11, 80), (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (int(sx - glow_r), int(sy - glow_r)))

        points: List[Tuple[float, float]] = []
        for i in range(10):
            r = outer_r if i % 2 == 0 else inner_r
            ang = (i * math.pi) / 5.0 - math.pi / 2.0
            points.append((sx + math.cos(ang) * r, sy + math.sin(ang) * r))

        pygame.draw.polygon(surface, (245, 158, 11), points)
        pygame.draw.polygon(surface, (254, 243, 199), points, max(1, int(1.8 * z)))
