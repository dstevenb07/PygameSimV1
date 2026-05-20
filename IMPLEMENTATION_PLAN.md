# Ball Battles — Implementation Plan

This document is the coding-side companion to SPEC.md. The spec made all design decisions. This plan answers: what to write, in what order, and what done looks like — per phase, per file, per method.

---

## Ground Rules

- Every phase ends with a runnable, testable simulation
- All stub files exist from Phase 1 (pygbag scans `main.py` imports at bundle time — missing files = broken WASM)
- No magic numbers ever — if a value is used, it lives in `constants.py`
- `hit_cooldowns` keys by object reference (not `id()`) — `id()` is unsafe for ephemeral objects like bullets/mines since Python's GC can recycle addresses
- Velocity renormalised after every bounce and collision — floating point drift is real at 60fps
- All surfaces for glow: one `pygame.SRCALPHA` surface per ball created at `__init__`, reused each frame (cleared + redrawn at draw time)
- Screen shake: draw everything to `game_surface`, blit `game_surface` to `screen` with a random pixel offset during shake frames. Entity positions never touched.

---

## Phase 1 — Arena + Bouncing Balls

**Deliverable:** Two balls bounce at constant velocity. Wall bounce and body collision work. Async loop runs at 60fps. Stub HUD visible. No crashes.

### Step 1 — `constants.py`
Write the complete constants block from the spec. Every value defined. Nothing left as a placeholder. This file is written once and only tuned after — no logic, no imports.

```
SCREEN_WIDTH, SCREEN_HEIGHT, FPS
BACKGROUND_COLOR, WALL_COLOR
BALL_RADIUS, BALL_SPEED, BALL_HP
HIT_COOLDOWN
SWORD_*, GUN_*, BULLET_*, TETHER_*, MINE_*
GLOW_*, PARTICLE_*, SCREEN_SHAKE_*
LOW_HP_THRESHOLD, FLICKER_INTERVAL
HUD_*
```

Done when: file imports cleanly with `from constants import *`, all names resolve.

---

### Step 2 — Stub files (all four ball subclasses + particles + hud)

Create these six files as minimal stubs. They must import without error and expose the names `main.py` will use.

**`particles.py`**
```python
from constants import *

class ParticleSystem:
    def __init__(self): pass
    def update(self, dt): pass
    def draw(self, surface): pass
    def emit_hit(self, pos, color): pass
    def emit_death(self, pos, color): pass
    def emit_mine(self, pos): pass
    def emit_bullet_spark(self, pos): pass
```

**`hud.py`**
```python
from constants import *

def draw_hud(surface, fighter_a, fighter_b, font):
    pass
```

**`ball_sword.py`, `ball_gun.py`, `ball_tether.py`, `ball_trap.py`**
Each:
```python
from constants import *
from ball_base import Ball

class SwordBall(Ball):  # (GunBall / TetherBall / TrapLayer)
    pass
```

Done when: all six files import without error.

---

### Step 3 — `arena.py`

```python
class Arena:
    def __init__(self):
        self.obstacles = []  # empty — architecture ready, not used

    def draw(self, surface):
        # 1px rect outline in WALL_COLOR, inset 1px from screen edges
        pygame.draw.rect(surface, WALL_COLOR,
            pygame.Rect(1, 1, SCREEN_WIDTH - 2, SCREEN_HEIGHT - 2), 1)
```

Done when: boundary line renders correctly on dark background.

---

### Step 4 — `ball_base.py`

Implement all shared ball logic. Weapon methods are stubs. `take_damage` is a stub (returns immediately) — it becomes real in Phase 2.

**`__init__(self, pos, vel_angle, color, name)`**
- `self.pos = pygame.math.Vector2(pos)`
- `self.vel` = Vector2 at BALL_SPEED magnitude, direction from `vel_angle` (radians)
- `self.hp = BALL_HP`
- `self.color = color`
- `self.name = name`
- `self.alive = True`
- `self.hit_cooldowns = {}` — keyed by object reference
- `self.flicker_timer = 0.0`
- `self.flicker_visible = True`
- `self.glow_surface = pygame.Surface((BALL_RADIUS * 2 + GLOW_LAYERS * 8 + 4,) * 2, pygame.SRCALPHA)`

