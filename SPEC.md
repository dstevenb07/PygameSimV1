# Ball Battles — Claude Code Build Spec

---

<overview>
A 1v1 ball battle simulation built for YouTube Shorts (portrait 9:16). Two balls bounce around a rectangular arena at constant velocity, each with a distinct combat mechanic that defines their entire identity. The fight is emergent — no AI intent, no scripted behaviour. Physics and weapon logic do all the work. The sim ends when one ball dies; the winner keeps bouncing. Four characters exist: Sword Ball, Gun Ball, Tether Ball, and Trap Layer. The architecture is built so swapping fighters or adding new characters requires minimal code changes — a base class handles all shared logic, subclasses define only what is unique to each character.
</overview>

---

<stack>
- Python 3.11+
- pygame-ce (community edition, drop-in pygame replacement)
- pygbag for browser/WASM deployment — all code decisions must be pygbag-compatible
- Flat file structure: all files are siblings in the same project folder, no subdirectories
- No external physics libraries
- No game engine abstractions
- No threads, no blocking I/O, no filesystem access at runtime
</stack>

---

<architecture>

## File Structure
All files are flat siblings in the same project folder. No subdirectories.

```
main.py           — game loop, character roster, init
constants.py      — entire constants block, all tunable values
arena.py          — Arena class, wall boundary, obstacle architecture
ball_base.py      — Ball base class, all shared logic
ball_sword.py     — SwordBall subclass
ball_gun.py       — GunBall subclass
ball_tether.py    — TetherBall subclass
ball_trap.py      — TrapLayer subclass
particles.py      — ParticleSystem class
hud.py            — HUD drawing
```

## Constants Block (constants.py)
All tunable values live here. Nothing magic-numbered inside logic. Every other file imports from constants.

```python
# ARENA
SCREEN_WIDTH = 720
SCREEN_HEIGHT = 1280
FPS = 60
BACKGROUND_COLOR = (10, 12, 20)       # deep blue-black
WALL_COLOR = (60, 65, 80)             # dim wall boundary line

# BALLS
BALL_RADIUS = 22
BALL_SPEED = 4.5                      # starting speed magnitude (pixels/frame)
BALL_HP = 100

# HIT SYSTEM
HIT_COOLDOWN = 0.5                    # seconds before same weapon can hit same ball again

# SWORD BALL
SWORD_ORBIT_RADIUS = 48
SWORD_LENGTH = 40
SWORD_WIDTH = 8
SWORD_ROTATION_SPEED = 4.0            # degrees per frame
SWORD_DAMAGE = 18

# GUN BALL
GUN_FIRE_INTERVAL = 1.2              # seconds between shots
BULLET_SPEED = 9
BULLET_MAX_DISTANCE = 900
BULLET_DAMAGE = 15
BULLET_WIDTH = 14
BULLET_HEIGHT = 5

# TETHER BALL
TETHER_ORBIT_RADIUS = 60
TETHER_WEIGHT_RADIUS = 10
TETHER_LAG_FACTOR = 0.08             # how quickly weight catches up to target angle (0–1)
TETHER_WHIP_BOOST = 3.5              # angular velocity boost applied on wall bounce
TETHER_DAMAGE = 22

# TRAP LAYER
MINE_DROP_INTERVAL = 1.8             # seconds between mine drops
MINE_RADIUS = 10
MINE_PROXIMITY_RADIUS = 28           # trigger radius
MINE_DAMAGE = 25
MINE_LIFETIME = 10.0                 # seconds before despawn
MINE_FADE_START = 7.0                # seconds at which mine begins fading

# VISUAL
GLOW_LAYERS = 4                      # number of glow rings drawn per ball/weapon tip
GLOW_ALPHA_START = 40                # outermost glow opacity
PARTICLE_COUNT_HIT = 8
PARTICLE_COUNT_MINE = 12
PARTICLE_COUNT_DEATH = 28
PARTICLE_LIFETIME = 0.6              # seconds
DEATH_PARTICLE_LIFETIME = 1.2
SCREEN_SHAKE_FRAMES = 4
SCREEN_SHAKE_MAGNITUDE = 5
LOW_HP_THRESHOLD = 25                # HP at which ball starts flickering
FLICKER_INTERVAL = 0.4              # seconds between flicker pulses

# HUD
HUD_BAR_WIDTH = 280
HUD_BAR_HEIGHT = 18
HUD_BAR_Y = 40
HUD_BAR_MARGIN = 30                  # from screen edge
HUD_FONT_SIZE = 22
```

