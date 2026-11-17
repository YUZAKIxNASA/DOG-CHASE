from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import pygame

from camera import Camera
from collectibles import Collectible, CollectibleKind
from settings import ASSETS_DIR, COLORS, TILE_SIZE, load_optional_sprite


@dataclass
class LevelSpec:
    level_index: int
    name: str
    subtitle: str
    prefer_fixed_camera: bool
    enemy_speed_multiplier: float
    powerup_duration: float
    rows: List[str]


LEVEL_SPECS: List[LevelSpec] = [
    LevelSpec(
        level_index=1,
        name="Garden Courtyard",
        subtitle="Compact hedge courtyard — Fixed Camera view",
        prefer_fixed_camera=True,
        enemy_speed_multiplier=0.92,
        powerup_duration=8.0,
        rows=[
            "###################",
            "#PBBBBBCBBBCBBBBBP#",
            "#B###B###B###B###B#",
            "#BBBBB.BBBBB.BBBBB#",
            "#B#B#####B#####B#B#",
            "#C#BBBBBB1BBBBBB#C#",
            "#B###B###.###B###B#",
            "#BBBB.B2.D.3B.BBBB#",
            "#B###B###.###B###B#",
            "#C#BBBBBB4BBBBBB#C#",
            "#B#B#####B#####B#B#",
            "#BBBBB.BBBBB.BBBBB#",
            "#B###B###B###B###B#",
            "#PBBBBBCBBBCBBBBBP#",
            "###################",
        ],
    ),
    LevelSpec(
        level_index=2,
        name="Hedge Labyrinth",
        subtitle="Twisting garden lanes — Smooth Follow Camera",
        prefer_fixed_camera=False,
        enemy_speed_multiplier=1.0,
        powerup_duration=7.5,
        rows=[
            "#######################",
            "#PBBBBB#BBBCBBB#BBBBBP#",
            "#B####B#B#####B#B####B#",
            "#BBBBCBBBBBBBBBBBCBBBB#",
            "#B##B#B###B#B###B#B##B#",
            "#BBBB#BBBB1B2BBBB#BBBB#",
            "####B###B#####B###B####",
            "#BBBBBBBB..D..BBBBBBBB#",
            "#B####B###B#B###B####B#",
            "#CBBBBBBBB3B4BBBBBBBBC#",
            "#B##B#B###B#B###B#B##B#",
            "#BBBBB#BBBBBBBBBB#BBBB#",
            "#B####B#B#####B#B####B#",
            "#BBBCBBBB#BBB#BBBBCBBB#",
            "#B######B#B#B#B######B#",
            "#PBBBBBBBBBCBBBBBBBBBP#",
            "#######################",
        ],
    ),
    LevelSpec(
        level_index=3,
        name="Lantern Plaza",
        subtitle="Cross-plaza tunnels and wrap gates",
        prefer_fixed_camera=False,
        enemy_speed_multiplier=1.08,
        powerup_duration=7.0,
        rows=[
            "###########################",
            "#PBBBBBB#BBBBCBBBB#BBBBBBP#",
            "#B#####B#B#######B#B#####B#",
            "#BBBBBCBBBBBBBBBBBBBCBBBBB#",
            "#B###B#B####B#B####B#B###B#",
            "#BBBB#BBBBBB1B2BBBBBB#BBBB#",
            "#B###B#####B###B#####B###B#",
            "#CBBBBBBBBBB...BBBBBBBBBBC#",
            "#####B###B##...##B###B#####",
            ".BBBBBBBB...D.3...BBBBBBBB.",
            "#####B###B##...##B###B#####",
            "#CBBBBBBBBBB.4.BBBBBBBBBBC#",
            "#B###B#####B###B#####B###B#",
            "#BBBB#BBBBBBBBBBBBBBB#BBBB#",
            "#B###B#B####B#B####B#B###B#",
            "#BBBBBCBBBBBBBBBBBBBCBBBBB#",
            "#B#####B#B#######B#B#####B#",
            "#PBBBBBB#BBBBCBBBB#BBBBBBP#",
            "###########################",
        ],
    ),
    LevelSpec(
        level_index=4,
        name="Moonlit Estates",
        subtitle="Sprawling cobblestone maze — Dead Zone & Look-Ahead",
        prefer_fixed_camera=False,
        enemy_speed_multiplier=1.15,
        powerup_duration=6.5,
        rows=[
            "###############################",
            "#PBBBBBCBBB#BBBBBBB#BBBCBBBBBP#",
            "#B#####B##B#B#####B#B##B#####B#",
            "#BBBBBBBBB#BBBBBBBBBB#BBBBBBBB#",
            "#B###B###B###B###B###B###B###B#",
            "#CBBB#BBBBBBBB1B2BBBBBBBB#BBBC#",
            "#B###B#B####B#####B####B#B###B#",
            "#BBBBBBB#BBBBBB.BBBBBB#BBBBBBB#",
            "####B###B#B###B.B###B#B###B####",
            "#BBBBBBBB#BBBB.D.BBBB#BBBBBBBB#",
            ".BBB###B###B##...##B###B###BBB.",
            "#BBBBBBBB#BBBB3B4BBBB#BBBBBBBB#",
            "####B###B#B###B#B###B#B###B####",
            "#BBBBBBB#BBBBBBBBBBBBB#BBBBBBB#",
            "#B###B#B####B#####B####B#B###B#",
            "#CBBB#BBBBBBBBBCBBBBBBBBB#BBBC#",
            "#B###B###B###B###B###B###B###B#",
            "#BBBBBBBBB#BBBBBBBBBB#BBBBBBBB#",
            "#B#####B##B#B#####B#B##B#####B#",
            "#PBBBBBCBBB#BBBBBBB#BBBCBBBBBP#",
            "###############################",
        ],
    ),
    LevelSpec(
        level_index=5,
        name="Grand Manor",
        subtitle="Full estate challenge — High-speed tactical humans",
        prefer_fixed_camera=False,
        enemy_speed_multiplier=1.22,
        powerup_duration=6.0,
        rows=[
            "###################################",
            "#PBBBBBB#BBBCBBBBBBBBBCBBB#BBBBBBP#",
            "#B#####B#B#######B#######B#B#####B#",
            "#BBBBBBBBB#BBBBBBBBBBBBB#BBBBBBBBB#",
            "#B###B###B#B###B###B###B#B###B###B#",
            "#CBBB#BBBBBBBBBB1B2BBBBBBBBBB#BBBC#",
            "#B###B#B#####B#######B#####B#B###B#",
            "#BBBBBBB#BBBBBBBB.BBBBBBBB#BBBBBBB#",
            "#B#####B#B###B###.###B###B#B#####B#",
            "#BBBBBBBB#BBBBBB...BBBBBB#BBBBBBBB#",
            "#####B###B#B###B...B###B#B###B#####",
            ".BBBBBBBBBBBB...D.3...BBBBBBBBBBBB.",
            "#####B###B#B###B.4.B###B#B###B#####",
            "#BBBBBBBB#BBBBBBBBBBBBBBB#BBBBBBBB#",
            "#B#####B#B###B###B###B###B#B#####B#",
            "#BBBBBBB#BBBBBBBBBBBBBBBBB#BBBBBBB#",
            "#B###B#B#####B#######B#####B#B###B#",
            "#CBBB#BBBBBBBBBBBCBBBBBBBBBBB#BBBC#",
            "#B###B###B#B###B###B###B#B###B###B#",
            "#BBBBBBBBB#BBBBBBBBBBBBB#BBBBBBBBB#",
            "#B#####B#B#######B#######B#B#####B#",
            "#PBBBBBB#BBBCBBBBBBBBBCBBB#BBBBBBP#",
            "###################################",
        ],
    ),
]


