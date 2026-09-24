"""Tabla de mejores puntuaciones, guardada en disco.

El archivo es un JSON pequeño en la carpeta de datos del usuario que da SDL
(`%APPDATA%` en Windows, `~/.local/share` en Linux), no junto al código: así
funciona aunque el juego esté instalado en una carpeta de solo lectura.

Igual que el sonido, la persistencia nunca puede tumbar el juego. Un archivo
que falta, está corrupto o no se puede escribir deja una tabla vacía en
memoria y la partida sigue; `persistent` indica si se está guardando de verdad.
"""

import json
import os
from collections import namedtuple

import pygame

from settings import (
    SCORES_ORG, SCORES_APP, SCORES_FILE, SCORES_TABLE_SIZE, NAME_MAX_LENGTH,
)

ScoreEntry = namedtuple("ScoreEntry", "name score level")

FILE_VERSION = 1


def default_path():
    """Ruta del archivo de récords, o None si el sistema no da carpeta de datos."""
    try:
        folder = pygame.system.get_pref_path(SCORES_ORG, SCORES_APP)
    except pygame.error:
        return None
    return os.path.join(folder, SCORES_FILE)


def _clean_entry(raw):
    """Valida una entrada leída del archivo; None si no sirve."""
    try:
        name = str(raw["name"]).strip().upper()[:NAME_MAX_LENGTH]
        score = int(raw["score"])
        level = int(raw["level"])
    except (KeyError, TypeError, ValueError):
        return None
    if not name or score <= 0 or level < 1:
        return None
    return ScoreEntry(name, score, level)


class ScoreTable:
    def __init__(self, path=None):
        self.path = default_path() if path is None else path
        self.entries = []
        self.last_name = ""        # para proponerlo en la siguiente entrada
        self.persistent = self.path is not None
        self._load()

    # ---------- Consultas ----------
    def best(self):
        return self.entries[0].score if self.entries else 0

    def rank_for(self, score):
        """Puesto (0 = primero) que ocuparía `score`, o None si no entra.

        Un empate queda por detrás de quien ya tenía esa puntuación.
        """
        if score <= 0:
            return None
        rank = sum(1 for entry in self.entries if entry.score >= score)
        return rank if rank < SCORES_TABLE_SIZE else None

    # ---------- Cambios ----------
    def add(self, name, score, level):
        """Inserta la puntuación, guarda y devuelve su puesto (o None)."""
        rank = self.rank_for(score)
        if rank is None:
            return None
        self.entries.insert(rank, ScoreEntry(name, score, level))
        del self.entries[SCORES_TABLE_SIZE:]
        self.last_name = name
        self._save()
        return rank

    # ---------- Disco ----------
    def _load(self):
        if not self.persistent or not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            raw_entries = data["scores"]
            self.last_name = str(data.get("last_name", ""))[:NAME_MAX_LENGTH]
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            # Corrupto o ilegible: se empieza de cero y se sobrescribirá al guardar
            return
        if not isinstance(raw_entries, list):
            return
        entries = [e for e in map(_clean_entry, raw_entries) if e is not None]
        # sorted() es estable: los empates conservan el orden del archivo
        entries.sort(key=lambda e: e.score, reverse=True)
        self.entries = entries[:SCORES_TABLE_SIZE]

    def _save(self):
        if not self.persistent:
            return
        data = {
            "version": FILE_VERSION,
            "last_name": self.last_name,
            "scores": [entry._asdict() for entry in self.entries],
        }
        # Se escribe en un temporal y se renombra: un corte a mitad de escritura
        # nunca deja el archivo de récords a medias
        temp = self.path + ".tmp"
        try:
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp, self.path)
        except OSError:
            self.persistent = False