## Main Loop (main.py)
All sibling module imports must appear at the top of main.py — pygbag requires this for WASM packaging:

```python
import asyncio
import pygame
from constants import *
from arena import Arena
from ball_sword import SwordBall
from ball_gun import GunBall
from ball_tether import TetherBall
from ball_trap import TrapLayer
from particles import ParticleSystem
from hud import draw_hud

async def main():
    # init
    while running:
        handle_events()
        update()
        draw()
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)

asyncio.run(main())
```

## Class Structure

```
Ball (base class)
├── position, velocity, hp, color, name
├── move() — constant velocity, elastic wall bounce
├── ball_collision(other) — elastic body bounce, no damage
├── take_damage(amount, source) — respects hit cooldown per source
├── draw_glow(surface, pos, radius, color) — layered bloom utility
├── draw_health_ring (NOT used — health is HUD only)
├── draw(surface) — draws glow + ball circle + outline ring
├── is_dead() → bool
├── update(dt, enemy) — calls move(), weapon_update(), checks weapon hits
├── weapon_update(dt, enemy) — OVERRIDE in subclass
├── weapon_draw(surface) — OVERRIDE in subclass
└── on_wall_bounce() — OVERRIDE in subclass (used by tether)

SwordBall(Ball)
GunBall(Ball)
TetherBall(Ball)
TrapLayer(Ball)
```

## Character Roster (top of main, easy swap)
```python
fighter_a = SwordBall(
    pos=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2),
    color=(220, 230, 255),
    name="Sword"
)
fighter_b = GunBall(
    pos=(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2),
    color=(255, 160, 40),
    name="Gun"
)
```
To run a different fight: change these two lines only.

</architecture>

---

<entities>

## Ball (Base)
- `pos`: [x, y] float
- `vel`: [vx, vy] float — magnitude always equals BALL_SPEED after bounces
- `hp`: float, starts at BALL_HP
- `color`: RGB tuple, unique per character
- `name`: string, shown in HUD
- `hit_cooldowns`: dict mapping source id → remaining cooldown time
- `flickering`: bool, True when hp < LOW_HP_THRESHOLD
- `alive`: bool

**Spawn:** Each fighter spawns at their assigned position with a randomised velocity direction (random angle in range, ensuring diagonal movement, never purely horizontal or vertical). Random seed per run — no two fights follow the same path.

**Wall bounce:** On contact with any wall, reverse the relevant velocity component. Call `on_wall_bounce()` after reversing. Maintain constant speed magnitude — renormalise velocity after bounce to prevent floating point drift.

**Body collision:** When two balls overlap (distance < BALL_RADIUS * 2), resolve elastically — swap velocity components along the collision normal. No damage.

---

## SwordBall
**Additional state:**
- `sword_angle`: float, current rotation angle in degrees

**weapon_update(dt, enemy):**
- Increment `sword_angle` by SWORD_ROTATION_SPEED each frame
- Compute sword tip position: `ball_center + orbit_vector(sword_angle, SWORD_ORBIT_RADIUS + SWORD_LENGTH)`
- Compute sword base position: `ball_center + orbit_vector(sword_angle, SWORD_ORBIT_RADIUS)`
- Check if enemy ball center is within BALL_RADIUS distance of the sword line segment
- On hit: call `enemy.take_damage(SWORD_DAMAGE, self)`

**weapon_draw(surface):**
- Draw rotated rectangle (SWORD_LENGTH × SWORD_WIDTH) from base to tip
- Color: cold blue-white `(180, 210, 255)`, tip slightly brighter `(220, 240, 255)`
- Draw glow bloom on tip only (GLOW_LAYERS rings, decreasing alpha)

