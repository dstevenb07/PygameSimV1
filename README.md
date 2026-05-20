# Ball Battles

A 1v1 ball battle simulation built for YouTube Shorts (portrait 9:16).

Two balls bounce around a rectangular arena at constant velocity. Each ball has a distinct combat mechanic — Sword, Gun, Tether, or Trap. The fight is emergent: no AI, no scripted behaviour. Physics and weapon logic do all the work.

## Characters

| Character | Mechanic |
|-----------|----------|
| Sword Ball | Rotating blade orbiting the ball — continuous spin, hit on contact |
| Gun Ball | Tracks enemy and fires bouncing bullets on a timer |
| Tether Ball | Weight on a chain that lags behind movement and whips on wall bounce |
| Trap Layer | Drops proximity mines that fade and explode on contact |

## Stack

- Python 3.11+
- pygame-ce (community edition)
- pygbag for browser/WASM deployment

## Running Locally

```bash
pip install pygame-ce pygbag
python main.py
```

## Running in Browser

```bash
pygbag .
```

Then open `http://localhost:8000` in your browser.

## Swapping Fighters

Change two lines at the top of `main.py`:

```python
fighter_a = SwordBall(pos=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2), color=(200, 215, 255), name="Sword")
fighter_b = GunBall(pos=(3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2), color=(255, 150, 30), name="Gun")
```

Available classes: `SwordBall`, `GunBall`, `TetherBall`, `TrapLayer`

## Project Structure

```
main.py         — game loop, character roster, init
constants.py    — all tunable values
arena.py        — Arena class, wall boundary
ball_base.py    — Ball base class, shared logic
ball_sword.py   — SwordBall
ball_gun.py     — GunBall
ball_tether.py  — TetherBall
ball_trap.py    — TrapLayer
particles.py    — ParticleSystem
hud.py          — HUD drawing
```

## Build Phases

| Phase | Branch | Description |
|-------|--------|-------------|
| 0 | `main` | Spec + README |
| 1 | `phase-1/arena-bouncing-balls` | Arena, bouncing balls, async loop |
| 2 | `phase-2/hp-hud` | HP system, live HUD bars |
| 3 | `phase-3/particles-shake` | Particle system, screen shake |
| 4 | `phase-4/sword-ball` | SwordBall complete |
| 5 | `phase-5/gun-ball` | GunBall complete |
| 6 | `phase-6/tether-ball` | TetherBall complete |
| 7 | `phase-7/trap-layer` | TrapLayer complete |
| 8 | `phase-8/polish` | Polish pass, final QA |