**`_random_angle()` (module-level helper)**
- Returns a random angle (radians) guaranteed not within 20° of horizontal or vertical axes
- Loop: `angle = random.uniform(0, 2*pi)`, reject if `abs(angle % (pi/2)) < radians(20)`, else return

**`move(self)`**
- `self.pos += self.vel`
- Wall bounce — check all four edges using ball edge (pos ± BALL_RADIUS):
  - x left: if `pos.x - BALL_RADIUS < 0` → `vel.x = abs(vel.x)`, `pos.x = BALL_RADIUS`
  - x right: if `pos.x + BALL_RADIUS > SCREEN_WIDTH` → `vel.x = -abs(vel.x)`, `pos.x = SCREEN_WIDTH - BALL_RADIUS`
  - y top / y bottom: same pattern for y
- After any bounce: call `self.on_wall_bounce()`
- After all bounces: renormalise — `self.vel = self.vel.normalize() * BALL_SPEED`

**`ball_collision(self, other)`**
- `delta = other.pos - self.pos`
- `dist = delta.length()`
- Guard: if `dist == 0`: nudge `other.pos` by (1, 0) and return
- If `dist < BALL_RADIUS * 2`:
  - `normal = delta.normalize()`
  - Separate: push each ball along normal by `(BALL_RADIUS * 2 - dist) / 2`
  - Velocity swap along normal axis:
    - `a_along = self.vel.dot(normal)`
    - `b_along = other.vel.dot(normal)`
    - `self.vel += (b_along - a_along) * normal`
    - `other.vel += (a_along - b_along) * normal`
  - Renormalise both to BALL_SPEED

**`take_damage(self, amount, source)`** — Phase 1 stub:
```python
def take_damage(self, amount, source):
    pass
```

**`is_dead(self)`**
```python
def is_dead(self):
    return self.hp <= 0
```

**`draw_glow(self, surface, pos, radius, color)`**
- Clear `self.glow_surface` to transparent each call
- Draw GLOW_LAYERS circles on it, each 4px larger than last, starting outside `radius`
- Alpha steps from GLOW_ALPHA_START down to ~5 linearly
- Blit `glow_surface` to `surface` centred on `pos`

**`draw(self, surface)`**
- If not `self.alive`: return
- Flicker: if `self.hp < LOW_HP_THRESHOLD`, compute `alpha = 100 + 155 * (0.5 + 0.5 * sin(self.flicker_timer * 2 * pi / FLICKER_INTERVAL))`. Else `alpha = 255`.
- Draw glow bloom at `self.pos`, radius `BALL_RADIUS`, `self.color`
- Draw filled circle: `pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), BALL_RADIUS)`
  - Note: alpha on the ball body itself requires a temp surface — create one, draw circle, set alpha, blit
- Draw outline ring: `pygame.draw.circle(surface, bright(self.color), pos, BALL_RADIUS + 1, 2)` where `bright()` clamps each channel +30
- Call `self.weapon_draw(surface)`

**`update(self, dt, enemy)`**
- If not `self.alive`: return
- `self.flicker_timer += dt`
- Tick down hit_cooldowns: `for src in list(self.hit_cooldowns): self.hit_cooldowns[src] = max(0, self.hit_cooldowns[src] - dt)`
- `self.move()`
- `self.weapon_update(dt, enemy)`

**Stubs (overridden in subclasses):**
```python
def weapon_update(self, dt, enemy): pass
def weapon_draw(self, surface): pass
def on_wall_bounce(self): pass
```

Done when: two Ball instances update and draw without error, bounce off all four walls correctly.

---

### Step 5 — `main.py`

