from __future__ import annotations

import math
from typing import Dict, List

import pygame

from audio import AudioManager
from camera import Camera
from collectibles import CollectibleKind, CollectibleManager
from enemy import ENEMY_PROFILES, HumanEnemy
from maze import Maze
from menu import HowToPlayScreen, MainMenuScreen, OverlayMenu, SettingsScreen
from player import DogPlayer
from settings import (
    COLORS,
    GameSettings,
    HUD_HEIGHT,
    HighScoreData,
    TILE_SIZE,
    load_highscore,
    load_settings,
    save_highscore,
    save_settings,
)
from ui import HUDRenderer, ParticleSystem


class DogChaseGame:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.settings: GameSettings = load_settings()
        self.highscore: HighScoreData = load_highscore()
        self.audio = AudioManager(self.settings)

        self.fonts = self._build_fonts()

        self.state = "MAIN_MENU"  # MAIN_MENU | HOW_TO_PLAY | SETTINGS | PLAYING | PAUSED | VICTORY | GAME_OVER
        self.settings_return_state = "MAIN_MENU"
        self.running = True

        self.score = 0
        self.lives = 3
        self.max_lives = 3
        self.level = 1
        self.bones_collected = 0
        self.total_bones = 0
        self.coins_collected = 0
        self.total_coins = 0
        self.full_maze_view = False
        self.is_new_highscore = False

        self.wave_timer = 0.0
        self.global_wave_state = "scatter"
        self.scare_combo = 0
        self.elapsed = 0.0

        self.maze = Maze(1)
        self.player = DogPlayer()
        self.enemies: List[HumanEnemy] = []
        self.collectibles = CollectibleManager()
        self.particles = ParticleSystem()
        self.hud = HUDRenderer()
        self.camera = Camera(screen.get_width(), max(240, screen.get_height() - HUD_HEIGHT))

        self.main_menu = MainMenuScreen(
            on_play=self.start_new_game,
            on_how_to_play=lambda: self._switch_state("HOW_TO_PLAY"),
            on_settings=lambda: self._open_settings("MAIN_MENU"),
            on_exit=self.quit_game,
        )
        self.how_to_play = HowToPlayScreen(on_back=lambda: self._switch_state("MAIN_MENU"))
        self.settings_screen = SettingsScreen(
            settings=self.settings,
            on_apply=self._apply_settings,
            on_back=lambda: self._switch_state(self.settings_return_state),
        )
        self.pause_menu = OverlayMenu(
            title="Game Paused",
            subtitle="Take a breather — the humans are waiting.",
            actions=[
                ("Resume", self.resume_game, True),
                ("Restart", self.start_new_game, False),
                ("Settings", lambda: self._open_settings("PAUSED"), False),
                ("Main Menu", self.return_to_menu, False),
            ],
        )
        self.victory_menu = OverlayMenu(
            title="Level Completed",
            subtitle="Every bone secured!",
            actions=[
                ("Next Level", self.next_level, True),
                ("Main Menu", self.return_to_menu, False),
            ],
        )
        self.gameover_menu = OverlayMenu(
            title="Game Over",
            subtitle="The neighborhood humans caught up.",
            actions=[
                ("Restart", self.start_new_game, True),
                ("Main Menu", self.return_to_menu, False),
                ("Exit", self.quit_game, False),
            ],
        )

        self.relayout()

    def _build_fonts(self) -> Dict[str, pygame.font.Font]:
        return {
            "hero": pygame.font.SysFont("arial", 46, bold=True),
            "title": pygame.font.SysFont("arial", 28, bold=True),
            "title_sm": pygame.font.SysFont("arial", 20, bold=True),
            "body": pygame.font.SysFont("arial", 17),
            "body_bold": pygame.font.SysFont("arial", 16, bold=True),
            "small": pygame.font.SysFont("arial", 14),
            "small_bold": pygame.font.SysFont("arial", 13, bold=True),
            "tiny": pygame.font.SysFont("arial", 11, bold=True),
            "mono": pygame.font.SysFont("consolas", 16, bold=True),
        }

    def relayout(self) -> None:
        w, h = self.screen.get_size()
        self.camera.set_viewport(w, max(240, h - HUD_HEIGHT))
        self.main_menu.layout(w, h)
        self.how_to_play.layout(w, h)
        self.settings_screen.layout(w, h)
        self.pause_menu.layout(w, h)
        self.victory_menu.layout(w, h)
        self.gameover_menu.layout(w, h)

    def _switch_state(self, next_state: str) -> None:
        self.state = next_state
        self.relayout()

    def _open_settings(self, return_to: str) -> None:
        self.settings_return_state = return_to
        self._switch_state("SETTINGS")

    def _apply_settings(self, updated: GameSettings, display_changed: bool) -> None:
        self.settings = updated
        save_settings(updated)
        self.audio.apply_settings(updated)
        if display_changed:
            flags = pygame.FULLSCREEN if updated.fullscreen else pygame.RESIZABLE
            w, h = updated.resolution
            try:
                self.screen = pygame.display.set_mode((w, h), flags)
            except pygame.error:
                pass
            self.relayout()

    def quit_game(self) -> None:
        self.audio.stop_music()
        self.running = False

    def start_new_game(self) -> None:
        self.score = 0
        self.lives = self.max_lives
        self.level = 1
        self.is_new_highscore = False
        self.full_maze_view = False
        self._load_level(1)
        self.state = "PLAYING"
        self.audio.start_music()

    def next_level(self) -> None:
        self.level += 1
        self.full_maze_view = False
        self._load_level(self.level)
        self.state = "PLAYING"
        self.audio.start_music()

    def resume_game(self) -> None:
        if self.state == "PAUSED":
            self.state = "PLAYING"
            self.audio.start_music()

    def pause_game(self) -> None:
        if self.state == "PLAYING":
            self.state = "PAUSED"
            self.audio.stop_music()
            self.relayout()

    def return_to_menu(self) -> None:
        self.audio.stop_music()
        self._switch_state("MAIN_MENU")

    def _load_level(self, level_number: int) -> None:
        self.maze = Maze(level_number)
        self.player.spawn(self.maze)
        self.enemies = []
        for idx, profile in enumerate(ENEMY_PROFILES):
            enemy = HumanEnemy(profile)
            enemy.spawn(self.maze.enemy_spawns[idx % len(self.maze.enemy_spawns)], self.maze)
            self.enemies.append(enemy)

        self.bones_collected = 0
        self.total_bones = sum(1 for c in self.maze.collectibles if c.kind == CollectibleKind.BONE)
        self.coins_collected = 0
        self.total_coins = sum(1 for c in self.maze.collectibles if c.kind == CollectibleKind.COIN)
        self.particles.clear()
        self.wave_timer = 0.0
        self.global_wave_state = "scatter"
        self.scare_combo = 0

        self.camera.reset(
            self.maze.world_width,
            self.maze.world_height,
            self.maze.prefer_fixed_camera,
            self.player.x,
            self.player.y,
            self.settings,
            self.full_maze_view,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.quit_game()
            return
        if event.type == pygame.VIDEORESIZE:
            self.relayout()

        if self.state == "MAIN_MENU":
            self.main_menu.handle_event(event)
            return
        if self.state == "HOW_TO_PLAY":
            self.how_to_play.handle_event(event)
            return
        if self.state == "SETTINGS":
            self.settings_screen.handle_event(event, *self.screen.get_size())
            return
        if self.state == "PAUSED":
            if event.type == pygame.KEYDOWN and event.key in self.settings.key_bindings.get("pause", []):
                self.resume_game()
                return
            self.pause_menu.handle_event(event)
            return
        if self.state == "VICTORY":
            self.victory_menu.handle_event(event)
            return
        if self.state == "GAME_OVER":
            self.gameover_menu.handle_event(event)
            return

        # PLAYING state
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hud.pause_rect.collidepoint(event.pos):
                self.pause_game()
                return
            if self.hud.mute_rect.collidepoint(event.pos):
                self.settings.muted = not self.settings.muted
                self._apply_settings(self.settings, False)
                return
            if self.hud.cam_rect.collidepoint(event.pos):
                self.full_maze_view = not self.full_maze_view
                return

        if event.type == pygame.KEYDOWN:
            kb = self.settings.key_bindings
            if event.key in kb.get("pause", []):
                self.pause_game()
            elif event.key in kb.get("full_view", []):
                self.full_maze_view = not self.full_maze_view
            elif event.key in kb.get("mute", []):
                self.settings.muted = not self.settings.muted
                self._apply_settings(self.settings, False)
            elif event.key in kb.get("up", []):
                self.player.queue_direction("up")
            elif event.key in kb.get("down", []):
                self.player.queue_direction("down")
            elif event.key in kb.get("left", []):
                self.player.queue_direction("left")
            elif event.key in kb.get("right", []):
                self.player.queue_direction("right")

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.state != "PLAYING":
            return

        # AI Wave cycle (Scatter <-> Chase)
        self.wave_timer += dt
        scatter_len = max(2.5, 5.0 - (self.level - 1) * 0.45)
        chase_len = 16.0 + (self.level - 1) * 2.0
        if self.global_wave_state == "scatter" and self.wave_timer >= scatter_len:
            self.global_wave_state = "chase"
            self.wave_timer = 0.0
        elif self.global_wave_state == "chase" and self.wave_timer >= chase_len:
            self.global_wave_state = "scatter"
            self.wave_timer = 0.0

        self.player.update(dt, self.maze)

        # Collectible checks
        ev = self.collectibles.try_collect(self.maze.collectibles, self.player.x, self.player.y)
        if ev is not None:
            self._add_score(ev.points)
            if ev.kind == CollectibleKind.BONE:
                self.bones_collected += 1
                self.highscore.total_bones_collected += 1
                self.audio.play("bone")
                if self.settings.graphics_quality == "high":
                    self.particles.spawn_burst(ev.world_x, ev.world_y, (254, 243, 199), 6)
            elif ev.kind == CollectibleKind.COIN:
                self.coins_collected += 1
                self.highscore.total_coins_collected += 1
                self.audio.play("coin")
                if self.settings.graphics_quality == "high":
                    self.particles.spawn_burst(ev.world_x, ev.world_y, (251, 191, 36), 12)
                self.particles.spawn_text(ev.world_x, ev.world_y - 12, "+50", (253, 224, 71))
            else:
                self.audio.play("powerup")
                self.scare_combo = 0
                self.player.activate_powerup(self.maze.powerup_duration)
                for enemy in self.enemies:
                    enemy.set_frightened()
                self.camera.trigger_shake(5.0, self.settings)
                if self.settings.graphics_quality == "high":
                    self.particles.spawn_burst(ev.world_x, ev.world_y, (245, 158, 11), 18)
                self.particles.spawn_text(ev.world_x, ev.world_y - 16, "ZOOMIES!", (251, 191, 36))

            save_highscore(self.highscore)

            if self.bones_collected >= self.total_bones:
                bonus = self.level * 250 + self.lives * 100
                self._add_score(bonus)
                self.highscore.best_level = max(self.highscore.best_level, self.level + 1)
                save_highscore(self.highscore)
                self.audio.stop_music()
                self.audio.play("level_complete")
                self.camera.trigger_shake(7.0, self.settings)
                self.victory_menu.subtitle = f"{self.maze.name} Cleared! (+{bonus} level bonus)"
                self._switch_state("VICTORY")
                return

        # Enemy updates and Dog <-> Human collision
        for enemy in self.enemies:
            enemy.update(dt, self.maze, self.player, self.global_wave_state, self.enemies)

        hit_radius = TILE_SIZE * 0.56
        for enemy in self.enemies:
            if enemy.state == "respawning":
                continue
            if math.hypot(self.player.x - enemy.x, self.player.y - enemy.y) <= hit_radius:
                if enemy.state == "frightened":
                    pts = 200 * (2 ** min(3, self.scare_combo))
                    self.scare_combo += 1
                    self._add_score(pts)
                    enemy.send_to_respawn()
                    self.audio.play("scare")
                    self.camera.trigger_shake(6.0, self.settings)
                    if self.settings.graphics_quality == "high":
                        self.particles.spawn_burst(enemy.x, enemy.y, (56, 189, 248), 16)
                    self.particles.spawn_text(enemy.x, enemy.y - 14, f"+{pts}", (56, 189, 248))
                elif self.player.invuln_timer <= 0.0:
                    self.lives -= 1
                    self.audio.play("hit")
                    self.camera.trigger_shake(12.0, self.settings)
                    if self.settings.graphics_quality == "high":
                        self.particles.spawn_burst(self.player.x, self.player.y, (239, 68, 68), 18)
                    self.particles.spawn_text(self.player.x, self.player.y - 16, "-1 LIFE", (248, 113, 113))

                    if self.lives <= 0:
                        self.lives = 0
                        self.audio.stop_music()
                        self.audio.play("game_over")
                        self._switch_state("GAME_OVER")
                        return

                    self.player.reset_position(self.maze)
                    for e in self.enemies:
                        e.reset_to_spawn(self.maze)
                    self.camera.reset(
                        self.maze.world_width,
                        self.maze.world_height,
                        self.maze.prefer_fixed_camera,
                        self.player.x,
                        self.player.y,
                        self.settings,
                        self.full_maze_view,
                    )
                    break

        self.particles.update(dt)
        self.camera.update(
            dt,
            self.maze.world_width,
            self.maze.world_height,
            self.maze.prefer_fixed_camera,
            self.player.x,
            self.player.y,
            self.player.facing,
            self.settings,
            self.full_maze_view,
        )

    def _add_score(self, points: int) -> None:
        self.score += points
        if self.score > self.highscore.high_score:
            self.highscore.high_score = self.score
            self.is_new_highscore = True
            save_highscore(self.highscore)

    def render(self) -> None:
        if self.state == "MAIN_MENU":
            self.main_menu.draw(self.screen, self.fonts, self.highscore, self.elapsed)
            return
        if self.state == "HOW_TO_PLAY":
            self.how_to_play.draw(self.screen, self.fonts)
            return
        if self.state == "SETTINGS":
            self.settings_screen.draw(self.screen, self.fonts)
            return

        # Gameplay viewport below HUD
        w, h = self.screen.get_size()
        self.screen.fill(COLORS["bg_dark"])
        game_area = self.screen.subsurface(pygame.Rect(0, HUD_HEIGHT, w, max(1, h - HUD_HEIGHT)))
        hq = self.settings.graphics_quality == "high"

        self.maze.draw(game_area, self.camera, high_quality=hq)
        self.collectibles.draw(game_area, self.maze.collectibles, self.camera, self.elapsed, high_quality=hq)
        self.player.draw(game_area, self.camera, self.elapsed, high_quality=hq)
        for enemy in self.enemies:
            enemy.draw(game_area, self.camera, self.elapsed, self.player.powerup_timer, high_quality=hq)
        self.particles.draw(game_area, self.camera, self.fonts["mono"])

        if self.player.has_powerup() and hq:
            pygame.draw.rect(game_area, COLORS["accent"], game_area.get_rect(), 4)

        self.hud.draw(
            self.screen,
            self.fonts,
            score=self.score,
            high_score=self.highscore.high_score,
            lives=self.lives,
            max_lives=self.max_lives,
            level=self.level,
            level_name=self.maze.name,
            bones_collected=self.bones_collected,
            total_bones=self.total_bones,
            powerup_remaining=self.player.powerup_timer,
            powerup_duration=self.player.powerup_duration,
            camera_label=self.camera.active_mode_label,
            muted=self.settings.muted,
        )

        if self.state == "PAUSED":
            self.pause_menu.draw(
                self.screen,
                self.fonts,
                f"Score: {self.score:,}  ·  Level {self.level}",
            )
        elif self.state == "VICTORY":
            badge = "  ·  NEW HIGH SCORE!" if self.is_new_highscore else ""
            self.victory_menu.draw(
                self.screen,
                self.fonts,
                f"Score: {self.score:,}  ·  Coins: {self.coins_collected}/{self.total_coins}{badge}",
            )
        elif self.state == "GAME_OVER":
            badge = " (NEW BEST!)" if self.is_new_highscore else ""
            self.gameover_menu.draw(
                self.screen,
                self.fonts,
                f"Final: {self.score:,}{badge}  ·  Best: {self.highscore.high_score:,}",
            )
