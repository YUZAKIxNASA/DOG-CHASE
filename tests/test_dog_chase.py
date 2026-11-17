from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

# Provide a lightweight pygame stub if pygame is not installed in headless CI
try:
    import pygame  # type: ignore
except ModuleNotFoundError:
    pg = types.ModuleType("pygame")
    pg.K_UP = 273
    pg.K_DOWN = 274
    pg.K_RIGHT = 275
    pg.K_LEFT = 276
    pg.K_w = 119
    pg.K_a = 97
    pg.K_s = 115
    pg.K_d = 100
    pg.K_ESCAPE = 27
    pg.K_p = 112
    pg.K_v = 118
    pg.K_m = 109
    pg.FULLSCREEN = 1
    pg.RESIZABLE = 2
    pg.SRCALPHA = 65536
    pg.QUIT = 256
    pg.VIDEORESIZE = 32778
    pg.KEYDOWN = 768
    pg.MOUSEBUTTONDOWN = 1025
    pg.MOUSEMOTION = 1024
    pg.error = RuntimeError

    class _DummyRect:
        def __init__(self, x=0, y=0, w=0, h=0):
            self.x, self.y, self.w, self.h = x, y, w, h

        @property
        def centerx(self):
            return self.x + self.w // 2

        @property
        def centery(self):
            return self.y + self.h // 2

        @property
        def right(self):
            return self.x + self.w

        @property
        def bottom(self):
            return self.y + self.h

        @property
        def topleft(self):
            return (self.x, self.y)

        def collidepoint(self, _pos):
            return False

        def inflate(self, dx, dy):
            return _DummyRect(self.x - dx // 2, self.y - dy // 2, self.w + dx, self.h + dy)

    class _DummySurface:
        def __init__(self, size=(1120, 720), *_args):
            self._size = size

        def get_size(self):
            return self._size

        def get_width(self):
            return self._size[0]

        def get_height(self):
            return self._size[1]

        def get_rect(self):
            return _DummyRect(0, 0, self._size[0], self._size[1])

        def fill(self, *_args):
            pass

        def blit(self, *_args):
            pass

        def set_alpha(self, *_args):
            pass

        def subsurface(self, rect):
            return _DummySurface((rect.w, rect.h))

    class _DummyFont:
        def render(self, *_args):
            return _DummySurface((60, 18))

    class _DummyVec2:
        def __init__(self, x=0.0, y=0.0):
            self.x, self.y = x, y

        def rotate(self, _deg):
            return _DummyVec2(self.x, self.y)

    pg.Rect = _DummyRect
    pg.Surface = _DummySurface
    pg.draw = types.SimpleNamespace(
        rect=lambda *_a, **_kw: None,
        circle=lambda *_a, **_kw: None,
        ellipse=lambda *_a, **_kw: None,
        line=lambda *_a, **_kw: None,
        polygon=lambda *_a, **_kw: None,
    )
    pg.math = types.SimpleNamespace(Vector2=_DummyVec2)
    pg.font = types.SimpleNamespace(SysFont=lambda *_args, **_kw: _DummyFont())
    pg.key = types.SimpleNamespace(name=lambda k: f"KEY_{k}")
    pg.mixer = types.SimpleNamespace(
        get_init=lambda: False,
        init=lambda **_kw: (_ for _ in ()).throw(pg.error("headless")),
        Sound=object,
        music=types.SimpleNamespace(
            load=lambda *_a: None,
            play=lambda *_a: None,
            stop=lambda: None,
            set_volume=lambda *_a: None,
        ),
    )
    sys.modules["pygame"] = pg

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audio import ensure_default_audio_assets  # noqa: E402
from camera import Camera  # noqa: E402
from collectibles import CollectibleKind, CollectibleManager  # noqa: E402
from enemy import ENEMY_PROFILES, HumanEnemy, find_next_direction_astar  # noqa: E402
from game import DogChaseGame  # noqa: E402
from maze import LEVEL_SPECS, Maze  # noqa: E402
from player import DogPlayer  # noqa: E402
from settings import GameSettings, TILE_SIZE  # noqa: E402


class TestDogChase(unittest.TestCase):
    def test_all_mazes_valid_and_reachable(self) -> None:
        for lvl in range(1, len(LEVEL_SPECS) + 2):
            maze = Maze(lvl)
            bones = [c for c in maze.collectibles if c.kind == CollectibleKind.BONE]
            coins = [c for c in maze.collectibles if c.kind == CollectibleKind.COIN]
            powers = [c for c in maze.collectibles if c.kind == CollectibleKind.POWERUP]
            self.assertGreater(len(bones), 50)
            self.assertGreaterEqual(len(coins), 4)
            self.assertEqual(len(powers), 4)
            self.assertTrue(maze.is_walkable(*maze.dog_spawn))

    def test_player_movement_and_wall_collision(self) -> None:
        maze = Maze(1)
        player = DogPlayer()
        player.spawn(maze)
        start_x, start_y = player.x, player.y

        # Move right into open corridor
        player.queue_direction("right")
        for _ in range(12):
            player.update(1.0 / 60.0, maze)
        self.assertGreater(player.x, start_x)

        # Ensure player never enters a wall tile
        for _ in range(120):
            player.update(1.0 / 60.0, maze)
            self.assertTrue(maze.is_walkable(player.tile_x, player.tile_y))

        # Test reverse direction
        player.queue_direction("left")
        prev_x = player.x
        player.update(1.0 / 60.0, maze)
        self.assertLessEqual(player.x, prev_x)
        _ = start_y

    def test_astar_and_enemy_states(self) -> None:
        maze = Maze(2)
        player = DogPlayer()
        player.spawn(maze)
        enemies = [HumanEnemy(p) for p in ENEMY_PROFILES]
        for idx, e in enumerate(enemies):
            e.spawn(maze.enemy_spawns[idx], maze)

        step = find_next_direction_astar(
            maze, enemies[0].tile_x, enemies[0].tile_y, player.tile_x, player.tile_y, "none"
        )
        self.assertIn(step, ("up", "down", "left", "right"))

        # Test frightened state & respawn transition
        player.activate_powerup(5.0)
        for e in enemies:
            e.set_frightened()
            e.update(0.05, maze, player, "chase", enemies)
            self.assertEqual(e.state, "frightened")

        enemies[0].send_to_respawn()
        self.assertEqual(enemies[0].state, "respawning")

    def test_collectibles_and_camera_modes(self) -> None:
        maze = Maze(1)
        cm = CollectibleManager()
        first = maze.collectibles[0]
        ev = cm.try_collect(
            maze.collectibles,
            (first.tile_x + 0.5) * TILE_SIZE,
            (first.tile_y + 0.5) * TILE_SIZE,
        )
        self.assertIsNotNone(ev)
        self.assertTrue(first.collected)

        settings = GameSettings()
        cam = Camera(1120, 656)
        cam.reset(
            maze.world_width,
            maze.world_height,
            maze.prefer_fixed_camera,
            TILE_SIZE * 5.0,
            TILE_SIZE * 5.0,
            settings,
            False,
        )
        self.assertEqual(cam.active_mode_label, "Fixed")

        large_maze = Maze(4)
        cam.update(
            0.1,
            large_maze.world_width,
            large_maze.world_height,
            large_maze.prefer_fixed_camera,
            TILE_SIZE * 10.0,
            TILE_SIZE * 10.0,
            "right",
            settings,
            False,
        )
        self.assertEqual(cam.active_mode_label, "Smooth Follow")

        cam.trigger_shake(10.0, settings)
        self.assertGreater(cam.shake_intensity, 0.0)

    def test_audio_wav_generation_and_game_state_machine(self) -> None:
        ensure_default_audio_assets()
        for name in ("bone.wav", "coin.wav", "powerup.wav", "scare.wav", "hit.wav", "level_complete.wav", "game_over.wav"):
            self.assertTrue((ROOT / "assets" / "sounds" / name).exists())
        self.assertTrue((ROOT / "assets" / "music" / "bgm.wav").exists())

        import pygame as pg

        screen = pg.Surface((1120, 720))
        game = DogChaseGame(screen)
        self.assertEqual(game.state, "MAIN_MENU")
        game.start_new_game()
        self.assertEqual(game.state, "PLAYING")
        game.pause_game()
        self.assertEqual(game.state, "PAUSED")
        game.resume_game()
        self.assertEqual(game.state, "PLAYING")
        game.update(0.016)
        game.render()


if __name__ == "__main__":
    unittest.main()
