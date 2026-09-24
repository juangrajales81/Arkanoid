"""Arkanoid - Fase 6: récords en disco y transiciones entre niveles."""

import random
from enum import Enum, auto

import pygame

from settings import (
    WIDTH, HEIGHT, FPS, TITLE, BG_COLOR, TEXT_COLOR, DIM_TEXT_COLOR,
    HUD_HEIGHT, HUD_LINE_COLOR, OVERLAY_COLOR,
    START_LIVES, SPEED_INCREASE_PER_LEVEL, BALL_SPEED, BALL_COLOR,
    BRICK_HEIGHT, BRICK_GAP, BRICK_TOP, BRICK_SIDE_MARGIN,
    BRICK_TYPES, EMPTY_CELL, LEVEL_LAYOUTS,
    HITS_BONUS_EVERY_LEVELS, MAX_EXTRA_HITS,
    PADDLE_WIDTH, PADDLE_WIDE_FACTOR, PADDLE_SHRINK_FACTOR,
    POWERUP_DROP_CHANCE, POWERUP_DURATION, POWERUP_POINTS,
    POWERUP_KINDS, POWERUP_WEIGHTS, TIMED_POWERUPS,
    POWERUP_LETTERS, POWERUP_NAMES, POWERUP_COLORS,
    BALL_SLOW_FACTOR, MULTIBALL_EXTRA, MULTIBALL_SPREAD, MAX_LIVES,
    PARTICLE_BREAK_COUNT, PARTICLE_HIT_COUNT, PARTICLE_LOST_COUNT,
    MAX_PARTICLES, SHAKE_ON_BREAK, SHAKE_ON_LIFE_LOST,
    PLAY_TOP, NAME_MAX_LENGTH, NAME_CHARS, HIGHLIGHT_COLOR,
    SCREEN_INPUT_DELAY, LEVEL_INTRO_TIME, INTRO_ROW_DELAY, INTRO_DROP_TIME,
    INTRO_DROP_DISTANCE, INTRO_FADE_TIME,
)
from audio import SoundBank
from entities import Paddle, Ball, Brick, PowerUp, Particle
from scores import ScoreTable


class State(Enum):
    MENU = auto()
    LEVEL_INTRO = auto()     # los ladrillos van cayendo; aún no se puede lanzar
    PLAYING = auto()
    PAUSED = auto()
    LEVEL_COMPLETE = auto()
    GAME_OVER = auto()
    NAME_ENTRY = auto()      # la puntuación entra en la tabla: iniciales
    SCORES = auto()          # tabla de récords


def layout_for(level):
    """Diseño de este nivel; al pasar el último se vuelve al primero."""
    return LEVEL_LAYOUTS[(level - 1) % len(LEVEL_LAYOUTS)]