```python
import asyncio
import pygame
import random
import math
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
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, HUD_FONT_SIZE)

    arena = Arena()
    particles = ParticleSystem()

    # --- CHARACTER ROSTER (change these two lines to swap fighters) ---
    fighter_a = Ball(
        pos=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2),
        color=(200, 215, 255),
        name="Ball A"
    )
    fighter_b = Ball(
        pos=(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2),
        color=(255, 150, 30),
        name="Ball B"
    )
    # ------------------------------------------------------------------

    shake_frames = 0
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        fighter_a.update(dt, fighter_b)
        fighter_b.update(dt, fighter_a)
        fighter_a.ball_collision(fighter_b)

        game_surface.fill(BACKGROUND_COLOR)
        arena.draw(game_surface)
        particles.update(dt)
        particles.draw(game_surface)
        fighter_a.draw(game_surface)
        fighter_b.draw(game_surface)
        draw_hud(game_surface, fighter_a, fighter_b, font)

        # Screen shake
        if shake_frames > 0:
            offset = (random.randint(-SCREEN_SHAKE_MAGNITUDE, SCREEN_SHAKE_MAGNITUDE),
                      random.randint(-SCREEN_SHAKE_MAGNITUDE, SCREEN_SHAKE_MAGNITUDE))
            shake_frames -= 1
        else:
            offset = (0, 0)

        screen.fill((0, 0, 0))
        screen.blit(game_surface, offset)
        pygame.display.flip()
        await asyncio.sleep(0)

asyncio.run(main())
```

Done when: window opens, two colored circles bounce indefinitely with no wall clipping and correct body collision separation.

---

## Phase 2 — HP System + Live HUD

**Deliverable:** `take_damage()` works with cooldowns. HUD bars drain, shift color, and show names. Flicker activates at low HP. Death removes ball.

### Step 1 — `ball_base.py`: implement `take_damage`

```python
def take_damage(self, amount, source):
    if self.hit_cooldowns.get(source, 0) > 0:
        return
    self.hp = max(0, self.hp - amount)
    self.hit_cooldowns[source] = HIT_COOLDOWN
    if self.hp <= 0:
        self.alive = False
        # Phase 3 will add: particles.emit_death(self.pos, self.color)
```

Note: `source` is the object reference itself (bullet instance, self for sword/tether). No `id()` — the object is the key.

### Step 2 — `ball_base.py`: flicker in `draw()`

Already stubbed in Phase 1 draw. Now it activates: when `hp < LOW_HP_THRESHOLD`, compute sine-wave alpha. Apply to the ball body surface before blitting.

### Step 3 — `hud.py`: real implementation

**`draw_hud(surface, fighter_a, fighter_b, font)`**

Left bar (fighter_a):
- Name label: `font.render(fighter_a.name, True, (255,255,255))`, drawn above bar, left-aligned at `HUD_BAR_MARGIN`
- Bar background rect: `(HUD_BAR_MARGIN, HUD_BAR_Y, HUD_BAR_WIDTH, HUD_BAR_HEIGHT)`, fill `(30, 30, 40)`
- Bar fill width: `int(HUD_BAR_WIDTH * (fighter_a.hp / BALL_HP))`
- Bar fill color: interpolate based on HP%:
  - `hp_pct = fighter_a.hp / BALL_HP`
  - if `hp_pct > 0.6`: color = `fighter_a.color`
  - elif `hp_pct > 0.25`: lerp from `fighter_a.color` toward `(220, 180, 0)` — `t = (0.6 - hp_pct) / 0.35`
  - else: lerp from `(220, 180, 0)` toward `(200, 40, 40)` — `t = (0.25 - hp_pct) / 0.25`

Right bar (fighter_b):
- Mirror layout: right-aligned. Bar starts at `SCREEN_WIDTH - HUD_BAR_MARGIN - HUD_BAR_WIDTH`
- Fill grows left-to-right (same direction — HP drains from right side)
- Name label: right-aligned

**`_lerp_color(a, b, t)`** — module-level helper:
```python
def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
```

### Step 4 — `main.py`: test damage call + death check

Add a temporary manual call after update (remove in Phase 4):
```python
# TEMP: test damage
if pygame.key.get_pressed()[pygame.K_SPACE]:
    fighter_a.take_damage(10, "test")
```

Add death check in the draw block:
```python
if fighter_a.alive:
    fighter_a.draw(game_surface)
if fighter_b.alive:
    fighter_b.draw(game_surface)
```

Done when: spacebar drains fighter_a's bar, bar shifts green→yellow→red, flicker appears below 25hp, ball disappears at 0hp.

---

## Phase 3 — Particle System + Screen Shake

**Deliverable:** All particle types work and fade correctly. Death explosion fires. Screen shake fires on hit. Performance stays at 60fps with max particles.

