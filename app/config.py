from pathlib import Path

# --- Paths and Filenames ---

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Directory where audio files are stored
AUDIO_DIR = PROJECT_ROOT / "audios"

# Mapping of audio filenames by index (1 to 10)
# The system will look for these files in AUDIO_DIR
AUDIO_FILES = {i: f"audio{i}.mp3" for i in range(1, 11)}


# --- Hardware Configuration (GPIO pins in BCM mode) ---

# Output pin for the feedback LED
LED_PIN = 11

# Input pins for the KY-033 sensors
SENSOR_PINS = [
    4,   # Sensor 1
    5,   # Sensor 2
    6,   # Sensor 3
    12,  # Sensor 4
    13,  # Sensor 5
    17,  # Sensor 6
    18,  # Sensor 7
    19,  # Sensor 8
    20,  # Sensor 9
    21,  # Sensor 10
]

# Output pins for the ULN2803A driver (ERM motors)
MOTOR_PINS = [
    16,  # Motor 1
    22,  # Motor 2
    23,  # Motor 3
    24,  # Motor 4
    25,  # Motor 5
    26,  # Motor 6
    27,  # Motor 7
    8,   # Motor 8
    9,   # Motor 9
    10,  # Motor 10
]


# --- Behavior Parameters ---

# Time in seconds a sensor must be active to trigger an audio change
DWELL_SECONDS = 3.0

# Duration of the confirmation vibration pulse in milliseconds
PULSE_MS = 250

# Duration of the audio fade-in/fade-out in milliseconds
FADE_MS = 500

# Delay in the main loop in seconds (controls reactivity)
LOOP_DELAY_S = 0.05  # 50 ms, equivalent to 20 reads per second


# --- Audio Configuration (Pygame Mixer) ---

# Sample rate
MIXER_FREQUENCY = 44100

# Audio buffer size (-16 for signed 16-bit)
MIXER_SIZE = -16

# Audio channels (1=mono, 2=stereo)
MIXER_CHANNELS = 2

# Buffer size (power of 2 recommended)
MIXER_BUFFER = 2048
