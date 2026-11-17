from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from camera import Camera, dir_to_vector
from maze import Maze
from player import DogPlayer, opposite_dir
from settings import ASSETS_DIR, TILE_SIZE, load_optional_sprite


def manhattan_wrapped(ax: int, ay: int, bx: int, by: int, width: int) -> int:
    dx = abs(ax - bx)
    wrapped_dx = min(dx, width - dx)
    return wrapped_dx + abs(ay - by)


def find_next_direction_astar(
    maze: Maze,
    start_x: int,
    start_y: int,
    goal_x: int,
    goal_y: int,
    current_dir: str,
) -> str:
    sx = maze.wrap_x(start_x)
    sy = max(0, min(maze.height - 1, start_y))
    gx = maze.wrap_x(goal_x)
    gy = max(0, min(maze.height - 1, goal_y))

    if sx == gx and sy == gy:
        return "right" if current_dir == "none" else current_dir

    start = (sx, sy)
    goal = (gx, gy)
    heap: List[Tuple[float, int, Tuple[int, int]]] = [
        (float(manhattan_wrapped(sx, sy, gx, gy, maze.width)), 0, start)
    ]
    g_score: Dict[Tuple[int, int], float] = {start: 0.0}
    came_from: Dict[Tuple[int, int], Tuple[Tuple[int, int], str]] = {}
    closed = set()

    closest_node = start
    closest_dist = manhattan_wrapped(sx, sy, gx, gy, maze.width)
    counter = 1
    max_iters = maze.width * maze.height * 2
    iters = 0

    dirs = (("up", 0, -1), ("right", 1, 0), ("down", 0, 1), ("left", -1, 0))

    while heap and iters < max_iters:
        iters += 1
        _, _, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        if cur == goal:
            closest_node = goal
            break
        closed.add(cur)

        dist = manhattan_wrapped(cur[0], cur[1], gx, gy, maze.width)
        if dist < closest_dist:
            closest_dist = dist
            closest_node = cur

        cur_g = g_score[cur]
        for d_name, dx, dy in dirs:
            raw_nx = cur[0] + dx
            ny = cur[1] + dy
            if not maze.is_walkable(raw_nx, ny):
                continue
            nxt = (maze.wrap_x(raw_nx), ny)
            if nxt in closed:
                continue

            turn_penalty = 1.5 if (cur == start and opposite_dir(current_dir) == d_name) else 0.0
            tentative_g = cur_g + 1.0 + turn_penalty
            if tentative_g < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative_g
                came_from[nxt] = (cur, d_name)
                f = tentative_g + manhattan_wrapped(nxt[0], nxt[1], gx, gy, maze.width)
                counter += 1
                heapq.heappush(heap, (f, counter, nxt))

    trace = closest_node
    step_dir: Optional[str] = None
    guard = 0
    while trace != start and guard < max_iters:
        guard += 1
        if trace not in came_from:
            break
        parent, d_name = came_from[trace]
        step_dir = d_name
        trace = parent

    if step_dir is not None:
        return step_dir

    for d_name, dx, dy in dirs:
        if d_name != opposite_dir(current_dir) and maze.is_walkable(sx + dx, sy + dy):
            return d_name
    for d_name, dx, dy in dirs:
        if maze.is_walkable(sx + dx, sy + dy):
            return d_name
    return "none"


@dataclass(frozen=True)
class EnemyProfile:
    enemy_id: str
    name: str
    role: str
    shirt_color: Tuple[int, int, int]
    hat_color: Tuple[int, int, int]
    skin_color: Tuple[int, int, int]
    scatter_corner: Callable[[Maze], Tuple[int, int]]


ENEMY_PROFILES: List[EnemyProfile] = [
    EnemyProfile(
        enemy_id="miller",
        name="Officer Miller",
        role="Direct Chaser",
        shirt_color=(37, 99, 235),
        hat_color=(29, 78, 216),
        skin_color=(245, 203, 167),
        scatter_corner=lambda m: (m.width - 2, 1),
    ),
    EnemyProfile(
        enemy_id="rosa",
        name="Chef Rosa",
        role="Corridor Ambusher",
        shirt_color=(220, 38, 38),
        hat_color=(248, 250, 252),
        skin_color=(238, 184, 146),
        scatter_corner=lambda _m: (1, 1),
    ),
    EnemyProfile(
        enemy_id="leo",
        name="Jogger Leo",
        role="Vector Flanker",
        shirt_color=(22, 163, 74),
        hat_color=(34, 197, 94),
        skin_color=(212, 154, 106),
        scatter_corner=lambda m: (m.width - 2, m.height - 2),
    ),
    EnemyProfile(
        enemy_id="vance",
        name="Inspector Vance",
        role="Tactical Patroller",
        shirt_color=(217, 119, 6),
        hat_color=(146, 64, 14),
        skin_color=(240, 196, 160),
        scatter_corner=lambda m: (1, m.height - 2),
    ),
]


