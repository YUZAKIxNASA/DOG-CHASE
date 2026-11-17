from __future__ import annotations

import sys

import pygame

from game import DogChaseGame
from settings import load_settings


def main() -> None:
    pygame.init()
    settings = load_settings()
    flags = pygame.FULLSCREEN if settings.fullscreen else pygame.RESIZABLE
    screen = pygame.display.set_mode(settings.resolution, flags)
    pygame.display.set_caption("DOG CHASE — Arcade Maze Chase")

    clock = pygame.time.Clock()
    game = DogChaseGame(screen)

    while game.running:
        dt = min(0.05, clock.tick(game.settings.fps_limit) / 1000.0)
        for event in pygame.event.get():
            game.handle_event(event)
        game.update(dt)
        game.render()
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
