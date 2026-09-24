# Fases de desarrollo

Registro de qué se construyó en cada fase del proyecto y por qué.

---

## Fase 1 — Núcleo jugable

**Objetivo:** que la pelota rebote bien. Todo lo demás depende de esto.

- `settings.py` como única superficie de ajuste: tamaños, velocidades y colores.
  Ningún módulo hardcodea números.
- `Paddle`, `Brick` y `Ball` en `entities.py`, y el bucle `Game.run()` en `main.py`.
- **Posiciones en `float` reflejadas en `Rect`.** `pygame.Rect` solo admite enteros,
  así que la posición real vive en `Paddle.x` y `Ball.pos`, y el `Rect` se recalcula
  redondeando cada frame. Mover el `Rect` directamente perdería el movimiento
  sub-píxel y a 60 FPS se notaría como tirones.
- **Colisión separada por ejes.** La pelota avanza primero en X (resuelve paredes y
  *un* ladrillo), luego en Y (techo y *otro* ladrillo distinto). Es lo que hace que
  los golpes de esquina salgan hacia un lado con sentido en vez de atravesar el muro.
- **El ángulo de rebote depende de dónde golpea la paleta**: centro = recto,
  extremos = `MAX_BOUNCE_ANGLE`. Es el único control de puntería del jugador.
- La colisión con la paleta es de un solo sentido (solo si la pelota baja y no la ha
  rebasado), para que no se quede atrapada dentro de ella.

---

## Fase 2 — Partida: vidas, puntuación y estados

**Objetivo:** convertir el prototipo en un juego con principio y final.

- Máquina de estados `State`: `MENU / PLAYING / PAUSED / LEVEL_COMPLETE / GAME_OVER`.
  `update()` sale inmediatamente si el estado no es `PLAYING`, así que pausar o abrir
  el menú congela la simulación sin código aparte.
- Vidas (`START_LIVES`), puntuación por fila de ladrillo (`BRICK_POINTS`: las de
  arriba valen más) y récord en memoria.
- HUD superior (`PUNTOS / NIVEL / VIDAS`) con la zona de juego empezando por debajo,
  y pantallas superpuestas semitransparentes para pausa, nivel completado y game over.
- Niveles: al limpiar la pantalla se reconstruye la misma rejilla con la pelota un
  **10 % más rápida** por nivel (`SPEED_INCREASE_PER_LEVEL`). La dificultad es solo
  velocidad.
- **Frontera de responsabilidades:** `Ball.update()` *devuelve* `(golpeados, perdida)`
  en vez de tocar el marcador. Quien quita ladrillos, suma puntos y resta vidas es
  `Game`. Las entidades siguen sin saber que existe una puntuación.
- Entrada partida por intención: acciones discretas (lanzar, pausar) por eventos
  `KEYDOWN`; movimiento continuo de la paleta sondeando el teclado cada frame.
- `dt` limitado a `1/30 s` para que un tirón de la ventana no teletransporte la pelota
  al otro lado de un ladrillo.

---

## Fase 3 — Power-ups, multi-bola y efectos temporales

**Objetivo:** dar variedad a cada partida sin tocar la física de la fase 1.

### Qué ve el jugador

Al romper un ladrillo hay un **20 %** de probabilidad de que caiga una cápsula.
Si la atrapa con la paleta: **+50 puntos** y su efecto.

| Letra | Efecto | Duración |
|---|---|---|
| **E** | ANCHA — paleta ×1,6 | 12 s |
| **R** | ESTRECHA — paleta ×0,6 *(la única mala)* | 12 s |
| **L** | LENTA — pelota al 65 % de velocidad | 12 s |
| **M** | MULTI — 2 pelotas extra abriendo ±25° | permanente |
| **C** | ATRAPA — la pelota se pega al rebotar y se relanza con ESPACIO | 12 s |
| **V** | VIDA — +1 vida (máximo 5) | inmediato |

El menú lleva la leyenda de colores y, durante la partida, los efectos activos
aparecen abajo a la izquierda con los segundos que les quedan.

### Qué cambió por dentro

- **`PowerUp` en `entities.py`**, tan tonta como el resto: sabe su `kind`, cae y se
  dibuja. Lo que *significa* cada tipo vive en `Game.apply_powerup()`. Sigue el mismo
  patrón float→`Rect` de la fase 1 (`PowerUp.y` → `rect.centery`).
- **`self.ball` pasó a ser `self.balls`** (una lista). Solo se pierde una vida cuando
  la lista se vacía. Los ladrillos se eliminan *dentro* del bucle por pelota, para que
  dos pelotas del mismo frame no puntúen el mismo ladrillo dos veces.
- **`Ball.clone(ángulo)`** crea la copia de multi-bola girando la velocidad; por eso
  `Ball.__init__` ahora acepta `paddle=None`.
- **`self.effects`** es un diccionario `tipo → segundos restantes`: la única fuente de
  verdad de lo que está activo. `update_effects()` lo descuenta y `end_effect()`
  deshace lo que toque al caducar.
