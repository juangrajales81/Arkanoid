# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Arkanoid/breakout clone in Python + pygame-ce. Three modules, no package layout, no test suite, no build step, not a git repo. [FASES.md](FASES.md) records what each development phase added and why — update it when you finish a phase.

## Commands

```powershell
pip install -r requirements.txt   # pygame-ce >= 2.5.5
python main.py                    # run the game (the only entry point)
```

Verified locally with Python 3.14 and pygame-ce 2.5.8. There is no linter, formatter, or test runner configured — do not invent `pytest`/`ruff` invocations in output unless you have added and verified them.

## Language convention

All comments, docstrings, and on-screen UI text are in **Spanish** (`PUNTOS`, `VIDAS`, `PAUSA`, `ESPACIO para lanzar`). Identifiers are in English. Match this when adding code — mixed-language UI strings are a bug here.

## Architecture

**[settings.py](settings.py)** is the single tuning surface. Every constant is imported *by name* (`from settings import WIDTH, PADDLE_SPEED, ...`) in both other modules, so renaming or removing a constant breaks imports in two places. Add new tunables here rather than hardcoding them in entities or the game loop.

**[entities.py](entities.py)** — `Paddle`, `Brick`, `Ball`, `PowerUp`. These are dumb: they move, collide, and draw, but never touch score, lives, or state. `PowerUp` only knows its `kind` string and how to fall; what that kind *does* lives in `Game.apply_powerup()`. `Brick.take_hit()` decrements its own durability and reports whether it broke — it still does not know what a point is.

**[main.py](main.py)** — `Game` owns everything else: the `State` enum machine (MENU / PLAYING / PAUSED / LEVEL_COMPLETE / GAME_OVER), score, lives, level, the `self.balls` / `self.powerups` lists, the `self.effects` timer dict, and the `build_bricks(level)` grid factory.

The boundary matters: `Ball.update(dt, paddle, bricks)` *returns* `(hit_bricks, lost)` instead of mutating the game. `Game.update()` is what removes bricks, adds points, and calls `lose_life()`. Keep new entity logic on the reporting side of that line.

### Float positions mirrored into Rects

`pygame.Rect` is integer-only, so both moving entities keep authoritative float state and round into the rect each frame: `Paddle.x` → `rect.centerx`, `PowerUp.y` → `rect.centery`, and `Ball.pos` (a `Vector2`) → a `rect` computed on demand as a property. Never move an entity by writing to its `Rect` — sub-pixel motion would be lost. New moving entities should follow the same pattern.

### Collision resolution is axis-separated

[entities.py:78-123](entities.py#L78-L123) moves X, resolves walls and **one** brick on that axis, then moves Y and resolves the ceiling and one more brick, excluding bricks already hit this frame. This is what makes corner hits deflect sensibly and gives the caller a `hit` list of at most two bricks per frame. `_first_collision()` is a linear scan over all bricks — fine at the ~60 bricks a layout holds, the place to look first if a level design grows much larger. Indestructible bricks are ordinary collision targets; only `Game` knows they never break.

Paddle collision is deliberately one-way: it only triggers when the ball is moving down *and* has not passed `paddle.rect.bottom`, which prevents the ball getting trapped inside the paddle.

### Ball speed and level scaling

Speed lives only as the magnitude of `Ball.vel`. `Game.ball_speed()` computes `BALL_SPEED * (1 + SPEED_INCREASE_PER_LEVEL * (level - 1))`, times `BALL_SLOW_FACTOR` while the `SLOW` power-up is active. It is applied at two moments only: `Ball.launch()`, and `Game.sync_balls()` when an effect starts or expires. `_bounce_on_paddle()` preserves the current magnitude, so nothing else can drift the speed.

Bounce angle off the paddle is derived from where the ball hits relative to the paddle center, scaled to `MAX_BOUNCE_ANGLE`. That is the player's only steering control; changing it changes the feel of the whole game.

### Power-ups and multi-ball

`self.balls` is a list: a life is lost only when it empties, so `Game.update_balls()` collects survivors and calls `lose_life()` once. Bricks are resolved *inside* that per-ball loop (`hit_brick()`), so a second ball in the same frame sees the updated durability and cannot score the same brick twice.

`self.effects` maps a kind string to its remaining seconds and is the single source of truth for what is active; `POWERUP_KINDS` / `TIMED_POWERUPS` / the colour and label dicts in settings drive both the sorting of drops and the HUD. Adding a kind means: a `settings.py` entry in those tables, a branch in `apply_powerup()`, and — if it changes the paddle or the balls — the matching undo in `end_effect()`. `MULTI` and `LIFE` are instantaneous and never enter `effects`; `WIDE` and `SHRINK` cancel each other.

Anything that affects the balls (`SLOW`, `CATCH`) is pushed through `sync_balls()` rather than set on one ball, so new balls from `Ball.clone()` and rescaling stay consistent. Losing a life calls `clear_effects()` and drops the falling capsules — effects never survive a death or a level change.

### Brick types and level layouts

A level is an ASCII grid in `LEVEL_LAYOUTS` — `(name, rows)`, one character per cell — and `BRICK_TYPES` maps each character to `(color, points, hits)`. `hits=None` means indestructible: it bounces, never breaks, never scores, and never drops a capsule. `build_bricks(level)` derives the column count from the layout itself, so a new layout may be any width; the only hard rule is that every row of one layout has the same length.

Because indestructible bricks stay on screen forever, **the end-of-level test is `Game.level_cleared()` (`not any(brick.breakable ...)`), never `not self.bricks`**. A layout with no breakable brick at all would complete instantly.

Layouts cycle with `layout_for(level)`, so `level` grows without bound while the grid repeats. Difficulty now moves on two axes: ball speed per level (above), and multi-hit bricks gaining `+1 hit` every `HITS_BONUS_EVERY_LEVELS` levels up to `MAX_EXTRA_HITS`.

### Loop and input

`Game.run()` clamps `dt` to `1/30` s so a stalled window cannot tunnel the ball through bricks. Input is split by intent: discrete actions (launch, pause, menu navigation) are handled per-state in the `KEYDOWN` branch of `handle_events()`; continuous paddle movement is polled from `pygame.key.get_pressed()` in `read_direction()`. `update()` returns immediately unless the state is `PLAYING`, so pause/menu states freeze the simulation without a separate code path.

`high_score` lives in the `Game` instance only — nothing is persisted to disk.
