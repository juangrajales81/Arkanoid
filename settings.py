"""Configuración general del juego: tamaños, velocidades y colores."""

# Ventana
WIDTH, HEIGHT = 800, 600
FPS = 60
TITLE = "Arkanoid"

# Colores
BG_COLOR = (15, 15, 30)
TEXT_COLOR = (230, 230, 240)
DIM_TEXT_COLOR = (140, 140, 160)
HUD_LINE_COLOR = (60, 60, 90)
OVERLAY_COLOR = (0, 0, 0, 160)   # negro semitransparente para menús

# Marcador (HUD) en la parte superior; la pelota rebota por debajo de él
HUD_HEIGHT = 40
PLAY_TOP = HUD_HEIGHT

# Reglas
START_LIVES = 3
SPEED_INCREASE_PER_LEVEL = 0.10   # +10 % de velocidad de pelota por nivel

# Paleta
PADDLE_WIDTH = 110
PADDLE_HEIGHT = 16
PADDLE_SPEED = 560          # píxeles por segundo
PADDLE_Y = HEIGHT - 40      # posición vertical (centro)
PADDLE_COLOR = (200, 200, 220)

# Pelota
BALL_RADIUS = 8
BALL_SPEED = 400            # píxeles por segundo
BALL_COLOR = (255, 255, 255)
MAX_BOUNCE_ANGLE = 60       # grados respecto a la vertical al golpear el borde de la paleta

# Ladrillos: geometría de la rejilla (el número de filas y columnas lo marca
# el diseño del nivel, más abajo)
BRICK_HEIGHT = 22
BRICK_GAP = 4
BRICK_TOP = 70
BRICK_SIDE_MARGIN = 20

# ---------------------------------------------------------------------------
# Fase 3: power-ups (cápsulas que sueltan los ladrillos)
# ---------------------------------------------------------------------------
POWERUP_DROP_CHANCE = 0.20   # probabilidad de que un ladrillo destruido suelte cápsula
POWERUP_WIDTH = 34
POWERUP_HEIGHT = 16
POWERUP_SPEED = 190          # píxeles por segundo de caída
POWERUP_DURATION = 12        # segundos que dura un efecto temporal
POWERUP_POINTS = 50          # puntos por atrapar una cápsula

# Tipos disponibles y su peso relativo en el sorteo (no tienen que sumar 100)
POWERUP_KINDS = ("WIDE", "SHRINK", "SLOW", "MULTI", "CATCH", "LIFE")
POWERUP_WEIGHTS = (22, 14, 16, 20, 18, 10)
# Los que caducan solos; MULTI y LIFE son de efecto inmediato
TIMED_POWERUPS = ("WIDE", "SHRINK", "SLOW", "CATCH")

POWERUP_LETTERS = {
    "WIDE": "E", "SHRINK": "R", "SLOW": "L",
    "MULTI": "M", "CATCH": "C", "LIFE": "V",
}
POWERUP_NAMES = {
    "WIDE": "ANCHA", "SHRINK": "ESTRECHA", "SLOW": "LENTA",
    "MULTI": "MULTI", "CATCH": "ATRAPA", "LIFE": "VIDA",
}
POWERUP_COLORS = {
    "WIDE": (46, 204, 113),    # verde
    "SHRINK": (231, 76, 60),   # rojo (es el único malo)
    "SLOW": (52, 152, 219),    # azul
    "MULTI": (155, 89, 182),   # morado
    "CATCH": (230, 126, 34),   # naranja
    "LIFE": (236, 64, 122),    # rosa
}
POWERUP_TEXT_COLOR = (20, 20, 30)

# Efectos concretos
PADDLE_WIDE_FACTOR = 1.6     # multiplicador de ancho con ANCHA
PADDLE_SHRINK_FACTOR = 0.6   # multiplicador de ancho con ESTRECHA
PADDLE_MIN_WIDTH = 60
PADDLE_MAX_WIDTH = 200
BALL_SLOW_FACTOR = 0.65      # velocidad de pelota mientras dura LENTA
MULTIBALL_EXTRA = 2          # pelotas que se añaden con MULTI
MULTIBALL_SPREAD = 25        # grados entre cada pelota nueva y la original
MAX_LIVES = 5                # tope de vidas acumulables con VIDA

# ---------------------------------------------------------------------------
# Fase 4: tipos de ladrillo y diseños de nivel
# ---------------------------------------------------------------------------
# Cada carácter de un diseño es un tipo: (color, puntos, golpes).
# golpes = None significa indestructible: rebota, no se rompe y no puntúa.
EMPTY_CELL = "."
BRICK_TYPES = {
    "R": ((231, 76, 60), 70, 1),      # rojo
    "O": ((230, 126, 34), 60, 1),     # naranja
    "Y": ((241, 196, 15), 50, 1),     # amarillo
    "G": ((46, 204, 113), 40, 1),     # verde
    "B": ((52, 152, 219), 30, 1),     # azul
    "P": ((155, 89, 182), 20, 1),     # morado
    "S": ((189, 195, 199), 90, 2),    # plata: aguanta 2 golpes
    "D": ((212, 175, 55), 130, 3),    # dorado: aguanta 3 golpes
    "X": ((88, 88, 112), 0, None),    # gris: indestructible
}
BRICK_DAMAGE_DARKEN = 0.45   # cuánto se oscurece un ladrillo al ir recibiendo golpes
BRICK_PIP_COLOR = (25, 25, 35)   # puntitos que indican los golpes que le quedan

# Los ladrillos duros (2+ golpes) ganan resistencia cada N niveles, hasta un tope.
HITS_BONUS_EVERY_LEVELS = 3
MAX_EXTRA_HITS = 2

# Diseños de nivel: (nombre, filas). Se recorren en orden y vuelven a empezar.
# Todas las filas de un diseño deben tener la misma longitud.
LEVEL_LAYOUTS = [
    ("CLÁSICO", [
        "RRRRRRRRRR",
        "OOOOOOOOOO",
        "YYYYYYYYYY",
        "GGGGGGGGGG",
        "BBBBBBBBBB",
        "PPPPPPPPPP",
    ]),
    ("PIRÁMIDE", [
        "....SS....",
        "...RRRR...",
        "..OOOOOO..",
        ".YYYYYYYY.",
        "GGGGGGGGGG",
        "..BBBBBB..",
    ]),
    ("FORTALEZA", [
        "XX.DDDD.XX",
        "..SSSSSS..",
        ".RRRRRRRR.",
        ".OOOOOOOO.",
        "..YYYYYY..",
        "...GGGG...",
    ]),
    ("DAMERO", [
        "S.S.S.S.S.",
        ".R.R.R.R.R",
        "O.O.O.O.O.",
        ".Y.Y.Y.Y.Y",
        "G.G.G.G.G.",
        ".B.B.B.B.B",
    ]),
    ("TÚNEL", [
        "..DDDDDD..",
        ".SS....SS.",
        "RR..XX..RR",
        "OO..XX..OO",
        ".YY....YY.",
        "..GGGGGG..",
    ]),
]
