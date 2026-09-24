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

## Fase 5 — Sonido y efectos visuales

**Objetivo:** que golpear algo se *sienta*. Hasta aquí el juego era mudo y nada
acusaba el impacto.

### Qué ve (y oye) el jugador

- **Nueve efectos de sonido:** lanzamiento, rebote en la paleta, rebote en pared,
  golpe seco en ladrillo duro, rotura, cápsula recogida, vida perdida, nivel
  completado y game over. **M** silencia y vuelve a activar en cualquier momento.
- **Partículas:** al romper un ladrillo saltan diez trocitos de su color, con
  gravedad, que se apagan fundiéndose con el fondo. Golpear un ladrillo duro sin
  romperlo suelta tres chispas, y perder la pelota lanza un chorro blanco desde el
  borde inferior.
- **Sacudida de pantalla:** corta y seca al romper (2,5 px), larga y fuerte al perder
  una vida (9 px). Solo tiembla la zona de juego; el marcador se queda quieto.

### Qué cambió por dentro

- **El sonido se sintetiza, no se distribuye.** No hay carpeta `assets/` ni
  dependencia nueva: `SOUND_RECIPES` describe cada efecto como una lista de tramos
  (frecuencia, barrido opcional, duración, forma de onda, volumen y caída) y el nuevo
  módulo [`audio.py`](audio.py) los convierte en WAV de 16 bits **en memoria** con
  `wave` + `io.BytesIO`, que es lo que carga pygame. Tarda 0,2 s al arrancar. Retocar
  un sonido es editar `settings.py`, no reemplazar un archivo.
- **Sin tarjeta de sonido el juego funciona igual.** `SoundBank` captura el error al
  abrir el mezclador, se queda en `enabled = False` y `play()` no hace nada. `Game`
  nunca llama a `pygame.mixer` directamente.
- **La frontera de la fase 2 aguantó.** Los rebotes contra pared y paleta ocurren
  dentro de `Ball.update()`, que no puede reproducir sonidos. En vez de dejar que la
  pelota hablara con el mezclador, su informe pasó de ser la tupla `(golpeados,
  perdida)` a un `BallReport(bricks, lost, bounces)`: la pelota dice *«he chocado con
  una pared»* y `Game` decide que eso suena. Los rebotes se agrupan en un conjunto por
  fotograma, así diez pelotas contra la pared no suenan diez veces.
- **La sacudida obliga a dibujar en dos pasos:** la zona de juego se pinta en una
  superficie aparte (`self.scene`) y se vuelca desplazada; el HUD se dibuja después
  directamente sobre la pantalla. Como ambas parten de `BG_COLOR`, la franja que
  destapa el desplazamiento no se nota.
- **`update()` pasó a tener dos niveles:** la decoración (partículas y calma de la
  sacudida) corre en todos los estados **menos en pausa**; la simulación, solo en
  `PLAYING`. Sin esa separación, una sacudida iniciada en el fotograma en que se pierde
  la última vida se quedaría temblando para siempre detrás del cartel de game over.
- `Particle` vive en `entities.py` pero es el bicho más tonto de todos: no choca con
  nada y se apaga solo. Hay un tope (`MAX_PARTICLES`) por seguridad.

### Cómo se verificó

- Las nueve recetas generan sonido real: se comprobó duración, pico de señal y que
  empiezan y acaban en cero (si no, chasquean).
- Todo nombre que `Game` pide al banco existe: una partida automática de 7 minutos
  disparó `launch`, `paddle`, `wall`, `brick`, `break`, `powerup` y `level`, y los
  sonidos de vida perdida y game over se probaron aparte.
- `BallReport` informa de pared y de paleta en los casos forzados a mano.
- La sacudida se calma sola, la más fuerte gana sobre la más débil, y —el caso que
  motivó el cambio— se calma también en game over y en nivel completado, pero **no**
  en pausa.
- Arrancando con el driver de audio roto a propósito: `enabled = False` y diez
  segundos de partida sin un solo error.
- Las pruebas de las fases 3 y 4 siguen pasando enteras.

---

## Fase 6 — Récords en disco y transiciones

**Objetivo:** que una buena partida deje huella y que pasar de nivel no sea un corte
seco. Hasta aquí el récord se perdía al cerrar la ventana.

### Qué ve el jugador

- **Tabla de los 10 mejores**, con iniciales, puntos y nivel alcanzado. Se abre desde
  el menú con **T** y se guarda entre sesiones.
- Si la partida entra en la tabla, el game over lo anuncia (*¡NUEVO RÉCORD!* o *Entras
  en la tabla: puesto N*) y pasa a una pantalla para **escribir hasta tres iniciales**
  al estilo recreativa: letras, cifras y Ñ, RETROCESO para borrar, ENTER para guardar.
  Propone las últimas iniciales usadas. Al guardar se muestra la tabla con la fila
  nueva resaltada en amarillo.
