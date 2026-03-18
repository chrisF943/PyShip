"""Procedurally generated retro sound effects."""

import math
import struct
import io
import numpy as np

import pygame


class SoundFX:
    """Generates retro-styled sound effects."""

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._generate()

    def _generate(self) -> None:
        try:
            self._sounds["hit"] = self._make_hit_sound()
            self._sounds["miss"] = self._make_miss_sound()
            self._sounds["sunk"] = self._make_sunk_sound()
            self._sounds["fire"] = self._make_fire_sound()
            self._sounds["select"] = self._make_select_sound()
            self._sounds["victory"] = self._make_victory_sound()
            self._sounds["defeat"] = self._make_defeat_sound()
            self._sounds["explosion"] = self._make_explosion_sound()
        except Exception:
            pass

    def _make_wav(self, samples: np.ndarray, rate: int = 22050) -> pygame.mixer.Sound:
        samples = np.clip(samples, -1.0, 1.0)
        samples = (samples * 32767).astype(np.int16)
        buf = io.BytesIO()
        buf.write(b'RIFF')
        buf.write(struct.pack('<I', 36 + len(samples) * 2))
        buf.write(b'WAVE')
        buf.write(b'fmt ')
        buf.write(struct.pack('<I', 16))
        buf.write(struct.pack('<H', 1))
        buf.write(struct.pack('<H', 1))
        buf.write(struct.pack('<I', rate))
        buf.write(struct.pack('<I', rate * 2))
        buf.write(struct.pack('<H', 2))
        buf.write(struct.pack('<H', 16))
        buf.write(b'data')
        buf.write(struct.pack('<I', len(samples) * 2))
        buf.write(samples.tobytes())
        buf.seek(0)
        return pygame.mixer.Sound(file=buf)

    def _make_hit_sound(self) -> pygame.mixer.Sound:
        rate = 22050
        dur = 0.15
        t = np.linspace(0, dur, int(rate * dur))
        env = np.exp(-t * 30)
        sig = (np.sin(2 * np.pi * 220 * t) * 0.5 +
                np.sin(2 * np.pi * 440 * t) * 0.3 +
                np.sin(2 * np.pi * 880 * t) * 0.2)
        noise = np.random.randn(len(t)) * 0.3
        samples = (sig * env + noise * np.exp(-t * 50)) * 0.6
        return self._make_wav(samples, rate)

    def _make_miss_sound(self) -> pygame.mixer.Sound:
        rate = 22050
        dur = 0.3
        t = np.linspace(0, dur, int(rate * dur))
        env = np.exp(-t * 8)
        sig = np.sin(2 * np.pi * 80 * t) * 0.4 + np.sin(2 * np.pi * 120 * t) * 0.2
        noise = np.random.randn(len(t)) * 0.2
        samples = (sig + noise) * env * 0.5
        return self._make_wav(samples, rate)

    def _make_sunk_sound(self) -> pygame.mixer.Sound:
        rate = 22050
        dur = 0.6
        t = np.linspace(0, dur, int(rate * dur))
        env = np.exp(-t * 5)
        boom = np.sin(2 * np.pi * 40 * t) * env
        crack = np.sin(2 * np.pi * 200 * t + np.random.randn(len(t))) * env * 0.5
        noise = np.random.randn(len(t)) * np.exp(-t * 3) * 0.4
        samples = (boom + crack + noise) * 0.7
        return self._make_wav(samples, rate)

    def _make_fire_sound(self) -> pygame.mixer.Sound:
        rate = 22050
        dur = 0.25
        t = np.linspace(0, dur, int(rate * dur))
        env = np.exp(-t * 15)
        sig = (np.sin(2 * np.pi * 60 * t) * 0.6 +
                np.sin(2 * np.pi * 120 * t) * 0.3 +
                np.random.randn(len(t)) * 0.2)
        samples = sig * env * 0.8
        return self._make_wav(samples, rate)

    def _make_select_sound(self) -> pygame.mixer.Sound:
        rate = 22050
        dur = 0.05
        t = np.linspace(0, dur, int(rate * dur))
        env = np.exp(-t * 40)
        sig = np.sin(2 * np.pi * 880 * t) * env
        samples = sig * 0.3
        return self._make_wav(samples, rate)

    def _make_victory_sound(self) -> pygame.mixer.Sound:
        rate = 22050
        dur = 0.8
        t = np.linspace(0, dur, int(rate * dur))
        freqs = [523, 659, 784, 1047]
        samples = np.zeros(len(t))
        for i, f in enumerate(freqs):
            start = int(i * len(t) // len(freqs))
            end = int((i + 1) * len(t) // len(freqs))
            seg = t[start:end]
            env = np.exp(-(seg - seg[0]) * 5)
            samples[start:end] += np.sin(2 * np.pi * f * seg) * env
        samples = samples / len(freqs) * 1.5
        return self._make_wav(samples, rate)

    def _make_defeat_sound(self) -> pygame.mixer.Sound:
        rate = 22050
        dur = 0.8
        t = np.linspace(0, dur, int(rate * dur))
        freq = 300 * np.exp(-t * 2)
        sig = np.sin(2 * np.pi * freq * t)
        env = np.exp(-t * 2)
        samples = sig * env * 0.6
        return self._make_wav(samples, rate)

    def _make_explosion_sound(self) -> pygame.mixer.Sound:
        rate = 22050
        dur = 0.5
        t = np.linspace(0, dur, int(rate * dur))
        env = np.exp(-t * 4)
        noise = np.random.randn(len(t))
        for _ in range(3):
            noise = np.cumsum(noise) * 0.01
        sig = noise * 0.5 + np.sin(2 * np.pi * 50 * t) * 0.5
        samples = sig * env * 0.8
        return self._make_wav(samples, rate)

    def play(self, name: str, volume: float = 1.0) -> None:
        if name in self._sounds:
            self._sounds[name].set_volume(volume)
            self._sounds[name].play()
