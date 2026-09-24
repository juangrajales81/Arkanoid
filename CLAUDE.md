# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Arkanoid/breakout clone in Python + pygame-ce. Five modules, no package layout, no test suite, no build step. pygame-ce is the only dependency — the sound is synthesized at startup rather than shipped as files, so there is deliberately no numpy and no `assets/`.

Git repo on branch `main`, remote `origin` → `github.com/juangrajales81/Arkanoid`. [README.md](README.md) is the public landing page (what the game is, how to run it, controls); [FASES.md](FASES.md) records what each development phase added and why. Finishing a phase means updating **both**, plus this file when the architecture moved.

## Commands

```powershell
pip install -r requirements.txt   # pygame-ce >= 2.5.5
python main.py                    # run the game (the only entry point)
```

Verified locally with Python 3.14 and pygame-ce 2.5.8. There is no linter, formatter, or test runner configured — do not invent `pytest`/`ruff` invocations in output unless you have added and verified them.

## Language convention

All comments, docstrings, and on-screen UI text are in **Spanish** (`PUNTOS`, `VIDAS`, `PAUSA`, `ESPACIO para lanzar`). Identifiers are in English. Match this when adding code — mixed-language UI strings are a bug here.

## Architecture

**[settings.py](settings.py)** is the single tuning surface. Every constant is imported *by name* (`from settings import WIDTH, PADDLE_SPEED, ...`) in every other module, so renaming or removing a constant breaks imports wherever it is used. Add new tunables here rather than hardcoding them in entities or the game loop.

**[entities.py](entities.py)** — `Paddle`, `Brick`, `Ball`, `PowerUp`, `Particle`. These are dumb: they move, collide, and draw, but never touch score, lives, or state. `PowerUp` only knows its `kind` string and how to fall; what that kind *does* lives in `Game.apply_powerup()`. `Brick.take_hit()` decrements its own durability and reports whether it broke — it still does not know what a point is. `Particle` is pure decoration: it collides with nothing and expires on its own. `Brick.draw(surface, dy)` offsets only the *drawing* (the level-intro drop); the brick keeps colliding at its real rect.

**[audio.py](audio.py)** — `SoundBank` renders every effect from `SOUND_RECIPES` into in-memory WAVs at startup (~0.2 s) and plays them by name. `Game` only ever calls `sounds.play("break")`.

**[scores.py](scores.py)** — `ScoreTable`: the top-`SCORES_TABLE_SIZE` list of `ScoreEntry(name, score, level)`, plus `last_name` to prefill the next entry. It is the only thing persisted, as JSON under `pygame.system.get_pref_path(SCORES_ORG, SCORES_APP)` (on Windows `%APPDATA%\arkanoid\arkanoid\records.json`) — never next to the code, so nothing to gitignore.

**[main.py](main.py)** — `Game` owns everything else: the `State` enum machine (MENU / LEVEL_INTRO / PLAYING / PAUSED / LEVEL_COMPLETE / GAME_OVER / NAME_ENTRY / SCORES), score, lives, level, the `ScoreTable`, the `self.balls` / `self.powerups` lists, the `self.effects` timer dict, `self.particles`, the screen-shake timer, the `SoundBank`, and the `build_bricks(level)` grid factory.

The boundary matters: `Ball.update(dt, paddle, bricks)` *returns* a `BallReport(bricks, lost, bounces)` instead of mutating the game. `Game.update()` is what removes bricks, adds points, plays sounds, and calls `lose_life()`. Keep new entity logic on the reporting side of that line — `bounces` exists precisely so the ball can report "I hit a wall" without knowing that walls make a noise.

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

### Sound is synthesized, never shipped

`SOUND_RECIPES` in settings describes each effect as a list of tone segments (frequency, optional sweep target, duration, waveform, volume, decay); `audio.py` renders them to 16-bit mono WAVs in a `BytesIO` and hands them to `pygame.mixer.Sound`. Adding or retuning a sound is a settings edit, not a new file. `SoundBank` re-inits the mixer to mono 16-bit at `SOUND_SAMPLE_RATE` so no format conversion happens at load.

**A machine with no audio device must still run the game.** `SoundBank._start_mixer()` catches `pygame.error`, leaves `enabled = False`, and `play()` becomes a no-op. Never call `pygame.mixer` directly from `Game`. `M` toggles mute in every state except `NAME_ENTRY`, where every key is a letter and `handle_name_key()` sees it first.

### Screen shake draws through a separate surface

The playfield is drawn onto `self.scene` and blitted to the screen at `shake_offset()`; the HUD is drawn straight onto the screen afterwards, so it never wobbles. Both surfaces start from `BG_COLOR`, which is why the strip the offset exposes is invisible.

`Game.update()` now has two tiers: decoration (particles, shake decay) runs in every state **except `PAUSED`**, the simulation only in `PLAYING` (plus paddle-only movement in `LEVEL_INTRO`). If the shake decay sat inside the `PLAYING` guard, a shake started on the frame the last life is lost would jitter forever behind the game-over overlay.

### Loop and input

`Game.run()` clamps `dt` to `1/30` s so a stalled window cannot tunnel the ball through bricks. Input is split by intent: discrete actions (launch, pause, menu navigation) are handled per-state in the `KEYDOWN` branch of `handle_events()`; continuous paddle movement is polled from `pygame.key.get_pressed()` in `read_direction()`. Past the decoration tier, `update()` returns early unless the state is `LEVEL_INTRO` or `PLAYING`, so pause/menu states freeze the simulation without a separate code path.

### State changes go through `set_state()`

Never assign `self.state` directly: `set_state()` also zeroes `self.state_time`, the one clock (advanced every frame in `update()`) that drives the level-intro drop and banner fade, the name-entry cursor blink, and `SCREEN_INPUT_DELAY` — LEVEL_COMPLETE and GAME_OVER ignore SPACE until it passes, and `hint()` hides the "ESPACIO: …" line until then. A direct assignment leaves a stale clock and breaks all of those.

`start_level()` ends in `LEVEL_INTRO`, so both a new game and the next level enter through the same animation. During the intro the paddle moves and stuck balls follow it (via `Ball.update`, which returns an empty report while stuck), but nothing launches; after `LEVEL_INTRO_TIME` or on SPACE, `finish_intro()` switches to `PLAYING`. Rows drop bottom-up so none passes through a row that already landed, and the scene is clipped to below `PLAY_TOP` while they fall.

### Scores never crash the game

Same rule as audio. A missing, corrupt, or oddly-typed file loads as an empty table (or keeps only valid entries); a failed write sets `persistent = False` and the table lives on in memory, which the scores screen mentions. Saves go through a `.tmp` + `os.replace()`. Ties rank *behind* the existing holder (`rank_for()` counts entries with score `>=`).

There is no `high_score` attribute: the record is `self.scores.best()`. Ending a game — last life lost (after the GAME_OVER screen) or Q from pause — goes through `finish_game()`, which routes to `NAME_ENTRY` if `rank_for(score)` is not `None`, else to the menu.