- **Terminar desde la pausa (Q) también cuenta**: si la puntuación entra, se pide el
  nombre igual.
- **Entrada de nivel:** la pantalla se funde desde negro, los ladrillos caen fila a
  fila de abajo arriba y aparece el cartel `NIVEL 3 · FORTALEZA`. La paleta ya se
  puede mover mientras tanto; al terminar suena un aviso y se puede lanzar. ESPACIO
  se la salta.
- Los carteles de nivel completado y game over **ignoran ESPACIO durante 0,6 s**, y la
  línea «ESPACIO: …» no aparece hasta que la tecla ya funciona. Quien venía
  machacando la barra para lanzar ya no se salta el cartel sin verlo.

### Qué cambió por dentro

- **Nuevo módulo [`scores.py`](scores.py)** con `ScoreTable`: carga, inserta y guarda.
  El archivo es un JSON en la carpeta de datos que da SDL
  (`pygame.system.get_pref_path()`; en Windows, `%APPDATA%\arkanoid\arkanoid\records.json`),
  no junto al código, para que funcione aunque el juego esté en una carpeta de solo
  lectura. Por eso no hace falta tocar `.gitignore`.
- **La persistencia sigue la regla del sonido: nunca tumba el juego.** Un archivo que
  falta, un JSON corrupto o entradas con tipos raros dejan la tabla vacía (o solo con
  las entradas válidas). Si no se puede escribir, `persistent` pasa a `False`, la tabla
  sigue en memoria y la pantalla de récords lo avisa.
- Se guarda escribiendo un `.tmp` y renombrándolo con `os.replace()`: un corte a mitad
  de escritura no deja el archivo a medias.
- **Los empates quedan por detrás** de quien ya tenía esa puntuación, como en los
  recreativos: `rank_for()` cuenta las entradas con puntuación `>=`.
- **`high_score` desaparece de `Game`.** El récord es `self.scores.best()`: una sola
  fuente de verdad en lugar de un número que había que acordarse de actualizar en dos
  sitios (game over y salir desde pausa).
- **Tres estados nuevos:** `LEVEL_INTRO`, `NAME_ENTRY` y `SCORES`. Todos los cambios de
  estado pasan ahora por `set_state()`, que pone a cero `state_time`. Ese único reloj
  mueve la caída de los ladrillos, el cartel que se desvanece, el cursor que parpadea
  y el retardo de los carteles, sin un temporizador por cada cosa.
- **`start_level()` deja el juego en `LEVEL_INTRO`**, así que tanto la partida nueva
  como el paso de nivel entran por la misma animación sin repetir código.
- **La caída es solo dibujo.** `Brick.draw()` acepta un `dy` que desplaza el dibujo,
  pero el `Rect` del ladrillo nunca se mueve. Las filas caen de abajo arriba para que
  ninguna atraviese a otra que ya aterrizó, y la escena se recorta a la zona de juego
  para que no asomen por detrás del marcador.
- **M no silencia mientras se escribe el nombre**: en `NAME_ENTRY` todas las teclas son
  letras y `handle_name_key()` las atiende antes que el atajo global.
- Tres sonidos nuevos en `SOUND_RECIPES`, sin tocar `audio.py`: `ready` (fin de la
  entrada), `record` (puntuación guardada) y `type` (cada letra).

### Cómo se verificó

- `ScoreTable` suelta: orden, empates detrás, tope de 10 (una puntuación igual a la
  última no entra, una más alta sí), y que al recargar el archivo se recupera la misma
  tabla y las últimas iniciales, sin `.tmp` sobrante.
- Archivos rotos: JSON inválido, una lista en vez de un objeto, `scores` que no es una
  lista y entradas mezcladas con basura → tabla vacía o solo con las válidas, sin
  excepción. Con una carpeta como ruta de guardado, y sin carpeta de datos:
  `persistent = False` y la partida sigue.
- Recorrido completo con eventos de teclado simulados: menú → entrada de nivel (la
  paleta se mueve y la pelota pegada la sigue; todas las filas han aterrizado antes de
  que acabe) → nivel completado (ESPACIO ignorado al principio) → entrada del nivel 2
  saltada con ESPACIO → game over → nombre (M escribe una M y no silencia; ENTER con el
  nombre vacío no guarda) → tabla con la fila resaltada → menú. Salir con Q en pausa
  con 0 puntos va al menú; con puntos que entran, a escribir el nombre con las
  iniciales anteriores ya propuestas.
- Capturas sin ventana de la entrada de nivel, el game over, la pantalla de nombre, la
  tabla y el menú para revisar la maqueta.
- Jugador automático durante 3 minutos pasando por las entradas y el cambio de nivel,
  sin errores.

---

## Ideas para fases siguientes

- **Fase 7 — Control y accesibilidad:** manejar la paleta con el ratón, ajustar el
  volumen desde el menú, recordar si el sonido quedó silenciado (puede ir en un archivo
  de preferencias junto al de récords).