class HumanEnemy:
    def __init__(self, profile: EnemyProfile) -> None:
        self.profile = profile
        self.x = 0.0
        self.y = 0.0
        self.tile_x = 0
        self.tile_y = 0
        self.spawn_tx = 0
        self.spawn_ty = 0
        self.dir = "left"
        self.state = "chase"  # "chase" | "scatter" | "frightened" | "respawning"
        self.walk_cycle = 0.0
        self.respawn_timer = 0.0
        self.base_speed = TILE_SIZE * 4.15
        self._last_decision_tile: Optional[Tuple[int, int]] = None

        self.sprite: Optional[pygame.Surface] = load_optional_sprite(
            ASSETS_DIR / "enemies" / f"{profile.enemy_id}.png", (32, 34)
        )

    def spawn(self, tile: Tuple[int, int], maze: Maze) -> None:
        self.spawn_tx, self.spawn_ty = tile
        self.reset_to_spawn(maze)

    def reset_to_spawn(self, maze: Maze) -> None:
        self.tile_x = self.spawn_tx
        self.tile_y = self.spawn_ty
        self.x = (self.tile_x + 0.5) * TILE_SIZE
        self.y = (self.tile_y + 0.5) * TILE_SIZE
        self.dir = "none"
        self.state = "chase"
        self.respawn_timer = 0.0
        self._last_decision_tile = None
        self.base_speed = TILE_SIZE * 4.15 * maze.enemy_speed_multiplier

    def set_frightened(self) -> None:
        if self.state == "respawning":
            return
        self.state = "frightened"
        self._last_decision_tile = None
        if self.dir != "none":
            self.dir = opposite_dir(self.dir)

    def send_to_respawn(self) -> None:
        self.state = "respawning"
        self.respawn_timer = 2.4
        self._last_decision_tile = None

    def update(
        self,
        dt: float,
        maze: Maze,
        player: DogPlayer,
        global_wave_state: str,
        all_enemies: List["HumanEnemy"],
    ) -> None:
        if self.state == "respawning":
            self.respawn_timer -= dt
            if self.respawn_timer <= 0.0 and (self.tile_x, self.tile_y) == (self.spawn_tx, self.spawn_ty):
                self.state = "frightened" if player.has_powerup() else global_wave_state
                self._last_decision_tile = None
        elif player.has_powerup():
            self.state = "frightened"
        else:
            self.state = global_wave_state

        speed = self.base_speed
        if self.state == "frightened":
            speed *= 0.66
        elif self.state == "respawning":
            speed *= 1.55

        step = speed * dt
        cur_tx = maze.wrap_x(int(self.x // TILE_SIZE))
        cur_ty = max(0, min(maze.height - 1, int(self.y // TILE_SIZE)))
        center_x = (cur_tx + 0.5) * TILE_SIZE
        center_y = (cur_ty + 0.5) * TILE_SIZE
        dist = math.hypot(self.x - center_x, self.y - center_y)

        tile_key = (cur_tx, cur_ty)
        should_decide = (
            self.dir == "none"
            or (dist <= max(step + 2.0, 4.5) and self._last_decision_tile != tile_key)
        )

        if should_decide:
            self.x = center_x
            self.y = center_y
            self.tile_x = cur_tx
            self.tile_y = cur_ty
            self._last_decision_tile = tile_key
            chosen = self._choose_next_direction(maze, player, all_enemies)
            if chosen != "none":
                self.dir = chosen

            if (
                self.state == "respawning"
                and (self.tile_x, self.tile_y) == (self.spawn_tx, self.spawn_ty)
                and self.respawn_timer <= 0.0
            ):
                self.state = "frightened" if player.has_powerup() else global_wave_state

        if self.dir == "none":
            return

        vx, vy = dir_to_vector(self.dir)
        if not maze.is_walkable(cur_tx + vx, cur_ty + vy) and dist <= step + 1.0:
            self.x = center_x
            self.y = center_y
            self.dir = self._choose_next_direction(maze, player, all_enemies)
            return

        self.x += vx * step
        self.y += vy * step

        if self.x < 0:
            self.x += maze.world_width
        elif self.x >= maze.world_width:
            self.x -= maze.world_width

        self.tile_x = maze.wrap_x(int(self.x // TILE_SIZE))
        self.tile_y = max(0, min(maze.height - 1, int(self.y // TILE_SIZE)))
        self.walk_cycle += dt * (8.0 if self.state == "frightened" else 11.0)

    def _choose_next_direction(
        self, maze: Maze, player: DogPlayer, all_enemies: List["HumanEnemy"]
    ) -> str:
        if self.state == "respawning":
            return find_next_direction_astar(
                maze, self.tile_x, self.tile_y, self.spawn_tx, self.spawn_ty, self.dir
            )

        if self.state == "frightened":
            best_dir = "none"
            best_score = -float("inf")
            for d_name in ("up", "right", "down", "left"):
                vx, vy = dir_to_vector(d_name)
                nx, ny = self.tile_x + vx, self.tile_y + vy
                if not maze.is_walkable(nx, ny):
                    continue
                score = float(
                    manhattan_wrapped(maze.wrap_x(nx), ny, player.tile_x, player.tile_y, maze.width)
                )
                if d_name == opposite_dir(self.dir):
                    score -= 1.2
                score += random.uniform(0.0, 0.6)
                if score > best_score:
                    best_score = score
                    best_dir = d_name
            return best_dir

        if self.state == "scatter":
            cx, cy = self.profile.scatter_corner(maze)
            return find_next_direction_astar(maze, self.tile_x, self.tile_y, cx, cy, self.dir)

        tx, ty = self._compute_chase_target(maze, player, all_enemies)
        return find_next_direction_astar(maze, self.tile_x, self.tile_y, tx, ty, self.dir)

    def _compute_chase_target(
        self, maze: Maze, player: DogPlayer, all_enemies: List["HumanEnemy"]
    ) -> Tuple[int, int]:
        px, py = dir_to_vector(player.facing)
        eid = self.profile.enemy_id

        if eid == "miller":
            return (player.tile_x, player.tile_y)
        if eid == "rosa":
            tx = maze.wrap_x(player.tile_x + px * 4)
            ty = max(1, min(maze.height - 2, player.tile_y + py * 4))
            return self._nearest_walkable(maze, tx, ty)
        if eid == "leo":
            miller = next((e for e in all_enemies if e.profile.enemy_id == "miller"), None)
            ax = player.tile_x + px * 2
            ay = player.tile_y + py * 2
            if miller is not None:
                tx = maze.wrap_x(ax + (ax - miller.tile_x))
                ty = max(1, min(maze.height - 2, ay + (ay - miller.tile_y)))
                return self._nearest_walkable(maze, tx, ty)
            return (player.tile_x, player.tile_y)

        # Inspector Vance: chases when far, retreats to patrol corner when close
        dist = manhattan_wrapped(self.tile_x, self.tile_y, player.tile_x, player.tile_y, maze.width)
        if dist > 6:
            return (player.tile_x, player.tile_y)
        return self.profile.scatter_corner(maze)

    def _nearest_walkable(self, maze: Maze, tx: int, ty: int) -> Tuple[int, int]:
        if maze.is_walkable(tx, ty):
            return (tx, ty)
        for r in range(1, 5):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx = maze.wrap_x(tx + dx)
                    ny = max(1, min(maze.height - 2, ty + dy))
                    if maze.is_walkable(nx, ny):
                        return (nx, ny)
        return maze.dog_spawn

    def draw(
        self,
        surface: pygame.Surface,
        camera: Camera,
        elapsed: float,
        powerup_remaining: float,
        high_quality: bool = True,
    ) -> None:
        sx, sy = camera.world_to_screen(self.x, self.y)
        z = camera.zoom
        is_frightened = self.state == "frightened"
        is_respawning = self.state == "respawning"

        if self.sprite is not None and not is_frightened and not is_respawning:
            w = max(12, int(32 * z))
            h = max(12, int(34 * z))
            scaled = pygame.transform.smoothscale(self.sprite, (w, h))
            surface.blit(scaled, (int(sx - w / 2), int(sy - h / 2)))
            return

        walk = math.sin(self.walk_cycle)
        bob = abs(walk) * 1.8 * z
        cy = sy - bob

        # Shadow
        sh_w, sh_h = max(6, int(20 * z)), max(3, int(9 * z))
        sh = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 85), sh.get_rect())
        surface.blit(sh, (int(sx - sh_w / 2), int(sy + 9 * z)))

        flash_white = (
            is_frightened and powerup_remaining < 2.0 and int(elapsed * 10) % 2 == 0
        )
        shirt = (
            (226, 232, 240)
            if flash_white
            else (59, 130, 246)
            if is_frightened
            else self.profile.shirt_color
        )
        skin = (219, 234, 254) if is_frightened else self.profile.skin_color

        alpha = 95 if is_respawning else 255
        char_surf = pygame.Surface((max(16, int(38 * z)), max(20, int(46 * z))), pygame.SRCALPHA)
        ox, oy = char_surf.get_width() / 2.0, char_surf.get_height() * 0.58

        # Legs
        pygame.draw.rect(
            char_surf,
            (30, 41, 59, alpha),
            pygame.Rect(int(ox - 6 * z), int(oy + (5 + walk * 2.5) * z), max(2, int(4.5 * z)), max(3, int(8 * z))),
            border_radius=2,
        )
        pygame.draw.rect(
            char_surf,
            (30, 41, 59, alpha),
            pygame.Rect(int(ox + 1.5 * z), int(oy + (5 - walk * 2.5) * z), max(2, int(4.5 * z)), max(3, int(8 * z))),
            border_radius=2,
        )

        # Torso & swinging arms
        torso = pygame.Rect(int(ox - 9 * z), int(oy - 4 * z), max(6, int(18 * z)), max(5, int(12 * z)))
        pygame.draw.rect(char_surf, (*shirt, alpha), torso, border_radius=max(2, int(4 * z)))
        pygame.draw.rect(char_surf, (15, 23, 42, alpha), torso, max(1, int(1.4 * z)), border_radius=max(2, int(4 * z)))

        pygame.draw.rect(
            char_surf,
            (*shirt, alpha),
            pygame.Rect(int(ox - 12 * z), int(oy - (2 + walk * 2.2) * z), max(2, int(3.5 * z)), max(3, int(8 * z))),
            border_radius=2,
        )
        pygame.draw.rect(
            char_surf,
            (*shirt, alpha),
            pygame.Rect(int(ox + 8.5 * z), int(oy - (2 - walk * 2.2) * z), max(2, int(3.5 * z)), max(3, int(8 * z))),
            border_radius=2,
        )

        # Head
        head_y = int(oy - 9.5 * z)
        head_r = max(3, int(7.2 * z))
        pygame.draw.circle(char_surf, (*skin, alpha), (int(ox), head_y), head_r)
        pygame.draw.circle(char_surf, (15, 23, 42, alpha), (int(ox), head_y), head_r, max(1, int(1.3 * z)))

        if is_frightened:
            pygame.draw.circle(char_surf, (15, 23, 42, alpha), (int(ox - 2.5 * z), head_y), max(1, int(1.5 * z)), 1)
            pygame.draw.circle(char_surf, (15, 23, 42, alpha), (int(ox + 2.5 * z), head_y), max(1, int(1.5 * z)), 1)
            if high_quality:
                pygame.draw.circle(char_surf, (56, 189, 248, alpha), (int(ox + 9 * z), int(oy - 13 * z)), max(1, int(2.2 * z)))
        else:
            lx = -1.2 if self.dir == "left" else 1.2 if self.dir == "right" else 0.0
            ly = -1.2 if self.dir == "up" else 0.8 if self.dir == "down" else 0.0
            pygame.draw.circle(char_surf, (15, 23, 42, alpha), (int(ox + (-2.4 + lx) * z), int(head_y + ly * z)), max(1, int(1.4 * z)))
            pygame.draw.circle(char_surf, (15, 23, 42, alpha), (int(ox + (2.4 + lx) * z), int(head_y + ly * z)), max(1, int(1.4 * z)))

        # Distinct headgear per Human Character
        if not is_frightened and not is_respawning:
            eid = self.profile.enemy_id
            if eid == "miller":
                pygame.draw.rect(
                    char_surf,
                    self.profile.hat_color,
                    pygame.Rect(int(ox - 7 * z), int(oy - 17 * z), max(4, int(14 * z)), max(3, int(5 * z))),
                    border_radius=3,
                )
                pygame.draw.rect(
                    char_surf,
                    (15, 23, 42),
                    pygame.Rect(int(ox - 7.5 * z), int(oy - 13.5 * z), max(4, int(15 * z)), max(1, int(2.2 * z))),
                )
            elif eid == "rosa":
                pygame.draw.rect(
                    char_surf,
                    (248, 250, 252),
                    pygame.Rect(int(ox - 6 * z), int(oy - 21 * z), max(4, int(12 * z)), max(3, int(7.5 * z))),
                    border_radius=3,
                )
            elif eid == "leo":
                pygame.draw.rect(
                    char_surf,
                    (34, 197, 94),
                    pygame.Rect(int(ox - 7.2 * z), int(oy - 13.5 * z), max(4, int(14.4 * z)), max(2, int(2.8 * z))),
                )
            elif eid == "vance":
                pygame.draw.rect(
                    char_surf,
                    self.profile.hat_color,
                    pygame.Rect(int(ox - 9.5 * z), int(oy - 14 * z), max(5, int(19 * z)), max(2, int(2.4 * z))),
                )
                pygame.draw.rect(
                    char_surf,
                    self.profile.hat_color,
                    pygame.Rect(int(ox - 5.5 * z), int(oy - 19 * z), max(4, int(11 * z)), max(3, int(5.5 * z))),
                    border_radius=2,
                )

        surface.blit(char_surf, (int(sx - ox), int(cy - oy)))