### Step 1 — `particles.py`: Particle data structure

Each particle is a dict (faster than a class for large counts):
```python
{
    'pos': [x, y],
    'vel': [vx, vy],
    'color': (r, g, b),
    'radius': float,
    'lifetime': float,
    'age': float,
    'gravity': float  # 0.0 for most, ~150.0 px/s² for death
}
```

### Step 2 — `particles.py`: `ParticleSystem` class

**`__init__`**: `self.particles = []`

**`_spawn(pos, vel, color, radius, lifetime, gravity=0.0)`**:
- Append dict to `self.particles`
- If `len(self.particles) > 150`: remove oldest (pop index 0)

**`update(self, dt)`**:
```python
for p in self.particles:
    p['age'] += dt
    p['vel'][1] += p['gravity'] * dt
    p['pos'][0] += p['vel'][0] * dt
    p['pos'][1] += p['vel'][1] * dt
self.particles = [p for p in self.particles if p['age'] < p['lifetime']]
```

**`draw(self, surface)`**:
```python
for p in self.particles:
    alpha = int(255 * (1 - p['age'] / p['lifetime']))
    r = max(1, int(p['radius'] * (1 - p['age'] / p['lifetime'])))
    # Draw to temp surface with alpha, blit to main surface
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*p['color'], alpha), (r, r), r)
    surface.blit(s, (int(p['pos'][0]) - r, int(p['pos'][1]) - r))
```

Note: Per-particle surface creation is expensive. If FPS drops below 60 at 150 particles, batch-draw using `pygame.draw.circle` directly with no alpha (acceptable tradeoff — particles are small and fast).

**`emit_hit(self, pos, color)`**:
- Spawn PARTICLE_COUNT_HIT particles
- Random directions, speed 60–120 px/s, radius 3–5, lifetime PARTICLE_LIFETIME, gravity 0

**`emit_death(self, pos, color)`**:
- Spawn PARTICLE_COUNT_DEATH particles
- Random directions, speed 150–300 px/s, radius 4–7, lifetime DEATH_PARTICLE_LIFETIME, gravity 150.0

**`emit_mine(self, pos)`**:
- Spawn PARTICLE_COUNT_MINE particles, color `(220, 80, 30)`
- Random directions, speed 100–200 px/s, radius 3–6, lifetime PARTICLE_LIFETIME, gravity 0
- Also store a flash: `self.flashes.append({'pos': pos, 'radius': 5, 'max_radius': 40, 'frames': 3})`

**`emit_bullet_spark(self, pos)`**:
- Spawn 3 particles in bullet color `(255, 200, 80)`, speed 150–250 px/s, lifetime 0.2s

### Step 3 — `main.py`: wire up particles + shake signal

- Pass `particles` into `fighter.update()` — or use a return value / callback. Simplest: `update()` returns a list of events, `main.py` dispatches them to `particles.emit_*()`.
- Alternatively (simpler): pass `particles` as a param to `update(dt, enemy, particles)` — subclasses call `particles.emit_hit()` directly on contact.
- Screen shake: `main.py` owns `shake_frames`. When a weapon hit occurs, set `shake_frames = SCREEN_SHAKE_FRAMES`. Signal via return value or a shared mutable `shake_state = [0]` list.

**Chosen approach:** pass `particles` and a `shake_state = [0]` list into `update()`. Weapon code sets `shake_state[0] = SCREEN_SHAKE_FRAMES` on hit. Main reads and decrements.

Update `ball_base.py` signature: `update(self, dt, enemy, particles, shake_state)`

Done when: manually triggered hits spawn particles, death explosion fires with gravity-fall, shake fires on hit, no FPS drop.

---

## Phase 4 — Sword Ball

**Deliverable:** SwordBall rotates blade, detects hits on sword line segment, deals damage. Two SwordBalls fight to completion.

### Step 1 — `ball_sword.py`

**`__init__(self, pos, color, name)`**:
- Call `super().__init__(pos, color, name)`
- `self.sword_angle = 0.0` (degrees)

