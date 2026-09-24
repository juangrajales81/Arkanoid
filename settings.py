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

# ---------------------------------------------------------------------------
# Fase 5: sonido y efectos visuales
# ---------------------------------------------------------------------------
# El juego no lleva archivos de audio: los sonidos se sintetizan al arrancar a
# partir de estas recetas. Cada sonido es una lista de tramos que suenan
# seguidos; de cada tramo solo "ms" es obligatorio.
#   freq   Hz iniciales (0 = silencio)
#   to     Hz finales, si el tono debe barrer de uno a otro
#   shape  "square" (seco, arcade), "triangle" (suave) o "sine"
#   vol    volumen relativo del tramo (0-1)
#   decay  caída del volumen dentro del tramo (0 = plano, 10 = muy percusivo)
SOUND_SAMPLE_RATE = 44100
SOUND_BUFFER = 512           # muestras por bloque; bajo = menos retardo
SOUND_VOLUME = 0.35          # volumen maestro
SOUND_RECIPES = {
    "launch":   [{"freq": 300, "to": 760, "ms": 130, "shape": "triangle", "decay": 2}],
    "paddle":   [{"freq": 440, "ms": 60, "vol": 0.9, "decay": 6}],
    "wall":     [{"freq": 300, "ms": 45, "vol": 0.6, "decay": 8}],
    "brick":    [{"freq": 170, "ms": 55, "vol": 0.7, "decay": 11}],
    "break":    [{"freq": 900, "to": 380, "ms": 95, "decay": 5}],
    "powerup":  [{"freq": 660, "ms": 55, "shape": "triangle", "decay": 3},
                 {"freq": 880, "ms": 55, "shape": "triangle", "decay": 3},
                 {"freq": 1170, "ms": 90, "shape": "triangle", "decay": 4}],
    "lose":     [{"freq": 520, "to": 110, "ms": 380, "shape": "triangle", "decay": 2.5}],
    "level":    [{"freq": 523, "ms": 90, "shape": "triangle", "decay": 2},
                 {"freq": 659, "ms": 90, "shape": "triangle", "decay": 2},
                 {"freq": 784, "ms": 90, "shape": "triangle", "decay": 2},
                 {"freq": 1047, "ms": 260, "shape": "triangle", "decay": 3}],
    "over":     [{"freq": 392, "ms": 170, "shape": "triangle", "decay": 1.5},
                 {"freq": 330, "ms": 170, "shape": "triangle", "decay": 1.5},
                 {"freq": 262, "ms": 170, "shape": "triangle", "decay": 1.5},
                 {"freq": 196, "ms": 420, "shape": "triangle", "decay": 2.5}],
    # Fase 6: los ladrillos ya han caído y se puede lanzar
    "ready":    [{"freq": 392, "ms": 70, "shape": "triangle", "decay": 3},
                 {"freq": 784, "ms": 150, "shape": "triangle", "decay": 3}],
    # Fase 6: entra una puntuación en la tabla
    "record":   [{"freq": 784, "ms": 80, "shape": "triangle", "decay": 2},
                 {"freq": 988, "ms": 80, "shape": "triangle", "decay": 2},
                 {"freq": 1175, "ms": 80, "shape": "triangle", "decay": 2},
                 {"freq": 1568, "ms": 300, "shape": "triangle", "decay": 3}],
    "type":     [{"freq": 1200, "ms": 25, "vol": 0.5, "decay": 8}],
}

# Partículas: trocitos que saltan del ladrillo
PARTICLE_BREAK_COUNT = 10    # al romperlo
PARTICLE_HIT_COUNT = 3       # al golpearlo sin romperlo
PARTICLE_LOST_COUNT = 14     # al perder la pelota
PARTICLE_SPEED = (70, 280)   # rango de velocidad inicial en píxeles/s
PARTICLE_LIFE = (0.25, 0.6)  # rango de duración en segundos
PARTICLE_SIZE = (2, 5)       # rango de lado en píxeles
PARTICLE_GRAVITY = 700       # píxeles/s² hacia abajo
MAX_PARTICLES = 400          # tope de seguridad

# Sacudida de pantalla: (píxeles, segundos)
SHAKE_ON_BREAK = (2.5, 0.08)
SHAKE_ON_LIFE_LOST = (9, 0.35)

# ---------------------------------------------------------------------------
# Fase 6: récords en disco y transiciones entre niveles
# ---------------------------------------------------------------------------
# La tabla se guarda en la carpeta de datos del usuario que da SDL
# (en Windows, %APPDATA%\arkanoid\arkanoid\records.json).
SCORES_ORG = "arkanoid"
SCORES_APP = "arkanoid"
SCORES_FILE = "records.json"
SCORES_TABLE_SIZE = 10
NAME_MAX_LENGTH = 3            # iniciales, como en los recreativos
NAME_CHARS = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ0123456789"   # lo que se puede escribir
HIGHLIGHT_COLOR = (241, 196, 15)   # la puntuación recién conseguida en la tabla

# Tiempo mínimo en un cartel antes de aceptar ESPACIO, para que el jugador que
# venía machacando la barra no se lo salte sin verlo
SCREEN_INPUT_DELAY = 0.6

# Entrada de nivel: los ladrillos caen fila a fila, de abajo arriba
LEVEL_INTRO_TIME = 1.9         # segundos hasta que se puede lanzar
INTRO_ROW_DELAY = 0.09         # desfase entre filas
INTRO_DROP_TIME = 0.45         # lo que tarda en caer una fila
INTRO_DROP_DISTANCE = 260      # píxeles desde los que cae
INTRO_FADE_TIME = 0.35         # fundido desde negro al empezar el nivel
