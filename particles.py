import math
import random
import pygame
from constants import *


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.flashes = []

    def _spawn(self, pos, vel, color, radius, lifetime, gravity=0.0):
        self.particles.append({
            'pos': [pos[0], pos[1]],
            'vel': [vel[0], vel[1]],
            'color': color,
            'radius': radius,
            'lifetime': lifetime,
            'age': 0.0,
            'gravity': gravity,
        })
        if len(self.particles) > PARTICLE_MAX_COUNT:
            self.particles.pop(0)

    def update(self, dt):
        for p in self.particles:
            p['age'] += dt
            p['vel'][1] += p['gravity'] * dt
            p['pos'][0] += p['vel'][0] * dt
            p['pos'][1] += p['vel'][1] * dt
        self.particles = [p for p in self.particles if p['age'] < p['lifetime']]

        for f in self.flashes:
            f['radius'] += (f['max_radius'] - f['radius']) * MINE_FLASH_EXPAND_FACTOR
            f['frames'] -= 1
        self.flashes = [f for f in self.flashes if f['frames'] > 0]

    def draw(self, surface):
        for p in self.particles:
            alpha = int(255 * (1 - p['age'] / p['lifetime']))
            r = max(1, int(p['radius'] * (1 - p['age'] / p['lifetime'])))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p['color'], alpha), (r, r), r)
            surface.blit(s, (int(p['pos'][0]) - r, int(p['pos'][1]) - r))

        for f in self.flashes:
            alpha = int(255 * f['frames'] / MINE_FLASH_FRAMES)
            r = max(1, int(f['radius']))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, alpha), (r, r), r)
            surface.blit(s, (int(f['pos'][0]) - r, int(f['pos'][1]) - r))

    def emit_hit(self, pos, color):
        for _ in range(PARTICLE_COUNT_HIT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(PARTICLE_HIT_SPEED_MIN, PARTICLE_HIT_SPEED_MAX)
            self._spawn(pos, (math.cos(angle) * speed, math.sin(angle) * speed),
                        color, random.uniform(PARTICLE_HIT_RADIUS_MIN, PARTICLE_HIT_RADIUS_MAX), PARTICLE_LIFETIME)

    def emit_death(self, pos, color):
        for _ in range(PARTICLE_COUNT_DEATH):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(PARTICLE_DEATH_SPEED_MIN, PARTICLE_DEATH_SPEED_MAX)
            self._spawn(pos, (math.cos(angle) * speed, math.sin(angle) * speed),
                        color, random.uniform(PARTICLE_DEATH_RADIUS_MIN, PARTICLE_DEATH_RADIUS_MAX),
                        DEATH_PARTICLE_LIFETIME, gravity=PARTICLE_DEATH_GRAVITY)

    def emit_mine(self, pos):
        for _ in range(PARTICLE_COUNT_MINE):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(PARTICLE_MINE_SPEED_MIN, PARTICLE_MINE_SPEED_MAX)
            self._spawn(pos, (math.cos(angle) * speed, math.sin(angle) * speed),
                        MINE_PARTICLE_COLOR, random.uniform(PARTICLE_MINE_RADIUS_MIN, PARTICLE_MINE_RADIUS_MAX),
                        PARTICLE_LIFETIME)
        self.flashes.append({
            'pos': (pos[0], pos[1]),
            'radius': MINE_FLASH_START_RADIUS,
            'max_radius': MINE_FLASH_MAX_RADIUS,
            'frames': MINE_FLASH_FRAMES,
        })

    def emit_bullet_spark(self, pos):
        for _ in range(PARTICLE_COUNT_SPARK):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(PARTICLE_SPARK_SPEED_MIN, PARTICLE_SPARK_SPEED_MAX)
            self._spawn(pos, (math.cos(angle) * speed, math.sin(angle) * speed),
                        BULLET_COLOR, PARTICLE_SPARK_RADIUS, PARTICLE_SPARK_LIFETIME)
