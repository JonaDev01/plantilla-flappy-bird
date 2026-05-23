"""
Capa de abstracción de GPIO (Raspberry Pi).

En escritorio (sin RPi.GPIO):  el módulo carga sin errores,
todas las llamadas retornan False / no hacen nada.

Para activar el hardware:
  1. Pon "gpio": {"enabled": true} en config/settings.json
  2. Configura los pines: "jump_pin", "signal_pin"
  3. Conecta el botón entre jump_pin y GND (pull-up interno activado)
  4. Conecta el dispositivo de señal (LED, relé, etc.) en signal_pin

Señal de salida (signal_pin):
  - Modo "score_threshold": pulsa cada <signal_score_threshold> puntos
  - Modo "game_over":       pulsa al terminar la partida
  - Modo "always":          pulsa en ambas condiciones
"""
from __future__ import annotations

import threading
import time
from typing import Any, Optional


class GPIOHandler:
    """Maneja el botón físico de salto y las señales de salida GPIO."""

    def __init__(self, config: dict) -> None:
        self._config = config
        self._gpio_cfg: dict = config.get("gpio", {})
        self.enabled: bool = self._gpio_cfg.get("enabled", False)
        self._gpio: Optional[Any] = None

        self._jump_pin: int = self._gpio_cfg.get("jump_pin", 17)
        self._signal_pin: int = self._gpio_cfg.get("signal_pin", 27)
        self._pulse_secs: float = self._gpio_cfg.get("signal_pulse_seconds", 0.2)
        self._signal_mode: str = self._gpio_cfg.get("signal_mode", "score_threshold")
        self._score_threshold: int = self._gpio_cfg.get("signal_score_threshold", 10)

        # Estado del botón (para detección de flanco)
        self._last_btn_state: bool = True   # True = no presionado (pull-up)

        if self.enabled:
            self._init_gpio()

    # ------------------------------------------------------------------ #
    # Inicialización
    # ------------------------------------------------------------------ #

    def _init_gpio(self) -> None:
        try:
            import RPi.GPIO as GPIO  # type: ignore[import]

            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self._jump_pin,   GPIO.IN,  pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self._signal_pin, GPIO.OUT, initial=GPIO.LOW)

            self._gpio = GPIO
            print(
                f"[GPIO] Inicializado — Botón: pin {self._jump_pin}  "
                f"Señal: pin {self._signal_pin}"
            )
        except ImportError:
            print("[GPIO] RPi.GPIO no disponible — GPIO desactivado.")
            self.enabled = False
        except Exception as exc:
            print(f"[GPIO] Error al inicializar: {exc} — GPIO desactivado.")
            self.enabled = False

    # ------------------------------------------------------------------ #
    # Entrada
    # ------------------------------------------------------------------ #

    def get_jump(self) -> bool:
        """
        Retorna True UNA sola vez al detectar el flanco de bajada del botón
        (HIGH → LOW = botón presionado con pull-up interno).
        """
        if not self.enabled or self._gpio is None:
            return False
        try:
            state = bool(self._gpio.input(self._jump_pin))  # True=HIGH, False=LOW
            pressed = not state                              # activo-bajo
            edge = pressed and self._last_btn_state          # flanco descendente
            self._last_btn_state = not pressed
            return edge
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Salida / Señal
    # ------------------------------------------------------------------ #

    def on_score(self, score: int) -> None:
        """Llama esto cada vez que el jugador suma un punto."""
        if not self.enabled:
            return
        if self._signal_mode in ("score_threshold", "always"):
            if score > 0 and score % self._score_threshold == 0:
                self._pulse()

    def on_game_over(self) -> None:
        """Llama esto cuando termina la partida."""
        if not self.enabled:
            return
        if self._signal_mode in ("game_over", "always"):
            self._pulse()

    # ------------------------------------------------------------------ #
    # Privados
    # ------------------------------------------------------------------ #

    def _pulse(self) -> None:
        """Activa signal_pin durante pulse_secs en un hilo separado (no bloquea)."""
        if self._gpio is None:
            return
        gpio = self._gpio
        pin = self._signal_pin
        duration = self._pulse_secs

        def _do() -> None:
            try:
                gpio.output(pin, gpio.HIGH)
                time.sleep(duration)
                gpio.output(pin, gpio.LOW)
            except Exception as exc:
                print(f"[GPIO] Error en pulso: {exc}")

        threading.Thread(target=_do, daemon=True).start()

    def cleanup(self) -> None:
        """Libera los recursos GPIO al cerrar el juego."""
        if self._gpio is not None:
            try:
                self._gpio.cleanup()
                print("[GPIO] Limpieza completada.")
            except Exception:
                pass
