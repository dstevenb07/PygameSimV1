from constants import *


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.flashes = []

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def emit_hit(self, pos, color):
        pass

    def emit_death(self, pos, color):
        pass

    def emit_mine(self, pos):
        pass

    def emit_bullet_spark(self, pos):
        pass