def build_bricks(level):
    """Crea la rejilla del nivel a partir de su diseño, centrada en pantalla."""
    _, rows = layout_for(level)
    cols = len(rows[0])
    usable = WIDTH - 2 * BRICK_SIDE_MARGIN - (cols - 1) * BRICK_GAP
    w = usable // cols
    total = cols * w + (cols - 1) * BRICK_GAP
    start_x = (WIDTH - total) // 2
    # Los ladrillos duros aguantan más golpes según se avanza
    bonus = min(MAX_EXTRA_HITS, (level - 1) // HITS_BONUS_EVERY_LEVELS)

    bricks = []
    for row, line in enumerate(rows):
        for col, char in enumerate(line):
            if char == EMPTY_CELL:
                continue
            color, points, hits = BRICK_TYPES[char]
            if hits is not None and hits > 1:
                hits += bonus
            x = start_x + col * (w + BRICK_GAP)
            y = BRICK_TOP + row * (BRICK_HEIGHT + BRICK_GAP)
            bricks.append(Brick(x, y, w, BRICK_HEIGHT, color, points, hits))
    return bricks


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 72)
        # Capa semitransparente reutilizable para los menús superpuestos
        self.overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.overlay.fill(OVERLAY_COLOR)
        # La zona de juego se dibuja aparte para poder sacudirla sin mover el HUD
        self.scene = pygame.Surface((WIDTH, HEIGHT))
        # Negro opaco al que se le cambia la transparencia para los fundidos
        self.fade = pygame.Surface((WIDTH, HEIGHT))
        self.fade.fill((0, 0, 0))
        self.sounds = SoundBank()
        self.scores = ScoreTable()

        self.name = ""              # iniciales que se están escribiendo
        self.highlight = None       # puesto recién conseguido, para resaltarlo
        self.new_game()
        self.set_state(State.MENU)

    def set_state(self, state):
        """Cambia de estado y pone a cero el reloj de lo que lleva en él.

        Ese reloj mueve la entrada de nivel, el parpadeo del cursor y el
        retardo antes de aceptar ESPACIO en los carteles.
        """
        self.state = state
        self.state_time = 0.0

    # ---------- Control de partida ----------
    def new_game(self):
        self.score = 0
        self.lives = START_LIVES
        self.level = 1
        self.start_level()

    def start_level(self):
        """Prepara el nivel y abre su entrada animada."""
        self.paddle = Paddle()
        # Desde la fase 3 puede haber varias pelotas en juego a la vez
        self.balls = [Ball(self.paddle)]
        self.bricks = build_bricks(self.level)
        self.powerups = []          # cápsulas cayendo
        self.effects = {}           # tipo -> segundos que le quedan
        self.particles = []
        self.shake_power = 0.0
        self.shake_time = 0.0
        self.shake_total = 0.0
        self.intro_rows = len(layout_for(self.level)[1])
        self.set_state(State.LEVEL_INTRO)

    def finish_intro(self):
        self.set_state(State.PLAYING)
        self.sounds.play("ready")

    def finish_game(self):
        """Tras la partida: a escribir el nombre si entra en la tabla, si no al menú."""
        if self.scores.rank_for(self.score) is None:
            self.set_state(State.MENU)
        else:
            self.name = self.scores.last_name
            self.set_state(State.NAME_ENTRY)

    def save_score(self):
        self.highlight = self.scores.add(self.name, self.score, self.level)
        self.sounds.play("record")
        self.set_state(State.SCORES)

    def ball_speed(self):
        """Velocidad que deben tener las pelotas ahora mismo."""
        speed = BALL_SPEED * (1 + SPEED_INCREASE_PER_LEVEL * (self.level - 1))
        if "SLOW" in self.effects:
            speed *= BALL_SLOW_FACTOR
        return speed

    def sync_balls(self):
        """Aplica a todas las pelotas los efectos que dependen de ellas."""
        speed = self.ball_speed()
        sticky = "CATCH" in self.effects
        for ball in self.balls:
            ball.set_speed(speed)
            ball.sticky = sticky

    def clear_effects(self):
        """Cancela todos los efectos y devuelve paleta y pelotas a su estado base."""
        self.effects.clear()
        self.paddle.set_width(PADDLE_WIDTH)
        self.sync_balls()

    def launch_balls(self):
        speed = self.ball_speed()
        launched = False
        for ball in self.balls:
            launched = launched or ball.stuck
            ball.launch(speed)
        if launched:
            self.sounds.play("launch")

    def lose_life(self):
        self.lives -= 1
        self.add_shake(*SHAKE_ON_LIFE_LOST)
        if self.lives <= 0:
            self.set_state(State.GAME_OVER)
            self.sounds.play("over")
        else:
            self.sounds.play("lose")
            # Se pierden los power-ups activos y las cápsulas que estaban cayendo
            self.powerups.clear()
            self.clear_effects()
            self.balls = [Ball(self.paddle)]

    # ---------- Ladrillos ----------
    def hit_brick(self, brick):
        """Aplica un golpe. Solo puntúa y suelta cápsula si el ladrillo se rompe."""
        if not brick.take_hit():
            # Aún aguanta, o es indestructible: solo un golpe seco y chispas
            self.sounds.play("brick")
            self.spawn_particles(brick.rect, brick.color, PARTICLE_HIT_COUNT)
            return
        self.bricks.remove(brick)
        self.score += brick.points
        self.sounds.play("break")
        self.spawn_particles(brick.rect, brick.color, PARTICLE_BREAK_COUNT)
        self.add_shake(*SHAKE_ON_BREAK)
        if random.random() < POWERUP_DROP_CHANCE:
            kind = random.choices(POWERUP_KINDS, POWERUP_WEIGHTS)[0]
            self.powerups.append(PowerUp(kind, brick.rect.centerx, brick.rect.centery))

    def level_cleared(self):
        """El nivel acaba cuando no queda ningún ladrillo rompible."""
        return not any(brick.breakable for brick in self.bricks)

    # ---------- Power-ups ----------

    def apply_powerup(self, kind):
        """Aplica el efecto de una cápsula recogida."""
        self.score += POWERUP_POINTS
        self.sounds.play("powerup")

        if kind == "WIDE":
            self.effects.pop("SHRINK", None)      # ANCHA y ESTRECHA se anulan
            self.paddle.set_width(PADDLE_WIDTH * PADDLE_WIDE_FACTOR)
        elif kind == "SHRINK":
            self.effects.pop("WIDE", None)
            self.paddle.set_width(PADDLE_WIDTH * PADDLE_SHRINK_FACTOR)
        elif kind == "MULTI":
            self.split_balls()
        elif kind == "LIFE":
            self.lives = min(MAX_LIVES, self.lives + 1)

        if kind in TIMED_POWERUPS:
            self.effects[kind] = POWERUP_DURATION
        if kind in ("SLOW", "CATCH"):
            self.sync_balls()

    def split_balls(self):
        """Multi-bola: clona una pelota en movimiento abriendo el ángulo."""
        source = next((b for b in self.balls if not b.stuck), None)
        if source is None:
            # Todas estaban pegadas a la paleta: la cápsula lanza la primera
            source = self.balls[0]
            source.launch(self.ball_speed())
        for i in range(MULTIBALL_EXTRA):
            sign = 1 if i % 2 == 0 else -1
            angle = sign * MULTIBALL_SPREAD * (i // 2 + 1)
            self.balls.append(source.clone(angle))

    def update_effects(self, dt):
        for kind in list(self.effects):
            self.effects[kind] -= dt
            if self.effects[kind] <= 0:
                del self.effects[kind]
                self.end_effect(kind)

    def end_effect(self, kind):
        if kind in ("WIDE", "SHRINK"):
            self.paddle.set_width(PADDLE_WIDTH)
        else:
            self.sync_balls()

    def update_powerups(self, dt):
        remaining = []
        for capsule in self.powerups:
            capsule.update(dt)
            if capsule.rect.colliderect(self.paddle.rect):
                self.apply_powerup(capsule.kind)
            elif capsule.rect.top < HEIGHT:
                remaining.append(capsule)
        self.powerups = remaining

    # ---------- Efectos visuales ----------
    def spawn_particles(self, rect, color, count):
        if len(self.particles) >= MAX_PARTICLES:
            return
        self.particles.extend(
            Particle(rect.centerx, rect.centery, color) for _ in range(count))

    def update_particles(self, dt):
        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def add_shake(self, power, seconds):
        """Se queda con la sacudida más fuerte de las que haya en marcha."""
        if power * seconds > self.shake_power * self.shake_time:
            self.shake_power = power
            self.shake_total = self.shake_time = seconds

    def shake_offset(self):
        """Desplazamiento de la zona de juego; se va calmando solo."""
        if self.shake_time <= 0:
            return (0, 0)
        power = self.shake_power * (self.shake_time / self.shake_total)
        return (round(random.uniform(-power, power)),
                round(random.uniform(-power, power)))

    # ---------- Entrada ----------
    def handle_events(self):
        """Procesa eventos según el estado. Devuelve False para cerrar el juego."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Si la ventana pierde el foco en plena partida, pausamos
            if event.type == pygame.WINDOWFOCUSLOST and self.state == State.PLAYING:
                self.set_state(State.PAUSED)

            if event.type != pygame.KEYDOWN:
                continue
            key = event.key

            # Escribiendo el nombre, las teclas son letras: M no silencia
            if self.state == State.NAME_ENTRY:
                self.handle_name_key(event)
                continue

            # El silencio se conmuta en cualquier otro estado
            if key == pygame.K_m:
                self.sounds.toggle_mute()
                continue

            # Los carteles ignoran ESPACIO un momento tras aparecer
            ready = self.state_time >= SCREEN_INPUT_DELAY

            if self.state == State.MENU:
                if key == pygame.K_SPACE:
                    self.new_game()
                elif key == pygame.K_t:
                    self.highlight = None
                    self.set_state(State.SCORES)
                elif key == pygame.K_ESCAPE:
                    return False

            elif self.state == State.LEVEL_INTRO:
                if key == pygame.K_SPACE:
                    self.finish_intro()

            elif self.state == State.PLAYING:
                if key == pygame.K_SPACE:
                    self.launch_balls()
                elif key in (pygame.K_p, pygame.K_ESCAPE):
                    self.set_state(State.PAUSED)

            elif self.state == State.PAUSED:
                if key in (pygame.K_p, pygame.K_ESCAPE):
                    self.set_state(State.PLAYING)
                elif key == pygame.K_q:
                    self.finish_game()

            elif self.state == State.LEVEL_COMPLETE:
                if key == pygame.K_SPACE and ready:
                    self.level += 1
                    self.start_level()

            elif self.state == State.GAME_OVER:
                if key == pygame.K_SPACE and ready:
                    self.finish_game()

            elif self.state == State.SCORES:
                if key in (pygame.K_SPACE, pygame.K_ESCAPE,
                           pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.set_state(State.MENU)
        return True

    def handle_name_key(self, event):
        """Edición de las iniciales: letras y cifras, borrar, y ENTER para guardar."""
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.name:
                self.save_score()
        elif event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
        else:
            char = event.unicode.upper()
            if char and char in NAME_CHARS and len(self.name) < NAME_MAX_LENGTH:
                self.name += char
                self.sounds.play("type")

    def read_direction(self):
        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1
        return direction

    # ---------- Lógica ----------
    def update(self, dt, direction):
        # La decoración corre en todos los estados menos en pausa: si no, una
        # sacudida iniciada justo antes del game over temblaría para siempre.
        if self.state != State.PAUSED:
            self.update_particles(dt)
            self.shake_time = max(0.0, self.shake_time - dt)
        self.state_time += dt
        # En la entrada del nivel la paleta ya se mueve (y la pelota pegada la
        # sigue), pero no se puede lanzar hasta que acaben de caer los ladrillos
        if self.state == State.LEVEL_INTRO:
            self.paddle.update(dt, direction)
            for ball in self.balls:
                ball.update(dt, self.paddle, self.bricks)
            if self.state_time >= LEVEL_INTRO_TIME:
                self.finish_intro()
            return
        # La simulación, en cambio, solo avanza mientras se juega
        if self.state != State.PLAYING:
            return
        self.paddle.update(dt, direction)
        self.update_effects(dt)
        self.update_balls(dt)
        self.update_powerups(dt)
        # Si la última pelota se perdió con el último ladrillo, manda el game over
        if self.state == State.PLAYING and self.level_cleared():
            self.set_state(State.LEVEL_COMPLETE)
            self.sounds.play("level")

    def update_balls(self, dt):
        """Mueve cada pelota; solo se pierde una vida cuando no queda ninguna."""
        survivors = []
        bounces = set()
        for ball in self.balls:
            report = ball.update(dt, self.paddle, self.bricks)
            # Un solo sonido por tipo de rebote aunque choquen varias pelotas
            bounces.update(report.bounces)
            for brick in report.bricks:
                # Se resuelve al momento para que las demás pelotas de este frame
                # vean ya el ladrillo roto y no lo vuelvan a puntuar
                self.hit_brick(brick)
            if report.lost:
                edge = pygame.Rect(round(ball.pos.x), HEIGHT - 6, 1, 1)
                self.spawn_particles(edge, BALL_COLOR, PARTICLE_LOST_COUNT)
            else:
                survivors.append(ball)
        for bounce in bounces:
            self.sounds.play(bounce)
        self.balls = survivors
        if not self.balls:
            self.lose_life()

    # ---------- Dibujo ----------
    def draw_text(self, text, font, center, color=TEXT_COLOR, alpha=255):
        surf = font.render(text, True, color)
        if alpha < 255:
            surf.set_alpha(alpha)
        self.screen.blit(surf, surf.get_rect(center=center))

    def draw_hud(self):
        y = HUD_HEIGHT / 2
        score = self.font.render(f"PUNTOS {self.score}", True, TEXT_COLOR)
        self.screen.blit(score, score.get_rect(midleft=(16, y)))
        self.draw_text(f"NIVEL {self.level} · {layout_for(self.level)[0]}",
                       self.font, (WIDTH / 2, y))
        lives = self.font.render(f"VIDAS {self.lives}", True, TEXT_COLOR)
        self.screen.blit(lives, lives.get_rect(midright=(WIDTH - 16, y)))
        pygame.draw.line(self.screen, HUD_LINE_COLOR, (0, HUD_HEIGHT - 1), (WIDTH, HUD_HEIGHT - 1), 2)

    def draw_active_effects(self):
        """Etiquetas de los efectos activos con los segundos restantes."""
        x = 16
        for kind, remaining in self.effects.items():
            label = f"{POWERUP_NAMES[kind]} {remaining:.0f}"
            surf = self.small_font.render(label, True, POWERUP_COLORS[kind])
            rect = surf.get_rect(midleft=(x, HEIGHT - 16))
            self.screen.blit(surf, rect)
            x = rect.right + 16
        if self.sounds.muted or not self.sounds.enabled:
            muted = self.small_font.render("SIN SONIDO", True, DIM_TEXT_COLOR)
            self.screen.blit(muted, muted.get_rect(midright=(WIDTH - 16, HEIGHT - 16)))

    def draw_powerup_legend(self, y):
        """Leyenda del menú: qué hace cada letra de cápsula."""
        surfaces = [
            self.small_font.render(
                f"{POWERUP_LETTERS[k]} {POWERUP_NAMES[k]}", True, POWERUP_COLORS[k])
            for k in POWERUP_KINDS
        ]
        gap = 16
        total = sum(s.get_width() for s in surfaces) + gap * (len(surfaces) - 1)
        x = (WIDTH - total) / 2
        for surf in surfaces:
            self.screen.blit(surf, surf.get_rect(midleft=(x, y)))
            x += surf.get_width() + gap

    def draw_playfield(self):
        """Dibuja la zona de juego aparte y la vuelca aplicando la sacudida."""
        self.scene.fill(BG_COLOR)
        if self.state == State.LEVEL_INTRO:
            # Mientras caen no deben asomar por encima del marcador
            self.scene.set_clip(pygame.Rect(0, PLAY_TOP, WIDTH, HEIGHT - PLAY_TOP))
            for brick in self.bricks:
                brick.draw(self.scene, self.intro_drop(brick))
            self.scene.set_clip(None)
        else:
            for brick in self.bricks:
                brick.draw(self.scene)
        for capsule in self.powerups:
            capsule.draw(self.scene)
        for particle in self.particles:
            particle.draw(self.scene)
        self.paddle.draw(self.scene)
        for ball in self.balls:
            ball.draw(self.scene)
        self.screen.blit(self.scene, self.shake_offset())

    def intro_drop(self, brick):
        """Cuánto le falta a un ladrillo por caer en la entrada del nivel.

        Las filas caen de abajo arriba: así ninguna atraviesa a otra que ya
        haya aterrizado.
        """
        row = round((brick.rect.y - BRICK_TOP) / (BRICK_HEIGHT + BRICK_GAP))
        delay = (self.intro_rows - 1 - row) * INTRO_ROW_DELAY
        progress = max(0.0, min(1.0, (self.state_time - delay) / INTRO_DROP_TIME))
        eased = 1 - (1 - progress) ** 3          # frena al llegar
        return -round((1 - eased) * INTRO_DROP_DISTANCE)

    def draw_intro(self):
        """Cartel del nivel que se desvanece, y fundido desde negro al principio."""
        t = self.state_time
        fade_out = LEVEL_INTRO_TIME - INTRO_FADE_TIME
        alpha = 255 if t < fade_out else round(255 * (LEVEL_INTRO_TIME - t) / INTRO_FADE_TIME)
        alpha = max(0, min(255, alpha))
        self.draw_text(f"NIVEL {self.level}", self.big_font,
                       (WIDTH / 2, HEIGHT / 2 + 20), alpha=alpha)
        self.draw_text(layout_for(self.level)[0], self.font,
                       (WIDTH / 2, HEIGHT / 2 + 70), DIM_TEXT_COLOR, alpha)
        if t < INTRO_FADE_TIME:
            self.fade.set_alpha(round(255 * (1 - t / INTRO_FADE_TIME)))
            self.screen.blit(self.fade, (0, 0))

    def draw_overlay(self, title, lines):
        """Oscurece el juego y muestra un título con líneas de ayuda."""
        self.screen.blit(self.overlay, (0, 0))
        cy = HEIGHT / 2 - 40
        self.draw_text(title, self.big_font, (WIDTH / 2, cy))
        for i, line in enumerate(lines):
            self.draw_text(line, self.font, (WIDTH / 2, cy + 70 + i * 34), DIM_TEXT_COLOR)

    def hint(self, text):
        """Línea de ayuda de un cartel: aparece cuando ya acepta la tecla."""
        return [text] if self.state_time >= SCREEN_INPUT_DELAY else []

    def draw_name_entry(self):
        rank = self.scores.rank_for(self.score)
        self.screen.blit(self.overlay, (0, 0))
        title = "¡NUEVO RÉCORD!" if rank == 0 else "¡A LA TABLA!"
        self.draw_text(title, self.big_font, (WIDTH / 2, 255), HIGHLIGHT_COLOR)
        self.draw_text(f"Puesto {rank + 1} · {self.score} puntos · nivel {self.level}",
                       self.font, (WIDTH / 2, 310))
        self.draw_text("Escribe tus iniciales", self.font, (WIDTH / 2, 355), DIM_TEXT_COLOR)

        # Una casilla por letra; el cursor parpadea en la siguiente libre
        box_w, gap = 52, 14
        x0 = WIDTH / 2 - (NAME_MAX_LENGTH * box_w + (NAME_MAX_LENGTH - 1) * gap) / 2
        cursor_on = int(self.state_time * 2.5) % 2 == 0
        for i in range(NAME_MAX_LENGTH):
            cx = x0 + i * (box_w + gap) + box_w / 2
            if i < len(self.name):
                self.draw_text(self.name[i], self.big_font, (cx, 410), HIGHLIGHT_COLOR)
            line_color = (HIGHLIGHT_COLOR if i == len(self.name) and cursor_on
                          else DIM_TEXT_COLOR)
            pygame.draw.line(self.screen, line_color,
                             (cx - box_w / 2, 440), (cx + box_w / 2, 440), 3)

        self.draw_text("ENTER: guardar   RETROCESO: borrar", self.font,
                       (WIDTH / 2, 490), DIM_TEXT_COLOR)

    def draw_scores(self):
        self.draw_text("RÉCORDS", self.big_font, (WIDTH / 2, 80))
        if not self.scores.entries:
            self.draw_text("Todavía no hay ninguna puntuación", self.font,
                           (WIDTH / 2, 260), DIM_TEXT_COLOR)
        # Columnas (x, anclaje): puesto, iniciales, puntos y nivel
        columns = ((265, "midright"), (295, "midleft"),
                   (480, "midright"), (545, "center"))
        for label, (x, anchor) in zip(("", "NOMBRE", "PUNTOS", "NIVEL"), columns):
            surf = self.small_font.render(label, True, DIM_TEXT_COLOR)
            self.screen.blit(surf, surf.get_rect(**{anchor: (x, 140)}))
        for i, entry in enumerate(self.scores.entries):
            y = 175 + i * 32
            color = HIGHLIGHT_COLOR if i == self.highlight else TEXT_COLOR
            cells = (f"{i + 1}.", entry.name, str(entry.score), str(entry.level))
            for text, (x, anchor) in zip(cells, columns):
                surf = self.font.render(text, True, color)
                self.screen.blit(surf, surf.get_rect(**{anchor: (x, y)}))
        if not self.scores.persistent:
            self.draw_text("No se pueden guardar en disco: solo duran esta sesión",
                           self.small_font, (WIDTH / 2, HEIGHT - 70), DIM_TEXT_COLOR)
        self.draw_text("ESPACIO: volver al menú", self.font,
                       (WIDTH / 2, HEIGHT - 40), DIM_TEXT_COLOR)

    def draw_menu(self):
        self.draw_text("ARKANOID", self.big_font, (WIDTH / 2, 200))
        self.draw_text("ESPACIO para empezar", self.font, (WIDTH / 2, 290))
        self.draw_text("Flechas o A/D: mover   P: pausa   M: sonido   ESC: salir",
                       self.font, (WIDTH / 2, 330), DIM_TEXT_COLOR)
        self.draw_text("Atrapa las cápsulas que sueltan los ladrillos",
                       self.font, (WIDTH / 2, 390), DIM_TEXT_COLOR)
        self.draw_powerup_legend(425)
        self.draw_text("Los plateados y dorados aguantan varios golpes; los grises no se rompen",
                       self.small_font, (WIDTH / 2, 465), DIM_TEXT_COLOR)
        best = self.scores.best()
        records = f"Récord: {best}   ·   T: ver la tabla" if best else "T: tabla de récords"
        self.draw_text(records, self.font, (WIDTH / 2, 510), DIM_TEXT_COLOR)

    def draw(self):
        self.screen.fill(BG_COLOR)

        if self.state == State.MENU:
            self.draw_menu()
            return
        if self.state == State.SCORES:
            self.draw_scores()
            return

        self.draw_playfield()
        self.draw_hud()
        self.draw_active_effects()

        if self.state == State.LEVEL_INTRO:
            self.draw_intro()
        elif self.state == State.PLAYING and any(ball.stuck for ball in self.balls):
            self.draw_text("ESPACIO para lanzar", self.font, (WIDTH / 2, HEIGHT / 2 + 80))
        elif self.state == State.PAUSED:
            self.draw_overlay("PAUSA", ["P o ESC: continuar", "Q: terminar la partida"])
        elif self.state == State.LEVEL_COMPLETE:
            self.draw_overlay(f"¡NIVEL {self.level} COMPLETADO!",
                              [f"Puntos: {self.score}",
                               f"Siguiente: {layout_for(self.level + 1)[0]}"]
                              + self.hint("ESPACIO: continuar"))
        elif self.state == State.GAME_OVER:
            rank = self.scores.rank_for(self.score)
            if rank is None:
                lines = [f"Puntos: {self.score}    Récord: {self.scores.best()}"]
                lines += self.hint("ESPACIO: volver al menú")
            else:
                verdict = "¡NUEVO RÉCORD!" if rank == 0 else f"Entras en la tabla: puesto {rank + 1}"
                lines = [f"Puntos: {self.score}", verdict]
                lines += self.hint("ESPACIO: escribir tu nombre")
            self.draw_overlay("GAME OVER", lines)
        elif self.state == State.NAME_ENTRY:
            self.draw_name_entry()

    # ---------- Bucle principal ----------
    def run(self):
        running = True
        while running:
            # dt en segundos; lo limitamos para evitar saltos si la ventana se congela
            dt = min(self.clock.tick(FPS) / 1000, 1 / 30)
            running = self.handle_events()
            self.update(dt, self.read_direction())
            self.draw()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
