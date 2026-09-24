"""Sonido del juego, sintetizado en memoria.

El repositorio no lleva archivos de audio: cada efecto se genera al arrancar a
partir de las recetas de `SOUND_RECIPES` y se convierte en un WAV en memoria
que pygame carga como cualquier otro sonido. Así no hacen falta ni assets ni
dependencias extra (numpy, por ejemplo).

Si la máquina no tiene tarjeta de sonido, `SoundBank` se queda desactivado y el
juego funciona igual, en silencio.
"""

import array
import io
import math
import wave

import pygame

from settings import (
    SOUND_SAMPLE_RATE, SOUND_BUFFER, SOUND_VOLUME, SOUND_RECIPES,
)

FADE_MS = 3   # rampa de entrada y salida para que no chasquee


def _wave_value(shape, phase):
    s = math.sin(phase)
    if shape == "square":
        return 1.0 if s >= 0 else -1.0
    if shape == "triangle":
        return 2 / math.pi * math.asin(max(-1.0, min(1.0, s)))
    return s


def _segment(ms, freq=0, to=None, shape="square", vol=1.0, decay=5.0):
    """Genera las muestras de un tramo, en el rango -1..1."""
    total = max(1, int(SOUND_SAMPLE_RATE * ms / 1000))
    fade = max(1, int(SOUND_SAMPLE_RATE * FADE_MS / 1000))
    end = freq if to is None else to
    samples = []
    phase = 0.0
    for i in range(total):
        t = i / total
        phase += 2 * math.pi * (freq + (end - freq) * t) / SOUND_SAMPLE_RATE
        value = _wave_value(shape, phase) if freq else 0.0
        envelope = math.exp(-decay * t)
        # Rampas en los extremos: un corte brusco suena como un "clic"
        envelope *= min(1.0, (i + 1) / fade, (total - i) / fade)
        samples.append(value * envelope * vol)
    return samples


def _to_sound(samples):
    """Empaqueta las muestras como WAV de 16 bits y las carga en pygame."""
    frames = array.array(
        "h", (int(max(-1.0, min(1.0, s)) * 32767) for s in samples))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SOUND_SAMPLE_RATE)
        wav.writeframes(frames.tobytes())
    buffer.seek(0)
    return pygame.mixer.Sound(file=buffer)


class SoundBank:
    """Los efectos del juego, generados una sola vez al construirse."""

    def __init__(self):
        self.muted = False
        self.sounds = {}
        self.enabled = self._start_mixer()
        if not self.enabled:
            return
        for name, recipe in SOUND_RECIPES.items():
            samples = []
            for part in recipe:
                samples.extend(_segment(**part))
            sound = _to_sound(samples)
            sound.set_volume(SOUND_VOLUME)
            self.sounds[name] = sound

    def _start_mixer(self):
        """Reinicia el mezclador en mono 16 bits, que es lo que generamos."""
        try:
            pygame.mixer.quit()
            pygame.mixer.init(SOUND_SAMPLE_RATE, -16, 1, SOUND_BUFFER)
        except pygame.error:
            return False   # sin tarjeta de sonido: se juega en silencio
        return True

    def play(self, name):
        if not self.enabled or self.muted:
            return
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    def toggle_mute(self):
        """Devuelve True si el sonido queda activado."""
        self.muted = not self.muted
        if self.muted:
            pygame.mixer.stop()
        return self.enabled and not self.muted
