import pygame
import math
import random
from constants import *


def _random_diagonal_angle():
    """Return a random angle (radians) not within 20 degrees of any axis."""
    forbidden = math.radians(20)
    while True:
        angle = random.uniform(0, 2 * math.pi)
        mod = angle % (math.pi / 2)
        if mod > forbidden and mod < (math.pi / 2 - forbidden):
            return angle


def _bright(color, amount=30):
    return tuple(min(255, c + amount) for c in color)


class Ball:
    def __init__(self, pos, color, name):
        self.pos = pygame.math.Vector2(pos)
        angle = _random_diagonal_angle()
        self.vel = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * BALL_SPEED
        self.hp = float(BALL_HP)
        self.color = color
        self.name = name
        self.alive = True
        self.hit_cooldowns = {}
        self.flicker_timer = 0.0

        glow_size = (BALL_RADIUS + GLOW_LAYERS * 4) * 2 + 4
        self.glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        self._glow_size = glow_size

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def move(self):
        self.pos += self.vel

        bounced = False

        if self.pos.x - BALL_RADIUS < 0:
            self.vel.x = abs(self.vel.x)
            self.pos.x = BALL_RADIUS
            bounced = True
        elif self.pos.x + BALL_RADIUS > SCREEN_WIDTH:
            self.vel.x = -abs(self.vel.x)
            self.pos.x = SCREEN_WIDTH - BALL_RADIUS
            bounced = True

        if self.pos.y - BALL_RADIUS < 0:
            self.vel.y = abs(self.vel.y)
            self.pos.y = BALL_RADIUS
            bounced = True
        elif self.pos.y + BALL_RADIUS > SCREEN_HEIGHT:
            self.vel.y = -abs(self.vel.y)
            self.pos.y = SCREEN_HEIGHT - BALL_RADIUS
            bounced = True

        if bounced:
            self.on_wall_bounce()

        speed = self.vel.length()
        if speed > 0:
            self.vel = self.vel / speed * BALL_SPEED

    def ball_collision(self, other):
        delta = other.pos - self.pos
        dist = delta.length()

        if dist == 0:
            other.pos.x += 1
            return

        if dist < BALL_RADIUS * 2:
            normal = delta.normalize()
            overlap = BALL_RADIUS * 2 - dist
            self.pos -= normal * (overlap / 2)
            other.pos += normal * (overlap / 2)

            a_along = self.vel.dot(normal)
            b_along = other.vel.dot(normal)
            self.vel += (b_along - a_along) * normal
            other.vel += (a_along - b_along) * normal

            speed_a = self.vel.length()
            speed_b = other.vel.length()
            if speed_a > 0:
                self.vel = self.vel / speed_a * BALL_SPEED
            if speed_b > 0:
                other.vel = other.vel / speed_b * BALL_SPEED

    # ------------------------------------------------------------------
    # Damage
    # ------------------------------------------------------------------

    def take_damage(self, amount, source):
        pass  # implemented Phase 2

    def is_dead(self):
        return self.hp <= 0

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_glow(self, surface, pos, radius, color):
        self.glow_surf.fill((0, 0, 0, 0))
        for i in range(GLOW_LAYERS):
            layer_radius = radius + (GLOW_LAYERS - i) * 4
            alpha = max(5, GLOW_ALPHA_START - int((GLOW_ALPHA_START - 5) * i / max(GLOW_LAYERS - 1, 1)))
            cx = self._glow_size // 2
            cy = self._glow_size // 2
            pygame.draw.circle(self.glow_surf, (*color, alpha), (cx, cy), layer_radius)
        blit_x = int(pos.x) - self._glow_size // 2
        blit_y = int(pos.y) - self._glow_size // 2
        surface.blit(self.glow_surf, (blit_x, blit_y))

    def draw(self, surface):
        if not self.alive:
            return

        if self.hp < LOW_HP_THRESHOLD:
            alpha = int(100 + 155 * (0.5 + 0.5 * math.sin(
                self.flicker_timer * 2 * math.pi / FLICKER_INTERVAL
            )))
        else:
            alpha = 255

        self.draw_glow(surface, self.pos, BALL_RADIUS, self.color)

        if alpha < 255:
            ball_surf = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(ball_surf, (*self.color, alpha),
                               (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
            surface.blit(ball_surf, (int(self.pos.x) - BALL_RADIUS,
                                     int(self.pos.y) - BALL_RADIUS))
        else:
            pygame.draw.circle(surface, self.color,
                               (int(self.pos.x), int(self.pos.y)), BALL_RADIUS)

        pygame.draw.circle(surface, _bright(self.color),
                           (int(self.pos.x), int(self.pos.y)), BALL_RADIUS + 1, 2)

        self.weapon_draw(surface)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt, enemy, particles, shake_state):
        if not self.alive:
            return

        self.flicker_timer += dt

        for src in list(self.hit_cooldowns):
            self.hit_cooldowns[src] = max(0.0, self.hit_cooldowns[src] - dt)

        self.move()
        self.weapon_update(dt, enemy, particles, shake_state)

    # ------------------------------------------------------------------
    # Subclass hooks
    # ------------------------------------------------------------------

    def weapon_update(self, dt, enemy, particles, shake_state):
        pass

    def weapon_draw(self, surface):
        pass

    def on_wall_bounce(self):
        pass