---

## GunBall
**Additional state:**
- `fire_timer`: float, counts down to next shot
- `bullets`: list of Bullet objects
- `barrel_angle`: float, angle pointing toward enemy

**Bullet object:**
- `pos`: [x, y]
- `vel`: [vx, vy]
- `distance_travelled`: float
- `alive`: bool

**weapon_update(dt, enemy):**
- Update `barrel_angle` to point toward enemy each frame
- Decrement `fire_timer` by dt; when it reaches 0, spawn bullet aimed at enemy current position, reset timer to GUN_FIRE_INTERVAL
- Each frame: move all bullets by their velocity, increment `distance_travelled`
- Bullet wall bounce: reverse relevant velocity component on wall contact, maintain speed
- Despawn bullet when `distance_travelled` >= BULLET_MAX_DISTANCE
- Check each bullet against enemy: on hit, call `enemy.take_damage(BULLET_DAMAGE, bullet)`, despawn bullet, trigger bullet hit particles + bullet spark effect

**weapon_draw(surface):**
- Draw barrel stub: short rectangle from ball edge pointing toward enemy at `barrel_angle`
- Barrel color: `(255, 180, 60)`
- Each bullet: elongated rectangle (BULLET_WIDTH × BULLET_HEIGHT) oriented along velocity direction
- Bullet color: amber `(255, 200, 80)` with short fading trail behind it (3–4 trail segments, decreasing alpha)
- Muzzle flash: on fire frame only, draw expanding circle at barrel tip, bright yellow, lasts 2–3 frames

---

## TetherBall
**Additional state:**
- `target_angle`: float, desired angle of weight (tracks ball movement direction)
- `current_angle`: float, actual angle of weight (lags behind target)
- `angular_velocity`: float, used for whip effect

**weapon_update(dt, enemy):**
- Each frame: update `target_angle` to match ball's current movement direction
- Interpolate `current_angle` toward `target_angle` using TETHER_LAG_FACTOR: `current_angle += (target_angle - current_angle) * TETHER_LAG_FACTOR`
- Compute weight position: `ball_center + orbit_vector(current_angle, TETHER_ORBIT_RADIUS)`
- Check if enemy ball center is within (BALL_RADIUS + TETHER_WEIGHT_RADIUS) of weight position
- On hit: call `enemy.take_damage(TETHER_DAMAGE, self)`

**on_wall_bounce():**
- Apply TETHER_WHIP_BOOST to angular velocity — weight snaps hard in the new direction, creating the whip effect
- Decay angular_velocity each frame toward 0

**weapon_draw(surface):**
- Draw chain: dashed line between ball center and weight position — alternate drawing short segments and gaps (e.g. 6px drawn, 4px gap)
- Chain color: grey `(130, 130, 140)`
- Weight: filled circle, radius TETHER_WEIGHT_RADIUS, dark purple `(90, 60, 120)` with glow bloom
- Trail: store last 5 weight positions each frame, draw as fading line to show whip arc

---

## TrapLayer
**Additional state:**
- `mine_timer`: float, counts down to next mine drop
- `mines`: list of Mine objects

**Mine object:**
- `pos`: [x, y]
- `age`: float, seconds since spawn
- `alive`: bool
- `alpha`: float, 0–255 opacity

**weapon_update(dt, enemy):**
- Decrement `mine_timer` by dt; when it reaches 0, drop mine at current ball position, reset timer to MINE_DROP_INTERVAL
- Each frame: increment each mine's `age`
- When `age` >= MINE_LIFETIME: despawn mine (set alive=False, shrink + fade over 0.3s then remove)
- When `age` >= MINE_FADE_START: compute `alpha = 255 * (1 - (age - MINE_FADE_START) / (MINE_LIFETIME - MINE_FADE_START))`
- Check each mine against enemy: if distance between enemy center and mine center < MINE_PROXIMITY_RADIUS, trigger: `enemy.take_damage(MINE_DAMAGE, mine)`, despawn mine, trigger mine explosion particles

