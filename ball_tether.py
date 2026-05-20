import math
import pygame
from constants import *
from ball_base import Ball


class TetherBall(Ball):
    def __init__(self, pos, color, name):
        super().__init__(pos, color, name)
        self.target_angle = 0.0
        self.current_angle = 0.0
        self.angular_velocity = 0.0
        self.weight_trail = []

    def on_wall_bounce(self):
        self.angular_velocity += TETHER_WHIP_BOOST

    def weapon_update(self, dt, enemy, particles, shake_state):
        if self.vel.length() > 0:
            self.target_angle = math.atan2(self.vel.y, self.vel.x)

        diff = self.target_angle - self.current_angle
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        self.current_angle += diff * TETHER_LAG_FACTOR + self.angular_velocity * dt
        self.angular_velocity *= 0.9

        weight_pos = self.pos + pygame.math.Vector2(
            math.cos(self.current_angle),
            math.sin(self.current_angle)
        ) * TETHER_ORBIT_RADIUS

        self.weight_trail.append(tuple(weight_pos))
        if len(self.weight_trail) > 5:
            self.weight_trail.pop(0)

        if enemy.alive and (enemy.pos - weight_pos).length() < BALL_RADIUS + TETHER_WEIGHT_RADIUS:
            enemy.take_damage(TETHER_DAMAGE, self)
            particles.emit_hit(weight_pos, enemy.color)
            shake_state[0] = SCREEN_SHAKE_FRAMES

    def weapon_draw(self, surface):
        weight_pos = self.pos + pygame.math.Vector2(
            math.cos(self.current_angle),
            math.sin(self.current_angle)
        ) * TETHER_ORBIT_RADIUS

        chain_vec = weight_pos - self.pos
        dist = chain_vec.length()
        if dist > 0:
            step_dir = chain_vec / dist
            t = 0.0
            draw = True
            while t < dist:
                if draw:
                    seg_end = min(t + 6, dist)
                    start = self.pos + step_dir * t
                    end = self.pos + step_dir * seg_end
                    pygame.draw.line(surface, (130, 130, 140),
                                     (int(start.x), int(start.y)),
                                     (int(end.x), int(end.y)), 2)
                t += 6 if draw else 4
                draw = not draw

        if self.weight_trail:
            for i, pos in enumerate(self.weight_trail):
                alpha = int(120 * (i / len(self.weight_trail)))
                r = 4
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (90, 60, 120, alpha), (r, r), r)
                surface.blit(s, (int(pos[0]) - r, int(pos[1]) - r))

        self.draw_glow(surface, weight_pos, TETHER_WEIGHT_RADIUS, (90, 60, 120))
        pygame.draw.circle(surface, (90, 60, 120),
                           (int(weight_pos.x), int(weight_pos.y)),
                           TETHER_WEIGHT_RADIUS)
