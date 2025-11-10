import pygame.mixer
import logging
from pathlib import Path

from . import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_audio_paths = {}
_is_initialized = False

def init_mixer():
    """Initializes the Pygame mixer with the defined settings."""
    global _is_initialized
    try:
        pygame.mixer.init(
            frequency=config.MIXER_FREQUENCY,
            size=config.MIXER_SIZE,
            channels=config.MIXER_CHANNELS,
            buffer=config.MIXER_BUFFER
        )
        _is_initialized = True
        logging.info("Pygame mixer initialized successfully.")
    except pygame.error as e:
        logging.error(f"Could not initialize pygame.mixer: {e}")
        logging.error("Ensure the Raspberry Pi's audio system is configured (e.g., `sudo raspi-config`).")
        _is_initialized = False

def load_audio_mappings():
    """
    Scans the audio directory and maps the found files to sensors.
    Only sensors with a corresponding audio file will be active.
    """
    global _audio_paths
    _audio_paths.clear()
    
    if not config.AUDIO_DIR.is_dir():
        logging.warning(f"Audio directory does not exist: {config.AUDIO_DIR}")
        return

    for i in range(1, len(config.SENSOR_PINS) + 1):
        audio_file = config.AUDIO_DIR / config.AUDIO_FILES.get(i, "")
        if audio_file.is_file():
            _audio_paths[i - 1] = str(audio_file)  # Use 0-9 index
            logging.info(f"Audio mapped for sensor {i}: {audio_file.name}")
        else:
            logging.warning(f"Audio not found for sensor {i} (expected file: {audio_file.name})")

def get_available_audio_map():
    """Returns the dictionary of loaded audio mappings."""
    return {k + 1: Path(v).name for k, v in _audio_paths.items()}

def has_audio_for_sensor(sensor_index: int) -> bool:
    """Checks if an audio file is mapped to a specific sensor."""
    return sensor_index in _audio_paths

def play_audio(sensor_index: int, fade_in_ms: int = 0):
    """
    Plays the audio associated with a sensor, with an optional fade-in.
    """
    if not _is_initialized or not has_audio_for_sensor(sensor_index):
        return

    audio_path = _audio_paths[sensor_index]
    logging.info(f"Playing audio for sensor {sensor_index + 1}: {Path(audio_path).name}")
    try:
        pygame.mixer.music.load(audio_path)
        if fade_in_ms > 0:
            pygame.mixer.music.play(fade_ms=fade_in_ms)
        else:
            pygame.mixer.music.play()
    except pygame.error as e:
        logging.error(f"Error playing {audio_path}: {e}")

def stop_audio(fade_out_ms: int = 0):
    """Stops audio playback, with an optional fade-out."""
    if not _is_initialized:
        return

    if fade_out_ms > 0:
        pygame.mixer.music.fadeout(fade_out_ms)
        logging.info(f"Fading out audio over {fade_out_ms} ms.")
    else:
        pygame.mixer.music.stop()
        logging.info("Audio stopped.")

def is_playing() -> bool:
    """Checks if any audio is currently playing."""
    if not _is_initialized:
        return False
    return pygame.mixer.music.get_busy()