**weapon_draw(surface):**
- Draw brief faint green trail on ball itself as it moves (last 3 positions, alpha 15–30, color ball green)
- Each mine: filled dark circle (MINE_RADIUS), color `(30, 80, 30)`, with thin red proximity ring `(180, 40, 40)` at MINE_PROXIMITY_RADIUS
- Proximity ring pulses: oscillate ring opacity between 80–180 using sine wave on `age`
- Apply mine's current `alpha` to both shapes during fade

</entities>

---

<rules>

## Movement
- All balls move at constant speed BALL_SPEED at all times
- Velocity direction is random at spawn (guaranteed diagonal — angle not within 20° of horizontal or vertical axes)
- After every wall bounce or body collision, renormalise velocity to maintain exact BALL_SPEED magnitude

## Damage System
- Damage is event-based: a single damage instance fires when a weapon makes contact
- Each ball maintains a `hit_cooldowns` dict keyed by source object id
- `take_damage(amount, source)`: if `source.id` is in cooldowns with time > 0, ignore. Otherwise apply damage, set cooldown to HIT_COOLDOWN seconds
- Cooldowns tick down in `update(dt)`

## HP & Death
- HP starts at BALL_HP, minimum 0
- When HP <= 0: set `alive = False`, trigger death particle explosion, sim continues with winner bouncing
- Sim does not reset or close — winner keeps bouncing indefinitely

## Win Condition
- First ball to reach 0 HP loses
- No win screen, no text overlay, no reset
- The death explosion is the payoff moment — sim continues silently after

## Arena Boundaries
- Hard rectangular boundary: x in [0, SCREEN_WIDTH], y in [0, SCREEN_HEIGHT]
- Ball edge (not center) is the collision point: wall bounce when `pos.x - BALL_RADIUS <= 0`, `pos.x + BALL_RADIUS >= SCREEN_WIDTH`, etc.
- Obstacle system: arena has an `obstacles` list (empty by default). Each obstacle is a Rect. Balls bounce off obstacle edges using the same elastic logic as walls. Weapons and bullets also check obstacle collision if obstacles are present. This list is empty at launch — no obstacles are built, only the architecture is ready.

## Body Collision
- Detected when distance between centers < BALL_RADIUS * 2
- Resolve by separating balls along collision normal and swapping velocity components along that normal
- No damage

</rules>

---

<visual_spec>

## Background & Arena
- Background fill: `(10, 12, 20)` — deep blue-black, every frame
- Arena boundary: thin rectangle outline, 1px, color `(60, 65, 80)`, drawn just inside screen edges

## Ball Visuals
All four balls share the same draw treatment from the base class:

**Glow bloom:**
- Draw GLOW_LAYERS concentric circles, each 4px larger than the last, outside the ball radius
- Alpha decreases from GLOW_ALPHA_START to ~5 across layers
- Color matches ball color
- Use a separate surface with per-pixel alpha for glow rendering

**Ball body:**
- Filled circle, radius BALL_RADIUS, in ball's base color

**Outline ring:**
- Circle outline, 2px width, slightly brighter than base color, drawn at BALL_RADIUS + 1

**Low HP flicker:**
- When HP < LOW_HP_THRESHOLD, pulse ball alpha between 255 and 100 on FLICKER_INTERVAL cycle
- Use sine wave for smooth pulse, not hard blink

**Ball colors:**
| Character | Ball Color | Weapon Color |
|-----------|-----------|______________|
| Sword Ball | `(200, 215, 255)` silver-white | `(180, 210, 255)` cold blue-white |
| Gun Ball | `(255, 150, 30)` orange-amber | `(255, 200, 80)` bright yellow |
| Tether Ball | `(140, 80, 200)` deep purple | `(130, 130, 140)` grey chain + `(90, 60, 120)` weight |
| Trap Layer | `(60, 180, 80)` green | `(30, 80, 30)` dark mine + `(180, 40, 40)` proximity ring |