- **`sync_balls()`** aplica a *todas* las pelotas lo que depende de ellas (velocidad y
  pegajosidad), en lugar de tocar una sola. Así una pelota recién clonada nunca queda
  con la velocidad antigua.
- `ball_speed()` ahora incluye el factor de LENTA, y se reaplica al empezar y terminar
  un efecto — antes solo se usaba en el lanzamiento.
- Perder una vida o cambiar de nivel llama a `clear_effects()` y borra las cápsulas en
  el aire: ningún efecto sobrevive a una muerte.
- Todas las constantes nuevas (probabilidad, duración, factores, colores, letras y
  pesos del sorteo) están en `settings.py`. **Añadir un tipo nuevo** = una entrada en
  esas tablas + una rama en `apply_powerup()` + su deshacer en `end_effect()` si toca
  la paleta o las pelotas.

### Cómo se verificó

Simulación sin ventana (`SDL_VIDEODRIVER=dummy`) con un jugador automático: 600 s de
partida, 4 niveles superados, los 6 tipos de cápsula soltados y recogidos, hasta 4
pelotas simultáneas, y comprobaciones de caducidad de efectos, tope de vidas y no
duplicar puntos de un ladrillo con varias pelotas.

---

## Fase 4 — Tipos de ladrillo y diseños de nivel

**Objetivo:** que cada nivel se sienta distinto. Hasta ahora todos los niveles eran
la misma rejilla llena y lo único que cambiaba era la velocidad.

### Qué ve el jugador

Cinco diseños que se recorren en bucle, con su nombre en el marcador
(`NIVEL 3 · FORTALEZA`) y anunciado al terminar el anterior:

| Nivel | Diseño | Qué tiene |
|---|---|---|
| 1 | CLÁSICO | la rejilla llena de siempre |
| 2 | PIRÁMIDE | escalonado, con plata en la cima |
| 3 | FORTALEZA | dorados protegidos y grises en las esquinas |
| 4 | DAMERO | huecos alternos: rebotes mucho más sueltos |
| 5 | TÚNEL | dos bloques grises en el centro que hay que rodear |

Y tres clases de ladrillo nuevas:

| | Ladrillo | Golpes | Puntos |
|---|---|---|---|
| Colores | rojo → morado | 1 | 70 → 20 |
| **Plata** | gris claro | 2 | 90 |
| **Dorado** | amarillo viejo | 3 | 130 |
| **Gris** | indestructible | — | 0 |

Los ladrillos duros se van **oscureciendo** al recibir golpes y muestran un punto por
cada golpe que les queda, así se ve de un vistazo cuánto aguantan. Además ganan **+1
golpe cada 3 niveles** (hasta +2), que es la segunda vía de dificultad además de la
velocidad.

### Qué cambió por dentro

- **Los niveles son texto.** `LEVEL_LAYOUTS` guarda `(nombre, filas)` y cada carácter
  es un tipo de `BRICK_TYPES → (color, puntos, golpes)`. Hacer un nivel nuevo es
  escribir seis líneas de texto en `settings.py`, sin tocar código.
- `build_bricks(level)` deduce el número de columnas **del propio diseño**, así que un
  trazado puede tener el ancho que quiera. La única regla es que todas las filas de un
  mismo diseño midan igual.
- **`Brick` gana resistencia:** `max_hits`, `hits`, la propiedad `breakable` y
  `take_hit()`, que resta un golpe y responde si se ha roto. Sigue sin saber qué es un
  punto: quien puntúa y suelta la cápsula es `Game.hit_brick()`, y solo cuando se rompe.
- **El fin de nivel dejó de ser `not self.bricks`.** Con ladrillos indestructibles en
  pantalla esa comprobación nunca se cumpliría, así que ahora es
  `level_cleared()` → «no queda ninguno rompible». Es el cambio más fácil de olvidar
  si se añaden más tipos de ladrillo.
- Los diseños se repiten en bucle (`layout_for()`), de modo que el nivel puede subir
  sin límite aunque los trazados sean cinco.
- Desaparecen `BRICK_ROWS`, `BRICK_COLS`, `BRICK_COLORS` y `BRICK_POINTS`: ese papel lo
  hacen ahora los diseños y la tabla de tipos.

### Cómo se verificó

- Validación de los cinco diseños: filas de igual longitud, caracteres conocidos, al
  menos un ladrillo rompible, y ningún ladrillo fuera de pantalla ni pisando el HUD en
  diez niveles seguidos.
- Jugador automático hasta completar el ciclo entero de diseños: los cinco se superan
  en orden y vuelve a empezar, y los niveles con grises terminan con 4 indestructibles
  todavía en pantalla — justo lo que comprueba que `level_cleared()` funciona.
- `take_hit()` sobre un indestructible nunca lo rompe; sobre uno de plata, al segundo
  golpe sí.

---

## Ideas para fases siguientes

- **Fase 5 — Sonido y efectos visuales:** rebotes, rotura, cápsula recogida; partículas
  y sacudida de pantalla.
- **Fase 6 — Persistencia y remate:** guardar el récord en disco, tabla de mejores
  puntuaciones, transiciones entre niveles.
