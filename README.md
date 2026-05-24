# Plantilla FlappyBird

> Motor de juego estilo Flappy Bird construido con Python + Pygame, diseñado para correr en **Raspberry Pi** con salida de señales GPIO, assets completamente intercambiables y configuración sin tocar código.

---

## Descripción

**Plantilla FlappyBird** es un clon de Flappy Bird de código abierto pensado para ser usado como base en proyectos de **maquinitas arcade** o instalaciones interactivas. Toda la lógica del juego está desacoplada de los assets: cambiar el personaje, los obstáculos, el fondo o la música es tan simple como reemplazar un archivo PNG u OGG en la carpeta correspondiente.

El proyecto integra soporte nativo para **Raspberry Pi** a través de su capa GPIO abstracta, lo que permite conectar botones físicos y enviar señales a dispositivos externos (LEDs, relés, etc.) con solo editar un archivo JSON.

---

## Características

- **Assets completamente intercambiables** — personaje, tubos, fondo, suelo y toda la música son archivos sueltos en carpetas dedicadas; sin tocar código.
- **Placeholders automáticos** — el juego corre al instante sin assets; genera gráficos proceduralmente como fallback.
- **Soporte GPIO nativo para Raspberry Pi** — botón físico de salto + pin de señal de salida configurable (activado con un flag en JSON).
- **Configuración centralizada** — resolución, velocidad, dificultad, volumen, pines GPIO, todo en `config/settings.json`.
- **Animación de personaje** — soporta uno o tres fotogramas (`bird_0.png`, `bird_1.png`, `bird_2.png`).
- **Récord local persistente** — se guarda automáticamente en `data/highscore.json`.
- **Máquina de estados** — pantalla de inicio, partida y game over con transiciones suaves.
- **Scroll parallax** — fondo lento + suelo rápido para sensación de profundidad.
- **Tests unitarios** — 15 tests que cubren configuración y sistema de puntuación.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.10+ |
| Motor gráfico | Pygame 2.x |
| GPIO (Raspberry Pi) | RPi.GPIO / gpiozero |
| Configuración | JSON |
| Tests | pytest |
| Control de versiones | Git |

---

## Estructura del proyecto

```
plantilla-flappy-bird/
├── src/
│   ├── main.py               ← Bucle principal + máquina de estados
│   ├── game/
│   │   ├── bird.py           ← Física, rotación y animación del personaje
│   │   ├── pipe_manager.py   ← Spawn, colisión y puntaje de obstáculos
│   │   ├── background.py     ← Scroll parallax (fondo + suelo)
│   │   ├── score.py          ← Puntuación y récord persistente
│   │   └── gpio_handler.py   ← Abstracción de botón y señal GPIO
│   └── utils/
│       ├── asset_loader.py   ← Carga dinámica de assets + placeholders
│       ├── config.py         ← Lector de settings.json con merge de defaults
│       └── paths.py          ← Rutas base del proyecto
├── assets/
│   ├── images/
│   │   ├── bird/             ← bird.png  (o bird_0/1/2.png para animación)
│   │   ├── pipes/            ← pipe.png
│   │   ├── background/       ← background.png
│   │   └── ground/           ← ground.png
│   └── sounds/
│       ├── music/            ← music.ogg
│       └── sfx/              ← sfx_jump.ogg  sfx_point.ogg  sfx_die.ogg
├── config/
│   └── settings.json         ← Toda la configuración del juego
├── data/
│   └── highscore.json        ← Récord local (generado automáticamente)
├── tests/
│   ├── test_score.py
│   └── test_config.py
├── run.bat                   ← Lanzador Windows
├── run.sh                    ← Lanzador Linux / Raspberry Pi
└── requirements.txt
```

---

## Instalación

### Requisitos