## Particle System
Single `ParticleSystem` class manages all particles. Each particle has:
- `pos`, `vel`, `color`, `radius`, `lifetime`, `age`, `gravity` (optional float)

**On weapon hit (sword, bullet, tether weight):**
- Spawn PARTICLE_COUNT_HIT particles at contact point
- Color: struck ball's color
- Velocity: random directions, moderate speed
- Lifetime: PARTICLE_LIFETIME seconds
- No gravity

**On bullet despawn (hit):**
- 3 small spark particles in bullet color, random directions, fast, short lifetime (0.2s)

**On mine trigger:**
- Spawn PARTICLE_COUNT_MINE particles at mine position
- Color mix: red-orange `(220, 80, 30)`
- Velocity: random directions, faster than hit particles
- Brief white flash circle at mine center (expand and fade over 3 frames)

**On death:**
- Spawn PARTICLE_COUNT_DEATH particles at dead ball position
- Color: dead ball's color
- Velocity: random directions, high speed
- Apply gravity (pulls down at ~150px/s²)
- Lifetime: DEATH_PARTICLE_LIFETIME seconds
- Particles fade alpha as they age

## Screen Shake
- On any weapon hit: SCREEN_SHAKE_FRAMES frames of shake, SCREEN_SHAKE_MAGNITUDE pixel offset
- Implemented as a shake offset applied to the entire draw surface blit, not to individual entity positions
- Offset direction randomised each frame during shake

## HUD
Layout — portrait screen, top of display:

```
[SWORD ████████████░░░]     [░░░████████████ GUN]
```

- Left bar: fighter_a, left-aligned from HUD_BAR_MARGIN
- Right bar: fighter_b, right-aligned from right edge minus HUD_BAR_MARGIN
- Bars are HUD_BAR_WIDTH × HUD_BAR_HEIGHT, positioned at y = HUD_BAR_Y
- Bar fill color matches ball color, transitions green → yellow → red based on HP %:
  - HP > 60%: ball's base color
  - HP 25–60%: interpolate toward `(220, 180, 0)` yellow
  - HP < 25%: interpolate toward `(200, 40, 40)` red
- Bar background: dark fill `(30, 30, 40)` showing empty HP
- Character name above each bar in bold, HUD_FONT_SIZE, white, matching alignment
- Use pygame default font (no external font files — pygbag compatibility)

## Frame Rate
- Target: 60 FPS via `clock.tick(FPS)`
- All time-based values use `dt` (delta time in seconds) — `dt = clock.tick(FPS) / 1000.0`

</visual_spec>

---

<build_phases>

Each phase produces a runnable, testable simulation.

## Phase 1 — Arena + Bouncing Balls
- Black/dark background, arena boundary drawn
- Two colored circles bouncing at constant velocity off walls
- Body collision resolves correctly (no overlap, no damage)
- 60fps loop with async main
- HUD drawn (static full health bars, placeholder names)

**Test:** Two balls bounce indefinitely, never clip through walls or each other.

## Phase 2 — HP System + HUD Live
- HP tracked per ball
- HUD bars drain correctly when `take_damage()` is called manually (hardcoded test call)
- Bar color transitions green → yellow → red
- Low HP flicker activates below threshold
- Death sets `alive = False`, ball disappears

**Test:** Manually trigger damage, confirm bar drains, flicker appears, ball disappears on death.

## Phase 3 — Particle System + Screen Shake
- ParticleSystem class working
- Hit particles spawn and fade correctly
- Death explosion with gravity-affected particles
- Screen shake on hit
- Mine explosion particles

**Test:** Manually trigger each particle type. Confirm no performance issues with max particles on screen.

## Phase 4 — Sword Ball
- SwordBall subclass complete
- Blade rotates, glow on tip, correct draw
- Hit detection on sword line segment works
- Damage applies with cooldown
- Two SwordBalls fight each other as a stress test

**Test:** Sword vs Sword — hits register, HP drains, fight ends.

## Phase 5 — Gun Ball
- GunBall subclass complete
- Barrel tracks enemy, fires on interval
- Bullets bounce off walls, travel max distance, despawn
- Muzzle flash, bullet trail
- Hit detection and damage

