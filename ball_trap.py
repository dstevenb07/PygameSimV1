import math
import pygame
from constants import *
from ball_base import Ball


class Mine:
    def __init__(self, pos):
        self.pos = pygame.math.Vector2(pos)
        self.age = 0.0
        self.alive = True
        self.alpha = 255


class TrapLayer(Ball):
    def __init__(self, pos, color, name):
        super().__init__(pos, color, name)
        self.mine_timer = MINE_DROP_INTERVAL
        self.mines = []
        self.trail = []

    def weapon_update(self, dt, enemy, particles, shake_state):
        self.trail.append(tuple(self.pos))
        if len(self.trail) > TRAP_TRAIL_LENGTH:
            self.trail.pop(0)

        self.mine_timer -= dt
        if self.mine_timer <= 0:
            self.mine_timer = MINE_DROP_INTERVAL
            self.mines.append(Mine(self.pos))

        for mine in self.mines:
            mine.age += dt
            if mine.age >= MINE_FADE_START:
                t = (mine.age - MINE_FADE_START) / (MINE_LIFETIME - MINE_FADE_START)
                mine.alpha = int(255 * (1 - t))
            if mine.age >= MINE_LIFETIME:
                mine.alive = False
                continue
            if enemy.alive and (enemy.pos - mine.pos).length() < MINE_PROXIMITY_RADIUS:
                enemy.take_damage(MINE_DAMAGE, mine)
                particles.emit_mine(mine.pos)
                shake_state[0] = SCREEN_SHAKE_FRAMES
                mine.alive = False

        self.mines = [m for m in self.mines if m.alive]

    def weapon_draw(self, surface):
        for i, pos in enumerate(self.trail):
            alpha = int(TRAP_TRAIL_ALPHA_MIN + (TRAP_TRAIL_ALPHA_MAX - TRAP_TRAIL_ALPHA_MIN) * (i / len(self.trail)))
            s = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
            surface.blit(s, (int(pos[0]) - BALL_RADIUS, int(pos[1]) - BALL_RADIUS))

        for mine in self.mines:
            alpha = mine.alpha
            mine_draw_pos = (int(mine.pos.x) - MINE_RADIUS, int(mine.pos.y) - MINE_RADIUS)
            s = pygame.Surface((MINE_RADIUS * 2, MINE_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*MINE_COLOR, alpha), (MINE_RADIUS, MINE_RADIUS), MINE_RADIUS)
            surface.blit(s, mine_draw_pos)

            pulse_alpha = int(MINE_RING_ALPHA_BASE + MINE_RING_ALPHA_AMP * math.sin(mine.age * MINE_PULSE_SPEED))
            ring_draw_pos = (int(mine.pos.x) - MINE_PROXIMITY_RADIUS,
                             int(mine.pos.y) - MINE_PROXIMITY_RADIUS)
            ring_surf = pygame.Surface(
                (MINE_PROXIMITY_RADIUS * 2, MINE_PROXIMITY_RADIUS * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(
                ring_surf, (*MINE_RING_COLOR, int(pulse_alpha * alpha / 255)),
                (MINE_PROXIMITY_RADIUS, MINE_PROXIMITY_RADIUS), MINE_PROXIMITY_RADIUS, 1
            )
            surface.blit(ring_surf, ring_draw_pos)
