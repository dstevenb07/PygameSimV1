import math
import pygame
from constants import *
from ball_base import Ball


class Bullet:
    def __init__(self, pos, vel):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.distance_travelled = 0.0
        self.alive = True
        self.trail = []  # last 4 positions


def _bullet_polygon(pos, vel_dir, length, width):
    perp = pygame.math.Vector2(-vel_dir.y, vel_dir.x) * (width / 2)
    front = pos + vel_dir * (length / 2)
    back = pos - vel_dir * (length / 2)
    return [front + perp, front - perp, back - perp, back + perp]


class GunBall(Ball):
    def __init__(self, pos, color, name):
        super().__init__(pos, color, name)
        self.fire_timer = GUN_FIRE_INTERVAL
        self.bullets = []
        self.barrel_angle = 0.0
        self.muzzle_flash_frames = 0

    def weapon_update(self, dt, enemy, particles, shake_state):
        delta = enemy.pos - self.pos
        self.barrel_angle = math.atan2(delta.y, delta.x)

        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = GUN_FIRE_INTERVAL
            self.muzzle_flash_frames = 3
            direction = pygame.math.Vector2(
                math.cos(self.barrel_angle), math.sin(self.barrel_angle)
            )
            spawn_pos = self.pos + direction * (BALL_RADIUS + 2)
            self.bullets.append(Bullet(spawn_pos, direction * BULLET_SPEED))

        for bullet in self.bullets:
            bullet.trail.append(tuple(bullet.pos))
            if len(bullet.trail) > 4:
                bullet.trail.pop(0)

            bullet.pos += bullet.vel
            bullet.distance_travelled += BULLET_SPEED

            if bullet.pos.x - 2 < 0 or bullet.pos.x + 2 > SCREEN_WIDTH:
                bullet.vel.x *= -1
                bullet.pos.x = max(2, min(SCREEN_WIDTH - 2, bullet.pos.x))
            if bullet.pos.y - 2 < 0 or bullet.pos.y + 2 > SCREEN_HEIGHT:
                bullet.vel.y *= -1
                bullet.pos.y = max(2, min(SCREEN_HEIGHT - 2, bullet.pos.y))
            bullet.vel = bullet.vel.normalize() * BULLET_SPEED

            if bullet.distance_travelled >= BULLET_MAX_DISTANCE:
                bullet.alive = False
                continue

            if enemy.alive and (enemy.pos - bullet.pos).length() < BALL_RADIUS + BULLET_HEIGHT / 2:
                enemy.take_damage(BULLET_DAMAGE, bullet)
                particles.emit_hit(bullet.pos, enemy.color)
                particles.emit_bullet_spark(bullet.pos)
                shake_state[0] = SCREEN_SHAKE_FRAMES
                bullet.alive = False

        self.bullets = [b for b in self.bullets if b.alive]

    def weapon_draw(self, surface):
        direction = pygame.math.Vector2(
            math.cos(self.barrel_angle), math.sin(self.barrel_angle)
        )
        barrel_start = self.pos + direction * BALL_RADIUS
        barrel_end = self.pos + direction * (BALL_RADIUS + 12)
        pygame.draw.line(surface, (255, 180, 60),
                         (int(barrel_start.x), int(barrel_start.y)),
                         (int(barrel_end.x), int(barrel_end.y)), 6)

        if self.muzzle_flash_frames > 0:
            radius = (4 - self.muzzle_flash_frames) * 5
            pygame.draw.circle(surface, (255, 240, 100),
                                (int(barrel_end.x), int(barrel_end.y)), radius)
            self.muzzle_flash_frames -= 1

        for bullet in self.bullets:
            if bullet.trail:
                for i, trail_pos in enumerate(bullet.trail):
                    alpha = int(80 * (i / len(bullet.trail)))
                    r = 3
                    s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (255, 200, 80, alpha), (r, r), r)
                    surface.blit(s, (int(trail_pos[0]) - r, int(trail_pos[1]) - r))

            if bullet.vel.length() > 0:
                vel_dir = bullet.vel.normalize()
                points = _bullet_polygon(bullet.pos, vel_dir, BULLET_WIDTH, BULLET_HEIGHT)
                pygame.draw.polygon(surface, (255, 200, 80), points)