**`weapon_update(self, dt, enemy, particles, shake_state)`**:
```
self.sword_angle = (self.sword_angle + SWORD_ROTATION_SPEED) % 360
angle_rad = math.radians(self.sword_angle)

base = self.pos + Vector2(cos, sin) * SWORD_ORBIT_RADIUS
tip  = self.pos + Vector2(cos, sin) * (SWORD_ORBIT_RADIUS + SWORD_LENGTH)

# Line segment vs circle hit test:
# Project enemy.pos onto segment base→tip, clamp t to [0,1], find closest point
# If distance from closest point to enemy.pos < BALL_RADIUS: hit
if hit and enemy.alive:
    enemy.take_damage(SWORD_DAMAGE, self)
    particles.emit_hit(closest_point, enemy.color)
    shake_state[0] = SCREEN_SHAKE_FRAMES
```

**Line segment vs circle — exact implementation:**
```python
def _segment_circle_hit(p1, p2, center, radius):
    seg = p2 - p1
    to_c = center - p1
    seg_len_sq = seg.length_squared()
    if seg_len_sq == 0:
        return (center - p1).length() < radius, p1
    t = max(0.0, min(1.0, to_c.dot(seg) / seg_len_sq))
    closest = p1 + seg * t
    return (center - closest).length() < radius, closest
```

**`weapon_draw(self, surface)`**:
- Compute `base` and `tip` positions
- Draw sword as a rotated rectangle:
  - Build a 4-point polygon: perpendicular to the blade direction at SWORD_WIDTH/2 on each side
  - `pygame.draw.polygon(surface, (180, 210, 255), points)`
- Draw glow bloom at tip: call `self.draw_glow(surface, tip, 4, (220, 240, 255))`

**Rotated rect polygon helper:**
```python
def _sword_polygon(base, tip, width):
    direction = (tip - base).normalize()
    perp = Vector2(-direction.y, direction.x) * (width / 2)
    return [base + perp, tip + perp, tip - perp, base - perp]
```

### Step 2 — `main.py`: swap fighters to SwordBall vs SwordBall

```python
fighter_a = SwordBall(pos=(SCREEN_WIDTH//4, SCREEN_HEIGHT//2), color=(200,215,255), name="Sword")
fighter_b = SwordBall(pos=(3*SCREEN_WIDTH//4, SCREEN_HEIGHT//2), color=(180,200,255), name="Sword B")
```

Remove the temp spacebar test damage call.

Done when: both swords rotate, blades connect and drain HP, one ball dies, winner bounces alone.

---

## Phase 5 — Gun Ball

**Deliverable:** GunBall fires bullets that track and bounce. Bullet trail visible. Muzzle flash fires. Hits register.

### Step 1 — Bullet class (top of `ball_gun.py`)

```python
class Bullet:
    def __init__(self, pos, vel):
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.distance_travelled = 0.0
        self.alive = True
        self.trail = []  # last 4 positions
```

### Step 2 — `ball_gun.py`

**`__init__`**:
- `self.fire_timer = GUN_FIRE_INTERVAL`
- `self.bullets = []`
- `self.barrel_angle = 0.0`
- `self.muzzle_flash_frames = 0`

**`weapon_update(self, dt, enemy, particles, shake_state)`**:

Barrel tracking:
```python
delta = enemy.pos - self.pos
self.barrel_angle = math.atan2(delta.y, delta.x)
```

Fire timer:
```python
self.fire_timer -= dt
if self.fire_timer <= 0:
    self.fire_timer = GUN_FIRE_INTERVAL
    self.muzzle_flash_frames = 3
    direction = Vector2(cos(barrel_angle), sin(barrel_angle))
    spawn_pos = self.pos + direction * (BALL_RADIUS + 2)
    self.bullets.append(Bullet(spawn_pos, direction * BULLET_SPEED))
```

