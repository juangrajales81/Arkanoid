"""Entidades del juego: paleta, pelota, ladrillos y cápsulas de power-up."""

import math
import random

import pygame

from settings import (
    WIDTH, HEIGHT, PLAY_TOP,
    PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED, PADDLE_Y, PADDLE_COLOR,
    PADDLE_MIN_WIDTH, PADDLE_MAX_WIDTH,
    BALL_RADIUS, BALL_SPEED, BALL_COLOR, MAX_BOUNCE_ANGLE,
    BRICK_DAMAGE_DARKEN, BRICK_PIP_COLOR,
    POWERUP_WIDTH, POWERUP_HEIGHT, POWERUP_SPEED,
    POWERUP_COLORS, POWERUP_LETTERS, POWERUP_TEXT_COLOR,
)


class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, PADDLE_WIDTH, PADDLE_HEIGHT)
        # Guardamos la posición como float para que el movimiento sea suave;
        # el Rect solo admite enteros.
        self.x = WIDTH / 2
        self.rect.center = (round(self.x), PADDLE_Y)

    def update(self, dt, direction):
        """direction: -1 izquierda, 0 quieto, 1 derecha."""
        self.x += direction * PADDLE_SPEED * dt
        self._clamp()

    def set_width(self, width):
        """Cambia el ancho conservando el centro (power-ups ANCHA / ESTRECHA)."""
        self.rect.width = max(PADDLE_MIN_WIDTH, min(PADDLE_MAX_WIDTH, round(width)))
        self._clamp()

    def _clamp(self):
        """Mantiene la paleta dentro de la pantalla y refleja el float en el Rect."""
        half = self.rect.width / 2
        self.x = max(half, min(WIDTH - half, self.x))
        self.rect.centerx = round(self.x)
        self.rect.centery = PADDLE_Y

    def draw(self, surface):
        pygame.draw.rect(surface, PADDLE_COLOR, self.rect, border_radius=6)


class Brick:
    def __init__(self, x, y, w, h, color, points, hits=1):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.points = points
        self.max_hits = hits   # None = indestructible
        self.hits = hits

    @property
    def breakable(self):
        return self.max_hits is not None

    def take_hit(self):
        """Resta un golpe. Devuelve True si el ladrillo se ha roto."""
        if not self.breakable:
            return False
        self.hits -= 1
        return self.hits <= 0

    def _damaged_color(self):
        """El ladrillo se va oscureciendo conforme le quedan menos golpes."""
        if not self.breakable or self.max_hits == 1:
            return self.color
        wear = 1 - self.hits / self.max_hits
        factor = 1 - BRICK_DAMAGE_DARKEN * wear
        return tuple(round(c * factor) for c in self.color)

    def draw(self, surface):
        color = self._damaged_color()
        pygame.draw.rect(surface, color, self.rect, border_radius=3)
        # Pequeño brillo en el borde superior para dar volumen
        highlight = tuple(min(255, c + 70) for c in color)
        pygame.draw.line(
            surface, highlight,
            (self.rect.left + 3, self.rect.top + 2),
            (self.rect.right - 4, self.rect.top + 2), 2,
        )
        if not self.breakable:
            # Borde marcado: se lee de un vistazo que ese no se rompe
            pygame.draw.rect(surface, highlight, self.rect, 2, border_radius=3)
        elif self.max_hits > 1:
            self._draw_pips(surface)

    def _draw_pips(self, surface):
        """Un punto por cada golpe que aún aguanta."""
        gap = 8
        cx = self.rect.centerx - gap * (self.hits - 1) / 2
        for i in range(self.hits):
            pygame.draw.circle(
                surface, BRICK_PIP_COLOR,
                (round(cx + i * gap), self.rect.centery + 3), 2)