**Test:** Sword vs Gun — full fight plays out correctly.

## Phase 6 — Tether Ball
- TetherBall subclass complete
- Angular lag working — weight trails ball movement
- Whip effect on wall bounce
- Weight trail drawn
- Hit detection on weight end only

**Test:** Tether vs Gun — weight visibly whips on bounces, hits register only on weight.

## Phase 7 — Trap Layer
- TrapLayer subclass complete
- Mines drop on interval at ball position
- Mines pulse, fade, despawn
- Proximity trigger works, mine explosion particles fire
- Faint trail on Trap Layer ball

**Test:** Trap Layer vs Sword — arena fills with mines, mines trigger on contact, despawn correctly.

## Phase 8 — Polish Pass
- Glow bloom on all balls and weapon tips
- Outline ring on all balls
- Bullet spark effect on despawn
- All particle types verified
- HUD font and layout final
- Obstacle list confirmed empty but architected
- Constants block reviewed — all values tunable from top of file
- Character roster swap confirmed working (change two lines, run different fight)

**Test:** All four characters work in any 1v1 combination. Swap fighters in two lines. Run 10 fights — no crashes, no visual glitches.

</build_phases>

---

<pygbag_notes>

- Main loop must be `async def main()` with `await asyncio.sleep(0)` at the end of each frame
- Entry point must be `asyncio.run(main())`
- All imports — including those from sibling modules — must be declared at the top of `main.py` in order. pygbag's packager scans `main.py` to detect what to bundle; imports inside other files may not be detected reliably
- All files must be flat siblings in the same folder as `main.py` — no subdirectories
- No `threading` module
- No `open()` file calls at runtime
- No `os.path` or filesystem access at runtime
- No `subprocess`
- pygame-ce is pygbag-compatible — use it in place of standard pygame
- All surfaces created at startup, not dynamically during the loop where avoidable
- Per-pixel alpha surfaces (`pygame.SRCALPHA`) are fine for glow — create once, reuse
- `pygame.font.Font(None, size)` — use None (default font) not a file path
- Keep total particle count bounded — max ~150 particles alive at once to maintain 60fps in WASM

</pygbag_notes>

---

<do_not_build>

- No AI movement or intent — balls move at constant velocity only, bounce off surfaces
- No health ring around the ball — health is HUD only
- No winner text overlay or win screen
- No reset or restart logic
- No sound
- No obstacles (architecture ready, list empty)
- No external fonts — default pygame font only
- No sprite/image assets — all visuals are primitive shapes
- No game engine abstractions
- No external physics libraries
- No countdown or intro sequence — sim starts immediately, weapons active from frame one
- No near-miss visual effects
- No timer or score display in HUD — health bars only

</do_not_build>

---

<quality_checklist>

Before considering complete:

- [ ] Two balls fight to the death with no crashes across 10+ runs
- [ ] All four characters implemented and individually tested
- [ ] Any two characters can be set as fighters by changing two lines at top of file
- [ ] New character can be added by creating one subclass — no other files or logic touched
- [ ] All tunable values are in the constants block at top of file — none magic-numbered in logic
- [ ] HUD health bars drain, change color, and display correct character names
- [ ] Low HP flicker activates correctly below threshold
- [ ] Death triggers particle explosion, ball disappears, winner continues
- [ ] Screen shake fires on weapon hits
- [ ] Glow bloom visible on balls and weapon tips
- [ ] Outline ring visible on all balls
- [ ] Sword rotates continuously, hit detection on line segment
- [ ] Bullets bounce off walls, trail visible, despawn at max distance
- [ ] Tether weight visibly lags and whips on wall bounce
- [ ] Mines drop, pulse, fade, despawn, trigger correctly
- [ ] Particle system bounded — no frame rate drop with max particles
- [ ] pygbag async loop pattern implemented correctly
- [ ] No file I/O, no threads, no blocking calls
- [ ] Runs in browser via pygbag without errors

</quality_checklist>