Bullet update (each bullet):
```python
bullet.trail.append(tuple(bullet.pos))
if len(bullet.trail) > 4:
    bullet.trail.pop(0)
bullet.pos += bullet.vel
bullet.distance_travelled += BULLET_SPEED

# Wall bounce
if bullet.pos.x - 2 < 0 or bullet.pos.x + 2 > SCREEN_WIDTH:
    bullet.vel.x *= -1
    bullet.pos.x = max(2, min(SCREEN_WIDTH-2, bullet.pos.x))
if bullet.pos.y - 2 < 0 or bullet.pos.y + 2 > SCREEN_HEIGHT:
    bullet.vel.y *= -1
    bullet.pos.y = max(2, min(SCREEN_HEIGHT-2, bullet.pos.y))
bullet.vel = bullet.vel.normalize() * BULLET_SPEED

# Max distance despawn
if bullet.distance_travelled >= BULLET_MAX_DISTANCE:
    bullet.alive = False
    continue

# Hit test
if enemy.alive and (enemy.pos - bullet.pos).length() < BALL_RADIUS + BULLET_HEIGHT/2:
    enemy.take_damage(BULLET_DAMAGE, bullet)
    particles.emit_hit(bullet.pos, enemy.color)
    particles.emit_bullet_spark(bullet.pos)
    shake_state[0] = SCREEN_SHAKE_FRAMES
    bullet.alive = False
```

Cull dead bullets: `self.bullets = [b for b in self.bullets if b.alive]`

**`weapon_draw(self, surface)`**:

Barrel stub:
```python
barrel_end = self.pos + Vector2(cos(self.barrel_angle), sin(self.barrel_angle)) * (BALL_RADIUS + 12)
# Draw short rect from ball edge to barrel_end, color (255, 180, 60), width 6
```

Muzzle flash (muzzle_flash_frames > 0):
```python
radius = (4 - self.muzzle_flash_frames) * 5  # expands 5→10→15
pygame.draw.circle(surface, (255, 240, 100), barrel_end, radius)
self.muzzle_flash_frames -= 1
```

Each bullet draw:
```python
# Draw trail segments (older = more transparent)
for i, trail_pos in enumerate(bullet.trail):
    alpha = int(80 * (i / len(bullet.trail)))
    # small circle at trail_pos with alpha

# Draw bullet rect oriented along velocity
# Build 4-point polygon: BULLET_WIDTH along vel direction, BULLET_HEIGHT perpendicular
```

Done when: Sword vs Gun fight plays to completion. Bullets visibly bounce, trail follows, muzzle flashes.

---

## Phase 6 — Tether Ball

**Deliverable:** Weight lags behind ball movement, whips visibly on wall bounce, hit detection on weight only.

### Step 1 — `ball_tether.py`

**`__init__`**:
- `self.target_angle = 0.0` (radians)
- `self.current_angle = 0.0` (radians)
- `self.angular_velocity = 0.0`
- `self.weight_trail = []` — last 5 weight positions

**`weapon_update(self, dt, enemy, particles, shake_state)`**:

Target angle tracks ball movement direction:
```python
if self.vel.length() > 0:
    self.target_angle = math.atan2(self.vel.y, self.vel.x)
```

Angle lag — handle wrap-around correctly:
```python
# Shortest-path angular interpolation
diff = self.target_angle - self.current_angle
# Normalise diff to [-pi, pi]
while diff > math.pi: diff -= 2 * math.pi
while diff < -math.pi: diff += 2 * math.pi
self.current_angle += diff * TETHER_LAG_FACTOR + self.angular_velocity * dt
self.angular_velocity *= 0.9  # decay toward 0
```

Weight position:
```python
weight_pos = self.pos + Vector2(
    math.cos(self.current_angle),
    math.sin(self.current_angle)
) * TETHER_ORBIT_RADIUS
```

Trail:
```python
self.weight_trail.append(tuple(weight_pos))
if len(self.weight_trail) > 5:
    self.weight_trail.pop(0)
```

Hit test:
```python
if enemy.alive and (enemy.pos - weight_pos).length() < BALL_RADIUS + TETHER_WEIGHT_RADIUS:
    enemy.take_damage(TETHER_DAMAGE, self)
    particles.emit_hit(weight_pos, enemy.color)
    shake_state[0] = SCREEN_SHAKE_FRAMES
```

**`on_wall_bounce(self)`**:
```python
self.angular_velocity += TETHER_WHIP_BOOST
```

**`weapon_draw(self, surface)`**:

Dashed chain:
```python
# Walk from self.pos to weight_pos in steps of 10px (6 drawn, 4 gap)
# Use parametric: step along direction vector, alternate draw/skip
```

