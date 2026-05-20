import math
import pygame
from constants import *
from ball_base import Ball


def _segment_circle_hit(p1, p2, center, radius):
    seg = p2 - p1
    to_c = center - p1
    seg_len_sq = seg.length_squared()
    if seg_len_sq == 0:
        return (center - p1).length() < radius, p1
    t = max(0.0, min(1.0, to_c.dot(seg) / seg_len_sq))
    closest = p1 + seg * t
    return (center - closest).length() < radius, closest


def _sword_polygon(base, tip, width):
    direction = (tip - base).normalize()
    perp = pygame.math.Vector2(-direction.y, direction.x) * (width / 2)
    return [base + perp, tip + perp, tip - perp, base - perp]


class SwordBall(Ball):
    def __init__(self, pos, color, name):
        super().__init__(pos, color, name)
        self.sword_angle = 0.0

    def weapon_update(self, dt, enemy, particles, shake_state):
        self.sword_angle = (self.sword_angle + SWORD_ROTATION_SPEED) % 360
        angle_rad = math.radians(self.sword_angle)
        direction = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))

        base = self.pos + direction * SWORD_ORBIT_RADIUS
        tip = self.pos + direction * (SWORD_ORBIT_RADIUS + SWORD_LENGTH)

        if enemy.alive:
            hit, closest = _segment_circle_hit(base, tip, enemy.pos, BALL_RADIUS)
            if hit:
                enemy.take_damage(SWORD_DAMAGE, self)
                particles.emit_hit(closest, enemy.color)
                shake_state[0] = SCREEN_SHAKE_FRAMES

    def weapon_draw(self, surface):
        angle_rad = math.radians(self.sword_angle)
        direction = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))

        base = self.pos + direction * SWORD_ORBIT_RADIUS
        tip = self.pos + direction * (SWORD_ORBIT_RADIUS + SWORD_LENGTH)

        points = _sword_polygon(base, tip, SWORD_WIDTH)
        pygame.draw.polygon(surface, SWORD_COLOR, points)
        self.draw_glow(surface, tip, SWORD_GLOW_RADIUS, SWORD_TIP_COLOR)
