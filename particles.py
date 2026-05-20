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
        if len(self.particles) > 150:
            self.particles.pop(0)

    def update(self, dt):
        for p in self.particles:
            p['age'] += dt
            p['vel'][1] += p['gravity'] * dt
            p['pos'][0] += p['vel'][0] * dt
            p['pos'][1] += p['vel'][1] * dt
        self.particles = [p for p in self.particles if p['age'] < p['lifetime']]

        for f in self.flashes:
            f['radius'] += (f['max_radius'] - f['radius']) * 0.8
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
            alpha = int(255 * f['frames'] / 3)
            r = max(1, int(f['radius']))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, alpha), (r, r), r)
            surface.blit(s, (int(f['pos'][0]) - r, int(f['pos'][1]) - r))

    def emit_hit(self, pos, color):
        for _ in range(PARTICLE_COUNT_HIT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 120)
            self._spawn(pos, (math.cos(angle) * speed, math.sin(angle) * speed),
                        color, random.uniform(3, 5), PARTICLE_LIFETIME)

    def emit_death(self, pos, color):
        for _ in range(PARTICLE_COUNT_DEATH):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150, 300)
            self._spawn(pos, (math.cos(angle) * speed, math.sin(angle) * speed),
                        color, random.uniform(4, 7), DEATH_PARTICLE_LIFETIME, gravity=150.0)

    def emit_mine(self, pos):
        for _ in range(PARTICLE_COUNT_MINE):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 200)
            self._spawn(pos, (math.cos(angle) * speed, math.sin(angle) * speed),
                        (220, 80, 30), random.uniform(3, 6), PARTICLE_LIFETIME)
        self.flashes.append({
            'pos': (pos[0], pos[1]),
            'radius': 5.0,
            'max_radius': 40,
            'frames': 3,
        })

    def emit_bullet_spark(self, pos):
        for _ in range(3):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150, 250)
            self._spawn(pos, (math.cos(angle) * speed, math.sin(angle) * speed),
                        (255, 200, 80), 3, 0.2)
