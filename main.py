import asyncio
import random
import pygame
from constants import *
from arena import Arena
from ball_base import Ball
from ball_sword import SwordBall
from ball_gun import GunBall
from ball_tether import TetherBall
from ball_trap import TrapLayer
from particles import ParticleSystem
from hud import draw_hud


async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Ball Battles")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, HUD_FONT_SIZE)

    arena = Arena()
    particles = ParticleSystem()
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    shake_state = [0]

    # --- CHARACTER ROSTER (change these two lines to swap fighters) ---
    fighter_a = TrapLayer(
        pos=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2),
        color=(60, 180, 80),
        name="Trap"
    )
    fighter_b = SwordBall(
        pos=(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2),
        color=(200, 215, 255),
        name="Sword"
    )
    # ------------------------------------------------------------------

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if fighter_a.alive:
            fighter_a.update(dt, fighter_b, particles, shake_state)
        if fighter_b.alive:
            fighter_b.update(dt, fighter_a, particles, shake_state)

        fighter_a.ball_collision(fighter_b)

        game_surface.fill(BACKGROUND_COLOR)
        arena.draw(game_surface)
        particles.update(dt)
        particles.draw(game_surface)

        if fighter_a.alive:
            fighter_a.draw(game_surface)
        if fighter_b.alive:
            fighter_b.draw(game_surface)

        draw_hud(game_surface, fighter_a, fighter_b, font)

        if shake_state[0] > 0:
            offset = (
                random.randint(-SCREEN_SHAKE_MAGNITUDE, SCREEN_SHAKE_MAGNITUDE),
                random.randint(-SCREEN_SHAKE_MAGNITUDE, SCREEN_SHAKE_MAGNITUDE),
            )
            shake_state[0] -= 1
        else:
            offset = (0, 0)

        screen.fill((0, 0, 0))
        screen.blit(game_surface, offset)
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