Weight trail (fading):
```python
for i, pos in enumerate(self.weight_trail):
    alpha = int(120 * (i / len(self.weight_trail)))
    # small circle at pos with alpha
```

Weight:
```python
self.draw_glow(surface, weight_pos, TETHER_WEIGHT_RADIUS, (90, 60, 120))
pygame.draw.circle(surface, (90, 60, 120), weight_pos, TETHER_WEIGHT_RADIUS)
```

Done when: Tether vs Gun — weight visibly drags behind movement and snaps on wall bounce.

---

## Phase 7 — Trap Layer

**Deliverable:** Mines drop on interval, pulse, fade, despawn, trigger explosion on proximity. Faint ball trail visible.

### Step 1 — Mine class (top of `ball_trap.py`)

```python
class Mine:
    def __init__(self, pos):
        self.pos = pygame.math.Vector2(pos)
        self.age = 0.0
        self.alive = True
        self.alpha = 255
```

### Step 2 — `ball_trap.py`

**`__init__`**:
- `self.mine_timer = MINE_DROP_INTERVAL`
- `self.mines = []`
- `self.trail = []` — last 3 positions for faint ball trail

**`weapon_update(self, dt, enemy, particles, shake_state)`**:

Ball trail:
```python
self.trail.append(tuple(self.pos))
if len(self.trail) > 3:
    self.trail.pop(0)
```

Mine drop:
```python
self.mine_timer -= dt
if self.mine_timer <= 0:
    self.mine_timer = MINE_DROP_INTERVAL
    self.mines.append(Mine(self.pos))
```

Mine lifecycle:
```python
for mine in self.mines:
    mine.age += dt
    if mine.age >= MINE_FADE_START:
        t = (mine.age - MINE_FADE_START) / (MINE_LIFETIME - MINE_FADE_START)
        mine.alpha = int(255 * (1 - t))
    if mine.age >= MINE_LIFETIME:
        mine.alive = False
        continue
    # Proximity check
    if enemy.alive and (enemy.pos - mine.pos).length() < MINE_PROXIMITY_RADIUS:
        enemy.take_damage(MINE_DAMAGE, mine)
        particles.emit_mine(mine.pos)
        shake_state[0] = SCREEN_SHAKE_FRAMES
        mine.alive = False
self.mines = [m for m in self.mines if m.alive]
```

**`weapon_draw(self, surface)`**:

Ball trail:
```python
for i, pos in enumerate(self.trail):
    alpha = 15 + 15 * (i / len(self.trail))  # 15–30
    s = pygame.Surface((BALL_RADIUS*2, BALL_RADIUS*2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*self.color, int(alpha)), (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
    surface.blit(s, (int(pos[0]) - BALL_RADIUS, int(pos[1]) - BALL_RADIUS))
```

Each mine:
```python
alpha = mine.alpha
# Dark mine body
s = pygame.Surface((MINE_RADIUS*2, MINE_RADIUS*2), pygame.SRCALPHA)
pygame.draw.circle(s, (30, 80, 30, alpha), (MINE_RADIUS, MINE_RADIUS), MINE_RADIUS)
surface.blit(s, mine_draw_pos)

# Pulsing proximity ring
pulse_alpha = int(80 + 50 * math.sin(mine.age * 4))  # oscillates 80–130, speed 4 rad/s
ring_surf = pygame.Surface((MINE_PROXIMITY_RADIUS*2, MINE_PROXIMITY_RADIUS*2), pygame.SRCALPHA)
pygame.draw.circle(ring_surf, (180, 40, 40, int(pulse_alpha * alpha / 255)),
    (MINE_PROXIMITY_RADIUS, MINE_PROXIMITY_RADIUS), MINE_PROXIMITY_RADIUS, 1)
surface.blit(ring_surf, ring_draw_pos)
```

Done when: Trap Layer vs Sword — mines accumulate, pulse, trigger on contact, explode with particles.

---

## Phase 8 — Polish Pass

**Deliverable:** All visuals verified, all matchups playable, roster swap works in two lines.

### Checklist (work through in order)

1. **Glow bloom** — verify on all four ball types and on: sword tip, tether weight, mine proximity ring. Tune `GLOW_ALPHA_START` and layer count if glow is too heavy or invisible.

