# Arkanoid

Clon de Arkanoid / Breakout hecho en Python con [pygame-ce](https://pyga.me/).
Paleta, pelota, ladrillos de varios tipos, cápsulas de power-up y cinco diseños de
nivel que se repiten en bucle subiendo la dificultad. Con efectos de sonido, trozos
que saltan al romper, sacudida de pantalla y una tabla de récords que se guarda entre
partidas.

Una sola dependencia (pygame-ce) y ningún archivo de audio: **los sonidos se
sintetizan al arrancar**.

![Captura del juego](docs/captura.png)

## Requisitos

- Python 3.10 o superior (probado con 3.14)
- pygame-ce >= 2.5.5

## Instalación y ejecución

```bash
pip install -r requirements.txt
python main.py
```

## Controles

| Tecla | Acción |
|---|---|
| ← → o A / D | Mover la paleta |
| ESPACIO | Lanzar la pelota / empezar / continuar |
| P o ESC | Pausa |
| M | Silenciar / activar el sonido |
| Q (en pausa) | Terminar la partida |
| T (en el menú) | Ver la tabla de récords |
| ESC (en el menú) | Salir |

Al empezar cada nivel los ladrillos caen en su sitio; ESPACIO se salta la animación.

## Cómo se juega

Rompe todos los ladrillos sin que la pelota se te escape. El **ángulo de salida
depende de dónde golpea la pelota en la paleta**: por el centro sale recta, por los
extremos sale muy abierta. Ése es todo tu control de puntería.

### Ladrillos

| Ladrillo | Golpes | Puntos |
|---|---|---|
| De color (rojo → morado) | 1 | 70 → 20 |
| Plata | 2 | 90 |
| Dorado | 3 | 130 |
| Gris | indestructible | — |

Los ladrillos duros se oscurecen al recibir golpes y muestran un punto por cada golpe
que les queda. Cada 3 niveles aguantan uno más (hasta +2). Los grises no se rompen
nunca: el nivel termina cuando no queda ningún ladrillo *rompible*.

### Cápsulas

Al romper un ladrillo puede caer una cápsula. Atraparla con la paleta da 50 puntos y
su efecto (12 segundos los temporales):

| | Efecto |
|---|---|
| **E** | Paleta ancha |
| **R** | Paleta estrecha — la única mala |
| **L** | Pelota lenta |
| **M** | Multi-bola: dos pelotas extra |
| **C** | Atrapa: la pelota se pega a la paleta, ESPACIO la relanza |
| **V** | Vida extra (máximo 5) |

Perder una vida cancela todos los efectos activos.

### Niveles

Cinco diseños —CLÁSICO, PIRÁMIDE, FORTALEZA, DAMERO y TÚNEL— que se recorren en orden
y vuelven a empezar. Cada nivel añade un 10 % de velocidad a la pelota.

### Récords

Las 10 mejores puntuaciones se guardan con tres iniciales, los puntos y el nivel
alcanzado. Si tu partida entra en la tabla, al terminar se te pide escribir tus
iniciales (ENTER para guardar). La tabla vive en la carpeta de datos del usuario
—en Windows, `%APPDATA%\arkanoid\arkanoid\records.json`—; borra ese archivo para
empezar de cero.

## Estructura

| Archivo | Qué contiene |
|---|---|
| [`settings.py`](settings.py) | Todos los ajustes: tamaños, velocidades, colores, tipos de ladrillo, diseños de nivel y recetas de sonido |
| [`entities.py`](entities.py) | `Paddle`, `Brick`, `Ball`, `PowerUp` y `Particle`: se mueven, chocan y se dibujan |
| [`audio.py`](audio.py) | Sintetiza los efectos de sonido en memoria y los reproduce |
| [`scores.py`](scores.py) | Tabla de récords: la carga, la ordena y la guarda en disco |
| [`main.py`](main.py) | `Game`: bucle principal, estados, puntuación, vidas y reglas |

Para crear un nivel nuevo no hace falta tocar código: basta con añadir un diseño de
texto a `LEVEL_LAYOUTS` en `settings.py`. Los sonidos funcionan igual: cada uno es una
receta de tonos en `SOUND_RECIPES`.

Si el equipo no tiene tarjeta de sonido, el juego arranca igual y se juega en silencio.
Si el archivo de récords no se puede leer o escribir, la tabla dura solo esa sesión.

## Desarrollo por fases

El juego se construyó en fases y cada una está documentada en
[FASES.md](FASES.md): qué se añadió, por qué y cómo se comprobó.