class Ball:
    def __init__(self, paddle=None):
        self.radius = BALL_RADIUS
        self.pos = pygame.Vector2()
        self.vel = pygame.Vector2()
        self.stuck = False
        self.stick_offset = 0.0   # desplazamiento respecto al centro de la paleta
        self.sticky = False       # power-up ATRAPA: se queda pegada al rebotar
        if paddle is not None:
            self.stick_to(paddle)

    @property
    def rect(self):
        r = self.radius
        return pygame.Rect(round(self.pos.x - r), round(self.pos.y - r), 2 * r, 2 * r)

    def stick_to(self, paddle, offset=0.0):
        """Deja la pelota pegada sobre la paleta, esperando el lanzamiento."""
        self.stuck = True
        self.vel.update(0, 0)
        limit = max(0.0, paddle.rect.width / 2 - self.radius)
        self.stick_offset = max(-limit, min(limit, offset))
        self._follow(paddle)

    def _follow(self, paddle):
        self.pos.update(paddle.rect.centerx + self.stick_offset,
                        paddle.rect.top - self.radius)

    def launch(self, speed=BALL_SPEED):
        if not self.stuck:
            return
        self.stuck = False
        # Ángulo inicial aleatorio, siempre hacia arriba
        angle = math.radians(random.uniform(-30, 30))
        self.vel.update(math.sin(angle), -math.cos(angle))
        self.vel *= speed

    def set_speed(self, speed):
        """Cambia el módulo de la velocidad sin tocar la dirección."""
        if self.vel.length_squared() > 0:
            self.vel.scale_to_length(speed)

    def clone(self, angle_deg):
        """Copia de la pelota en la misma posición y con la dirección girada.

        Es lo que usa el power-up MULTI; la pelota original no se modifica.
        """
        other = Ball()
        other.pos.update(self.pos)
        other.vel = self.vel.rotate(angle_deg)
        other.sticky = self.sticky
        return other

    def update(self, dt, paddle, bricks):
        """Mueve la pelota y resuelve colisiones.

        Devuelve (ladrillos_golpeados, pelota_perdida).
        """
        if self.stuck:
            self._follow(paddle)
            return [], False

        r = self.radius
        hit = []

        # --- Movimiento en X y sus colisiones ---
        self.pos.x += self.vel.x * dt
        if self.pos.x - r < 0:
            self.pos.x = r
            self.vel.x = abs(self.vel.x)
        elif self.pos.x + r > WIDTH:
            self.pos.x = WIDTH - r
            self.vel.x = -abs(self.vel.x)

        brick = self._first_collision(bricks)
        if brick:
            if self.vel.x > 0:
                self.pos.x = brick.rect.left - r
            else:
                self.pos.x = brick.rect.right + r
            self.vel.x = -self.vel.x
            hit.append(brick)

        # --- Movimiento en Y y sus colisiones ---
        self.pos.y += self.vel.y * dt
        if self.pos.y - r < PLAY_TOP:
            self.pos.y = PLAY_TOP + r
            self.vel.y = abs(self.vel.y)

        brick = self._first_collision([b for b in bricks if b not in hit])
        if brick:
            if self.vel.y > 0:
                self.pos.y = brick.rect.top - r
            else:
                self.pos.y = brick.rect.bottom + r
            self.vel.y = -self.vel.y
            hit.append(brick)

        # --- Paleta: solo si la pelota baja y aún no la ha rebasado ---
        if (self.vel.y > 0
                and self.pos.y < paddle.rect.bottom
                and self.rect.colliderect(paddle.rect)):
            self._bounce_on_paddle(paddle)

        lost = self.pos.y - r > HEIGHT
        return hit, lost

    def _first_collision(self, bricks):
        ball_rect = self.rect
        for brick in bricks:
            if ball_rect.colliderect(brick.rect):
                return brick
        return None

    def _bounce_on_paddle(self, paddle):
        """El ángulo de salida depende de dónde golpea: centro = recto,
        extremos = ángulo máximo. Esto es lo que da control al jugador."""
        half = paddle.rect.width / 2
        offset = (self.pos.x - paddle.rect.centerx) / half
        offset = max(-1.0, min(1.0, offset))
        angle = math.radians(offset * MAX_BOUNCE_ANGLE)
        speed = self.vel.length()
        self.vel.update(math.sin(angle) * speed, -math.cos(angle) * speed)
        self.pos.y = paddle.rect.top - self.radius
        # Con ATRAPA la pelota no sale rebotada: se queda pegada donde cayó
        if self.sticky:
            self.stick_to(paddle, self.pos.x - paddle.rect.centerx)

    def draw(self, surface):
        pygame.draw.circle(surface, BALL_COLOR, (round(self.pos.x), round(self.pos.y)), self.radius)


_CAPSULE_FONT = None


def _capsule_font():
    """Fuente de la letra de la cápsula.

    Se crea en el primer dibujado y no al importar el módulo, porque en ese
    momento pygame.font todavía no está inicializado.
    """
    global _CAPSULE_FONT
    if _CAPSULE_FONT is None:
        _CAPSULE_FONT = pygame.font.Font(None, 22)
    return _CAPSULE_FONT


class PowerUp:
    """Cápsula que cae desde un ladrillo destruido hasta salir de la pantalla.

    Igual que la paleta, la posición real es un float y el Rect es su reflejo
    redondeado: si se moviera el Rect se perdería la parte decimal cada frame.
    """

    def __init__(self, kind, centerx, centery):
        self.kind = kind
        self.y = float(centery)
        self.rect = pygame.Rect(0, 0, POWERUP_WIDTH, POWERUP_HEIGHT)
        self.rect.center = (round(centerx), round(self.y))

    def update(self, dt):
        self.y += POWERUP_SPEED * dt
        self.rect.centery = round(self.y)

    def draw(self, surface):
        color = POWERUP_COLORS[self.kind]
        pygame.draw.rect(surface, color, self.rect, border_radius=7)
        pygame.draw.rect(surface, POWERUP_TEXT_COLOR, self.rect, 2, border_radius=7)
        letter = _capsule_font().render(
            POWERUP_LETTERS[self.kind], True, POWERUP_TEXT_COLOR)
        surface.blit(letter, letter.get_rect(center=self.rect.center))