- Python 3.10 o superior
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/plantilla-flappy-bird.git
cd plantilla-flappy-bird

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Correr el juego
python src/main.py
```

**Windows:** también puedes hacer doble clic en `run.bat`.  
**Linux / Raspberry Pi:**

```bash
chmod +x run.sh
./run.sh
```

---

## Cómo reemplazar assets

No se necesita tocar ninguna línea de código. Solo coloca tu archivo en la carpeta correspondiente con el nombre configurado en `settings.json`:

| Asset | Carpeta | Nombre por defecto |
|---|---|---|
| Personaje (estático) | `assets/images/bird/` | `bird.png` |
| Personaje (animado) | `assets/images/bird/` | `bird_0.png`, `bird_1.png`, `bird_2.png` |
| Tubo / obstáculo | `assets/images/pipes/` | `pipe.png` |
| Fondo del nivel | `assets/images/background/` | `background.png` |
| Suelo | `assets/images/ground/` | `ground.png` |
| Música de fondo | `assets/sounds/music/` | `music.ogg` |
| Sonido de salto | `assets/sounds/sfx/` | `sfx_jump.ogg` |
| Sonido de punto | `assets/sounds/sfx/` | `sfx_point.ogg` |
| Sonido de muerte | `assets/sounds/sfx/` | `sfx_die.ogg` |

> Si quieres usar nombres distintos, cámbialos en la sección `assets` de `config/settings.json`.

---

## Configuración (`config/settings.json`)

```jsonc
{
  "display": {
    "width": 480,         // Resolución horizontal
    "height": 640,        // Resolución vertical
    "fps": 60,
    "fullscreen": false,  // true para pantalla completa (arcade)
    "show_fps": false     // true para mostrar FPS en pantalla
  },
  "game": {
    "gravity": 0.5,
    "jump_strength": -9.5,
    "pipe_speed": 3.0,    // Velocidad de los obstáculos
    "pipe_gap": 155,      // Tamaño del hueco entre tubos
    "pipe_spawn_interval": 90  // Fotogramas entre tubos
  },
  "gpio": {
    "enabled": false,          // Cambiar a true en Raspberry Pi
    "jump_pin": 17,            // Pin BCM del botón de salto
    "signal_pin": 27,          // Pin BCM de la señal de salida
    "signal_mode": "score_threshold",  // score_threshold | game_over | always
    "signal_score_threshold": 10       // Pulso cada N puntos
  },
  "audio": {
    "music_volume": 0.4,
    "sfx_volume": 0.7,
    "enabled": true
  }
}
```

---

## Controles

| Entrada | Acción |
|---|---|
| `ESPACIO` / `↑` | Saltar |
| `R` (en Game Over) | Reiniciar |
| `F11` | Alternar pantalla completa |
| `ESC` | Salir |
| Botón GPIO (Raspberry Pi) | Saltar |

---

## Raspberry Pi — Configuración GPIO

### Esquema de conexión

```
Raspberry Pi GPIO (BCM)
┌─────────────────────────┐
│  Pin 17 ──[Botón]── GND │   ← Salto (pull-up interno)
│  Pin 27 ──[LED/Relé]    │   ← Señal de salida
└─────────────────────────┘
```

### Pasos

1. Conectar el botón entre **GPIO 17** y **GND**
2. Conectar el dispositivo de señal en **GPIO 27**
3. Editar `config/settings.json`:

```json
"gpio": {
  "enabled": true,
  "jump_pin": 17,
  "signal_pin": 27
}
```

4. Instalar dependencia adicional:

```bash
pip install RPi.GPIO
```

5. Correr con `./run.sh`

> Los pines son configurables. Puedes usar cualquier pin GPIO disponible del Pi.

---

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

```
15 passed in 0.27s
```

---

## Recursos recomendados para assets

Todos los recursos listados aquí son **libres de uso** (dominio público o licencia abierta):

- **Sprites:** [OpenGameArt.org](https://opengameart.org) — busca "flappy" o "bird platformer"
- **Música:** [FreeMusicArchive.org](https://freemusicarchive.org) — filtrar por CC0
- **SFX:** [Freesound.org](https://freesound.org) — búsquedas "jump", "coin", "game over"
- **Fondos:** [Kenney.nl](https://kenney.nl/assets) — packs de juegos 2D gratuitos

> Los formatos recomendados son **PNG** (con transparencia) para imágenes y **OGG** para audio.

---

## Roadmap

- [ ] Dificultad progresiva (velocidad aumenta con los puntos)
- [ ] Tabla de puntuaciones con top 5 local
- [ ] Soporte para pantallas TFT pequeñas (SPI)
- [ ] Modo demo / atraeción para cabinas arcade
- [ ] Empaquetado como ejecutable standalone (PyInstaller)

---

## Licencia

Este proyecto se distribuye bajo la licencia **MIT**.  
Puedes usarlo, modificarlo y distribuirlo libremente, incluso en proyectos comerciales.

```
MIT License — Copyright (c) 2026
```

---

<p align="center">
  Hecho con Python + Pygame · Diseñado para Raspberry Pi
</p>
