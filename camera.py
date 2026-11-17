from __future__ import annotations

import math
import random
from typing import Tuple

from settings import GameSettings, TILE_SIZE


def dir_to_vector(direction: str) -> Tuple[int, int]:
    if direction == "up":
        return (0, -1)
    if direction == "down":
        return (0, 1)
    if direction == "left":
        return (-1, 0)
    if direction == "right":
        return (1, 0)
    return (0, 0)


class Camera:
    """
    2D Top-Down Camera System supporting:
    - Fixed Camera
    - Smooth Follow Camera
    - Camera Bounds
    - Smooth Camera Movement
    - Camera Zoom
    - Camera Shake
    - Dead Zone
    - Look-Ahead
    - Camera Reset
    - Full Maze View
    """

    def __init__(self, view_width: int, view_height: int) -> None:
        self.view_width = view_width
        self.view_height = view_height
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
        self.shake_intensity = 0.0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0
        self.look_ahead_x = 0.0
        self.look_ahead_y = 0.0
        self.full_maze_view = False
        self.active_mode_label = "Fixed"

    def set_viewport(self, view_width: int, view_height: int) -> None:
        self.view_width = max(320, view_width)
        self.view_height = max(240, view_height)

    def _should_use_fixed(
        self, prefer_fixed_maze: bool, settings: GameSettings
    ) -> bool:
        if self.full_maze_view:
            return True
        if settings.camera_mode == "fixed":
            return True
        if settings.camera_mode == "follow":
            return False
        return prefer_fixed_maze

    def reset(
        self,
        world_w: float,
        world_h: float,
        prefer_fixed_maze: bool,
        target_x: float,
        target_y: float,
        settings: GameSettings,
        full_maze_view: bool = False,
    ) -> None:
        self.full_maze_view = full_maze_view
        self.shake_intensity = 0.0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0
        self.look_ahead_x = 0.0
        self.look_ahead_y = 0.0

        fit_zoom = min(self.view_width / world_w, self.view_height / world_h) * 0.94
        if self._should_use_fixed(prefer_fixed_maze, settings):
            self.x = world_w / 2.0
            self.y = world_h / 2.0
            self.zoom = fit_zoom if full_maze_view else min(fit_zoom, settings.camera_zoom)
            self.active_mode_label = "Full Maze" if full_maze_view else "Fixed"
        else:
            self.zoom = settings.camera_zoom
            self.x = target_x
            self.y = target_y
            self._clamp_to_bounds(world_w, world_h)
            self.active_mode_label = "Smooth Follow"

    def trigger_shake(self, intensity: float, settings: GameSettings) -> None:
        if not settings.camera_shake:
            return
        self.shake_intensity = min(18.0, max(self.shake_intensity, intensity))

    def update(
        self,
        dt: float,
        world_w: float,
        world_h: float,
        prefer_fixed_maze: bool,
        target_x: float,
        target_y: float,
        target_facing: str,
        settings: GameSettings,
        full_maze_view: bool,
    ) -> None:
        self.full_maze_view = full_maze_view
        fit_zoom = min(self.view_width / world_w, self.view_height / world_h) * 0.94
        fixed = self._should_use_fixed(prefer_fixed_maze, settings)

        desired_zoom = (
            (fit_zoom if full_maze_view else min(fit_zoom, settings.camera_zoom))
            if fixed
            else settings.camera_zoom
        )
        zoom_lerp = 1.0 - math.exp(-8.0 * dt)
        self.zoom += (desired_zoom - self.zoom) * zoom_lerp

        if fixed:
            self.active_mode_label = "Full Maze" if full_maze_view else "Fixed"
            lerp = 1.0 - math.exp(-7.0 * dt)
            self.x += (world_w / 2.0 - self.x) * lerp
            self.y += (world_h / 2.0 - self.y) * lerp
            self.look_ahead_x *= 0.85
            self.look_ahead_y *= 0.85
        else:
            self.active_mode_label = "Smooth Follow"

            # Look-Ahead
            vx, vy = dir_to_vector(target_facing)
            look_dist = TILE_SIZE * 1.65 if settings.camera_look_ahead else 0.0
            la_lerp = 1.0 - math.exp(-4.5 * dt)
            self.look_ahead_x += (vx * look_dist - self.look_ahead_x) * la_lerp
            self.look_ahead_y += (vy * look_dist - self.look_ahead_y) * la_lerp

            desired_x = target_x + self.look_ahead_x
            desired_y = target_y + self.look_ahead_y

            # Dead Zone
            if settings.camera_dead_zone:
                dz_x = TILE_SIZE * 1.1
                dz_y = TILE_SIZE * 0.9
                dx = desired_x - self.x
                dy = desired_y - self.y
                if abs(dx) <= dz_x:
                    desired_x = self.x
                else:
                    desired_x = self.x + (dx - math.copysign(dz_x, dx))
                if abs(dy) <= dz_y:
                    desired_y = self.y
                else:
                    desired_y = self.y + (dy - math.copysign(dz_y, dy))

            follow_lerp = 1.0 - math.exp(-7.5 * dt)
            self.x += (desired_x - self.x) * follow_lerp
            self.y += (desired_y - self.y) * follow_lerp
            self._clamp_to_bounds(world_w, world_h)

        # Camera Shake decay
        if self.shake_intensity > 0.15:
            self.shake_offset_x = random.uniform(-1.0, 1.0) * self.shake_intensity
            self.shake_offset_y = random.uniform(-1.0, 1.0) * self.shake_intensity
            self.shake_intensity *= math.exp(-10.0 * dt)
        else:
            self.shake_intensity = 0.0
            self.shake_offset_x = 0.0
            self.shake_offset_y = 0.0

    def _clamp_to_bounds(self, world_w: float, world_h: float) -> None:
        half_vis_w = self.view_width / (2.0 * self.zoom)
        half_vis_h = self.view_height / (2.0 * self.zoom)
        pad = TILE_SIZE * 0.5

        if world_w + pad * 2 <= half_vis_w * 2:
            self.x = world_w / 2.0
        else:
            self.x = max(half_vis_w - pad, min(world_w - half_vis_w + pad, self.x))

        if world_h + pad * 2 <= half_vis_h * 2:
            self.y = world_h / 2.0
        else:
            self.y = max(half_vis_h - pad, min(world_h - half_vis_h + pad, self.y))

    def world_to_screen(self, wx: float, wy: float) -> Tuple[float, float]:
        cam_x = self.x + self.shake_offset_x
        cam_y = self.y + self.shake_offset_y
        sx = (wx - cam_x) * self.zoom + self.view_width / 2.0
        sy = (wy - cam_y) * self.zoom + self.view_height / 2.0
        return (sx, sy)