2. **Outline ring** — confirm `draw()` base class renders it correctly on all subclasses. Adjust brightness offset if invisible on any color.

3. **HUD final** — verify name labels align correctly for both fighters. Confirm color transition thresholds feel right. Test with HP at 60%, 25%, 10%, 0%.

4. **Low HP flicker** — tune `FLICKER_INTERVAL` so pulse is visible but not seizure-inducing. Verify sine wave is smooth (not hard blink).

5. **Bullet spark** — confirm 3 spark particles fire at bullet impact point, distinct from hit particles.

6. **Mine flash** — confirm white expand-and-fade circle fires at mine trigger point.

7. **Particle count** — stress test by letting Trap Layer run for 60 seconds. If particle count hits cap, confirm oldest are culled and FPS holds.

8. **Screen shake** — verify shake fires on every weapon hit type: sword contact, bullet hit, tether weight contact, mine trigger. Confirm it never fires on body collision (body collisions deal no damage).

9. **Obstacle list** — confirm `arena.obstacles = []` exists and is empty. No obstacles built.

10. **Constants audit** — grep each logic file for any raw number that should be a constant. Zero tolerance.

11. **Roster swap test** — change fighter_a and fighter_b to every combination:
    - Sword vs Sword
    - Sword vs Gun
    - Sword vs Tether
    - Sword vs Trap
    - Gun vs Tether
    - Gun vs Trap
    - Tether vs Trap
    Run each to completion. No crashes.

12. **pygbag check** — confirm:
    - `async def main()` with `await asyncio.sleep(0)` at loop end
    - `asyncio.run(main())` at module level
    - All imports at top of `main.py`
    - No `open()`, no `threading`, no `os.path`
    - `pygame.font.Font(None, HUD_FONT_SIZE)` — not a file path

---

## Key Implementation Notes (Cross-Phase)

### Velocity renormalisation
Do this after every `move()` call that touches velocity. Floating point drift at 60fps will cause speed creep or decay over a long run:
```python
speed = self.vel.length()
if speed > 0:
    self.vel = self.vel / speed * BALL_SPEED
```

### Hit cooldown key safety
Use the object reference as the key, not `id()`:
```python
# CORRECT
self.hit_cooldowns[source] = HIT_COOLDOWN

# WRONG — id() can be reused after object is GC'd
self.hit_cooldowns[id(source)] = HIT_COOLDOWN
```
The risk: a bullet is created, hits, is deleted. A new bullet is created and Python allocates it at the same memory address. `id()` returns the same int — the new bullet appears to be on cooldown.

### Glow surface reuse
Create one `pygame.SRCALPHA` surface per ball in `__init__`. Each frame in `draw_glow()`: call `surface.fill((0,0,0,0))` to clear it, then draw the rings, then blit to the main surface. Do not create a new Surface every frame.

### Screen shake signal path
`shake_state = [0]` is a single-element list so it's mutable when passed by reference. Any weapon code that detects a hit sets `shake_state[0] = SCREEN_SHAKE_FRAMES`. Main loop reads and decrements it each frame.

### Angular wrap-around (TetherBall)
Angle interpolation must take the shortest path. Without normalisation, the weight will spin the long way around when crossing the ±π boundary. Always normalise the diff to [-π, π] before applying lag.

### Death and particle timing
When `take_damage` sets `alive = False`, the death particle emit must happen immediately in the same call (or be signalled immediately). If `draw()` checks `alive` first and skips drawing before particles emit, the explosion appears at (0,0). Pass `particles` into `take_damage` or emit in `update()` on the frame death is detected.

---

## File Creation Order (Master List)

```
Phase 1:  constants.py, particles.py (stub), hud.py (stub),
          ball_sword.py (stub), ball_gun.py (stub),
          ball_tether.py (stub), ball_trap.py (stub),
          arena.py, ball_base.py, main.py

Phase 2:  ball_base.py (take_damage, flicker), hud.py (real)

Phase 3:  particles.py (real)

Phase 4:  ball_sword.py (real)

Phase 5:  ball_gun.py (real)

Phase 6:  ball_tether.py (real)

Phase 7:  ball_trap.py (real)

Phase 8:  all files (polish)
```