class Maze:
    def __init__(self, level_number: int) -> None:
        idx = (level_number - 1) % len(LEVEL_SPECS)
        cycle = (level_number - 1) // len(LEVEL_SPECS)
        spec = LEVEL_SPECS[idx]

        self.level_number = level_number
        self.name = f"{spec.name} (Lap {cycle + 1})" if cycle > 0 else spec.name
        self.subtitle = spec.subtitle
        self.prefer_fixed_camera = spec.prefer_fixed_camera
        self.enemy_speed_multiplier = min(1.45, spec.enemy_speed_multiplier + cycle * 0.1)
        self.powerup_duration = max(4.0, spec.powerup_duration - cycle * 0.6)

        self.height = len(spec.rows)
        self.width = len(spec.rows[0])
        self.grid: List[List[str]] = []  # "wall" | "floor"
        self.dog_spawn: Tuple[int, int] = (self.width // 2, self.height // 2)
        enemy_map: Dict[str, Tuple[int, int]] = {}
        raw_collectibles: List[Collectible] = []

        for y, row_str in enumerate(spec.rows):
            row: List[str] = []
            for x, ch in enumerate(row_str):
                if ch == "#":
                    row.append("wall")
                else:
                    row.append("floor")
                    if ch == "D":
                        self.dog_spawn = (x, y)
                    elif ch in ("1", "2", "3", "4"):
                        enemy_map[ch] = (x, y)
                    elif ch == "B":
                        raw_collectibles.append(Collectible(CollectibleKind.BONE, x, y))
                    elif ch == "C":
                        raw_collectibles.append(Collectible(CollectibleKind.COIN, x, y))
                    elif ch == "P":
                        raw_collectibles.append(Collectible(CollectibleKind.POWERUP, x, y))
            self.grid.append(row)

        # Flood-fill verify all collectibles are reachable from dog_spawn
        reachable: Set[Tuple[int, int]] = {self.dog_spawn}
        queue: deque[Tuple[int, int]] = deque([self.dog_spawn])
        while queue:
            cx, cy = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = (cx + dx) % self.width
                ny = cy + dy
                if 0 <= ny < self.height and self.grid[ny][nx] == "floor":
                    if (nx, ny) not in reachable:
                        reachable.add((nx, ny))
                        queue.append((nx, ny))

        self.collectibles: List[Collectible] = [
            item for item in raw_collectibles if (item.tile_x, item.tile_y) in reachable
        ]
        self.enemy_spawns: List[Tuple[int, int]] = [
            enemy_map.get(k, (self.dog_spawn[0], max(1, self.dog_spawn[1] - 2)))
            for k in ("1", "2", "3", "4")
        ]

        self.bg_image: Optional[pygame.Surface] = load_optional_sprite(
            ASSETS_DIR / "backgrounds" / "background.png"
        )

    @property
    def world_width(self) -> float:
        return float(self.width * TILE_SIZE)

    @property
    def world_height(self) -> float:
        return float(self.height * TILE_SIZE)

    def wrap_x(self, tx: int) -> int:
        return tx % self.width

    def is_walkable(self, tx: int, ty: int) -> bool:
        if ty < 0 or ty >= self.height:
            return False
        if tx < 0 or tx >= self.width:
            edge_x = 0 if tx < 0 else self.width - 1
            if self.grid[ty][edge_x] == "wall":
                return False
        return self.grid[ty][tx % self.width] == "floor"

    def draw(
        self,
        surface: pygame.Surface,
        camera: Camera,
        high_quality: bool = True,
    ) -> None:
        if self.bg_image is not None:
            scaled = pygame.transform.smoothscale(self.bg_image, surface.get_size())
            surface.blit(scaled, (0, 0))

        tile_px = max(2, int(round(TILE_SIZE * camera.zoom)))

        for y in range(self.height):
            for x in range(self.width):
                wx = x * TILE_SIZE
                wy = y * TILE_SIZE
                sx, sy = camera.world_to_screen(wx, wy)
                # Cull off-screen tiles
                if (
                    sx + tile_px < 0
                    or sy + tile_px < 0
                    or sx > surface.get_width()
                    or sy > surface.get_height()
                ):
                    continue

                rect = pygame.Rect(int(sx), int(sy), tile_px + 1, tile_px + 1)

                if self.grid[y][x] == "floor":
                    color = COLORS["floor_a"] if (x + y) % 2 == 0 else COLORS["floor_b"]
                    pygame.draw.rect(surface, color, rect)
                    if high_quality:
                        pygame.draw.rect(surface, COLORS["floor_grid"], rect, 1)
                else:
                    pygame.draw.rect(surface, COLORS["wall_base"], rect)
                    pad = max(1, int(3 * camera.zoom))
                    inner = pygame.Rect(
                        rect.x + pad,
                        rect.y + pad,
                        max(1, rect.w - pad * 2),
                        max(1, rect.h - pad * 2),
                    )
                    pygame.draw.rect(surface, COLORS["wall_top"], inner)

                    if high_quality:
                        pad2 = max(2, int(6 * camera.zoom))
                        crown = pygame.Rect(
                            rect.x + pad2,
                            rect.y + pad2,
                            max(1, rect.w - pad2 * 2),
                            max(1, rect.h - pad2 * 2 - 1),
                        )
                        pygame.draw.rect(surface, COLORS["wall_highlight"], crown)

                        edge_t = max(1, int(3 * camera.zoom))
                        if self.is_walkable(x, y - 1):
                            pygame.draw.rect(
                                surface, COLORS["wall_edge"], (rect.x, rect.y, rect.w, edge_t)
                            )
                        if self.is_walkable(x, y + 1):
                            pygame.draw.rect(
                                surface,
                                COLORS["wall_edge"],
                                (rect.x, rect.bottom - edge_t, rect.w, edge_t),
                            )
                        if self.is_walkable(x - 1, y):
                            pygame.draw.rect(
                                surface, COLORS["wall_edge"], (rect.x, rect.y, edge_t, rect.h)
                            )
                        if self.is_walkable(x + 1, y):
                            pygame.draw.rect(
                                surface,
                                COLORS["wall_edge"],
                                (rect.right - edge_t, rect.y, edge_t, rect.h),
                            )

                        # Deterministic blossom accents
                        if (x * 13 + y * 7) % 11 == 0:
                            r = max(1, int(2.2 * camera.zoom))
                            pygame.draw.circle(
                                surface,
                                (253, 224, 71),
                                (int(rect.x + rect.w * 0.3), int(rect.y + rect.h * 0.34)),
                                r,
                            )
                            pygame.draw.circle(
                                surface,
                                (244, 114, 182),
                                (int(rect.x + rect.w * 0.68), int(rect.y + rect.h * 0.62)),
                                r,
                            )
