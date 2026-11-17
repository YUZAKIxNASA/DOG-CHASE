from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import pygame

from camera import Camera, dir_to_vector
from maze import Maze
from settings import ASSETS_DIR, TILE_SIZE, load_optional_sprite


def opposite_dir(direction: str) -> str:
    return {
        "up": "down",
        "down": "up",
        "left": "right",
        "right": "left",
    }.get(direction, "none")


class DogPlayer:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.tile_x = 0
        self.tile_y = 0
        self.dir = "none"
        self.facing = "right"
        self.buffered_dir = "none"
        self.base_speed = TILE_SIZE * 4.9
        self.walk_cycle = 0.0
        self.powerup_timer = 0.0
        self.powerup_duration = 7.5
        self.invuln_timer = 0.0
        self.is_moving = False

        self.sprites: Dict[str, Optional[pygame.Surface]] = {}
        self.load_sprites()

    def load_sprites(self) -> None:
        char_dir = ASSETS_DIR / "characters"
        fallback = load_optional_sprite(char_dir / "dog.png", (34, 34))
        self.sprites = {
            "right": load_optional_sprite(char_dir / "dog_right.png", (34, 34)) or fallback,
            "left": load_optional_sprite(char_dir / "dog_left.png", (34, 34))
            or (pygame.transform.flip(fallback, True, False) if fallback else None),
            "up": load_optional_sprite(char_dir / "dog_up.png", (34, 34)) or fallback,
            "down": load_optional_sprite(char_dir / "dog_down.png", (34, 34)) or fallback,
        }

    def spawn(self, maze: Maze) -> None:
        self.tile_x, self.tile_y = maze.dog_spawn
        self.x = (self.tile_x + 0.5) * TILE_SIZE
        self.y = (self.tile_y + 0.5) * TILE_SIZE
        self.dir = "none"
        self.facing = "right"
        self.buffered_dir = "none"
        self.walk_cycle = 0.0
        self.powerup_duration = maze.powerup_duration
        self.powerup_timer = 0.0
        self.invuln_timer = 1.0
        self.is_moving = False

    def reset_position(self, maze: Maze) -> None:
        self.tile_x, self.tile_y = maze.dog_spawn
        self.x = (self.tile_x + 0.5) * TILE_SIZE
        self.y = (self.tile_y + 0.5) * TILE_SIZE
        self.dir = "none"
        self.facing = "right"
        self.buffered_dir = "none"
        self.invuln_timer = 1.6
        self.is_moving = False

    def queue_direction(self, next_dir: str) -> None:
        if next_dir in ("up", "down", "left", "right"):
            self.buffered_dir = next_dir

    def activate_powerup(self, duration: float) -> None:
        self.powerup_duration = duration
        self.powerup_timer = duration

    def has_powerup(self) -> bool:
        return self.powerup_timer > 0.0

    def update(self, dt: float, maze: Maze) -> None:
        if self.powerup_timer > 0.0:
            self.powerup_timer = max(0.0, self.powerup_timer - dt)
        if self.invuln_timer > 0.0:
            self.invuln_timer = max(0.0, self.invuln_timer - dt)

        speed = self.base_speed * (1.22 if self.has_powerup() else 1.0)
        step = speed * dt

        cur_tx = int(self.x // TILE_SIZE)
        cur_ty = int(self.y // TILE_SIZE)
        center_x = (cur_tx + 0.5) * TILE_SIZE
        center_y = (cur_ty + 0.5) * TILE_SIZE

        if self.buffered_dir != "none":
            bx, by = dir_to_vector(self.buffered_dir)
            if self.dir == "none" or self.buffered_dir == opposite_dir(self.dir):
                if maze.is_walkable(cur_tx + bx, cur_ty + by):
                    self.dir = self.buffered_dir
                    self.facing = self.buffered_dir
                    self.buffered_dir = "none"
            elif self.buffered_dir != self.dir:
                dist = math.hypot(self.x - center_x, self.y - center_y)
                turn_threshold = max(step + 3.0, TILE_SIZE * 0.28)
                if dist <= turn_threshold and maze.is_walkable(cur_tx + bx, cur_ty + by):
                    self.x = center_x
                    self.y = center_y
                    self.dir = self.buffered_dir
                    self.facing = self.buffered_dir
                    self.buffered_dir = "none"

        if self.dir == "none":
            self.is_moving = False
            return

        vx, vy = dir_to_vector(self.dir)
        next_x = self.x + vx * step
        next_y = self.y + vy * step

        ahead_walkable = maze.is_walkable(cur_tx + vx, cur_ty + vy)
        if not ahead_walkable:
            if (
                (vx > 0 and next_x >= center_x)
                or (vx < 0 and next_x <= center_x)
                or (vy > 0 and next_y >= center_y)
                or (vy < 0 and next_y <= center_y)
            ):
                self.x = center_x
                self.y = center_y
                self.dir = "none"
                self.is_moving = False
                return

        if vx != 0:
            self.y += (center_y - self.y) * min(1.0, 16.0 * dt)
            self.x = next_x
        elif vy != 0:
            self.x += (center_x - self.x) * min(1.0, 16.0 * dt)
            self.y = next_y

        # Horizontal tunnel wrapping
        if self.x < 0:
            self.x += maze.world_width
        elif self.x >= maze.world_width:
            self.x -= maze.world_width

        self.tile_x = maze.wrap_x(int(self.x // TILE_SIZE))
        self.tile_y = max(0, min(maze.height - 1, int(self.y // TILE_SIZE)))
        self.is_moving = True
        self.walk_cycle += dt * (16.0 if self.has_powerup() else 12.0)

    def draw(
        self,
        surface: pygame.Surface,
        camera: Camera,
        elapsed: float,
        high_quality: bool = True,
    ) -> None:
        if self.invuln_timer > 0.0 and int(elapsed * 14) % 2 == 0:
            return

        sx, sy = camera.world_to_screen(self.x, self.y)
        z = camera.zoom

        # Power-up protective aura
        if self.has_powerup():
            aura_r = max(10, int((21.0 + math.sin(elapsed * 12.0) * 2.5) * z))
            is_warning = self.powerup_timer < 2.0 and int(elapsed * 10) % 2 == 0
            aura_color = (248, 113, 113) if is_warning else (251, 191, 36)
            if high_quality:
                glow = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*aura_color, 45), (aura_r, aura_r), aura_r)
                surface.blit(glow, (int(sx - aura_r), int(sy - aura_r)))
            pygame.draw.circle(surface, aura_color, (int(sx), int(sy)), aura_r, max(1, int(2.4 * z)))

        # External replaceable sprite if provided
        custom_img = self.sprites.get(self.facing)
        if custom_img is not None:
            size = max(12, int(34 * z))
            bounce = math.sin(self.walk_cycle) * 1.8 * z if self.is_moving else 0.0
            scaled = pygame.transform.smoothscale(custom_img, (size, size))
            surface.blit(scaled, (int(sx - size / 2), int(sy - size / 2 - bounce)))
            return

        # Procedural Dog sprite (4-directional + walking animation)
        shadow_rect = pygame.Rect(int(sx - 12 * z), int(sy + 8 * z), int(24 * z), int(9 * z))
        shadow_surf = pygame.Surface((max(4, shadow_rect.w), max(4, shadow_rect.h)), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 95), shadow_surf.get_rect())
        surface.blit(shadow_surf, shadow_rect.topleft)

        bounce = (
            abs(math.sin(self.walk_cycle)) * 2.4 * z
            if self.is_moving
            else math.sin(elapsed * 3.0) * 0.6 * z
        )
        cy = sy - bounce
        paw_swing = math.sin(self.walk_cycle) * 3.5 * z if self.is_moving else 0.0
        tail_wag = math.sin(elapsed * (22.0 if self.has_powerup() else 12.0)) * 3.0 * z

        if self.facing in ("left", "right"):
            flip = -1 if self.facing == "left" else 1
            # Tail
            tail_start = (int(sx - 10 * z * flip), int(cy))
            tail_end = (int(sx - 16 * z * flip), int(cy - 6 * z + tail_wag))
            pygame.draw.line(surface, (146, 64, 14), tail_start, tail_end, max(2, int(4.5 * z)))
            pygame.draw.line(surface, (217, 119, 6), tail_start, tail_end, max(1, int(3.0 * z)))

            # Paws
            for px_off in (-8 * z * flip + paw_swing, 5 * z * flip - paw_swing):
                paw = pygame.Rect(int(sx + px_off - 2 * z), int(cy + 5 * z), max(2, int(4.5 * z)), max(3, int(7 * z)))
                pygame.draw.rect(surface, (180, 83, 9), paw, border_radius=2)

            # Body
            body = pygame.Rect(int(sx - 11.5 * z), int(cy - 6.5 * z), max(6, int(23 * z)), max(6, int(17 * z)))
            pygame.draw.ellipse(surface, (245, 158, 11), body)
            pygame.draw.ellipse(surface, (120, 53, 15), body, max(1, int(1.6 * z)))

            # Red collar
            pygame.draw.line(
                surface,
                (239, 68, 68),
                (int(sx + 4 * z * flip), int(cy - 4 * z)),
                (int(sx + 6 * z * flip), int(cy + 6 * z)),
                max(2, int(2.6 * z)),
            )

            # Head & Snout
            hx, hy = int(sx + 8 * z * flip), int(cy - 4 * z)
            pygame.draw.circle(surface, (251, 191, 36), (hx, hy), max(4, int(8 * z)))
            pygame.draw.circle(surface, (120, 53, 15), (hx, hy), max(4, int(8 * z)), max(1, int(1.5 * z)))

            snout = pygame.Rect(
                int(sx + (14.5 * flip - 4.2) * z),
                int(cy - 5.5 * z),
                max(3, int(8.4 * z)),
                max(3, int(6.4 * z)),
            )
            pygame.draw.ellipse(surface, (253, 230, 138), snout)
            pygame.draw.circle(
                surface, (30, 41, 59), (int(sx + 17.5 * z * flip), int(cy - 3.5 * z)), max(1, int(2.0 * z))
            )

            # Floppy Ear & Eye
            ear = pygame.Rect(
                int(sx + (4.5 * flip - 3.2) * z),
                int(cy - 9 * z),
                max(2, int(6.4 * z)),
                max(3, int(11 * z)),
            )
            pygame.draw.ellipse(surface, (180, 83, 9), ear)
            pygame.draw.circle(
                surface, (15, 23, 42), (int(sx + 10.5 * z * flip), int(cy - 6.5 * z)), max(1, int(1.8 * z))
            )
        else:
            is_up = self.facing == "up"
            tail_y = cy + 11 * z if is_up else cy - 10 * z
            pygame.draw.line(
                surface,
                (217, 119, 6),
                (int(sx), int(tail_y)),
                (int(sx + tail_wag), int(tail_y + (6 * z if is_up else -6 * z))),
                max(2, int(3.8 * z)),
            )

            for side_x, swing in ((-8 * z, paw_swing * 0.6), (4 * z, -paw_swing * 0.6)):
                paw = pygame.Rect(
                    int(sx + side_x),
                    int(cy + 3 * z + swing),
                    max(2, int(4.5 * z)),
                    max(3, int(7 * z)),
                )
                pygame.draw.rect(surface, (180, 83, 9), paw, border_radius=2)

            body = pygame.Rect(int(sx - 9.5 * z), int(cy - 10 * z), max(6, int(19 * z)), max(6, int(22 * z)))
            pygame.draw.ellipse(surface, (245, 158, 11), body)
            pygame.draw.ellipse(surface, (120, 53, 15), body, max(1, int(1.6 * z)))

            hy = int(cy - (6 * z if is_up else 3 * z))
            pygame.draw.circle(surface, (251, 191, 36), (int(sx), hy), max(4, int(8.2 * z)))
            pygame.draw.circle(surface, (120, 53, 15), (int(sx), hy), max(4, int(8.2 * z)), max(1, int(1.5 * z)))

            for ex in (-7.5 * z, 7.5 * z):
                ear = pygame.Rect(int(sx + ex - 2.8 * z), int(hy - 4 * z), max(2, int(5.6 * z)), max(3, int(9.5 * z)))
                pygame.draw.ellipse(surface, (180, 83, 9), ear)

            if not is_up:
                snout = pygame.Rect(int(sx - 4.5 * z), int(cy - 1.5 * z), max(3, int(9 * z)), max(3, int(6.4 * z)))
                pygame.draw.ellipse(surface, (253, 230, 138), snout)
                pygame.draw.circle(surface, (30, 41, 59), (int(sx), int(cy + 1 * z)), max(1, int(2.1 * z)))
                pygame.draw.circle(surface, (15, 23, 42), (int(sx - 3.2 * z), int(cy - 4.5 * z)), max(1, int(1.6 * z)))
                pygame.draw.circle(surface, (15, 23, 42), (int(sx + 3.2 * z), int(cy - 4.5 * z)), max(1, int(1.6 * z)))
