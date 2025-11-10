import RPi.GPIO as GPIO
import logging

from . import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_sensor_pins = config.SENSOR_PINS

def setup_sensors():
    """Initializes the GPIO pins for all sensors as inputs with pull-up resistors."""
    # The BCM mode should already be set, but we ensure it here.
    GPIO.setmode(GPIO.BCM)
    for pin in _sensor_pins:
        # We use PUD_UP because the KY-033 sensor outputs LOW when it detects an object.
        # The pull-up resistor ensures the input is HIGH when no object is detected.
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    logging.info(f"Sensors configured on pins: {_sensor_pins}")

def read_active_sensor() -> int | None:
    """
    Scans all sensors and returns the index of the first active one.

    A sensor is considered active if its pin state is LOW.

    Returns:
        int | None: The index (0-9) of the active sensor, or None if none are active.
    """
    for i, pin in enumerate(_sensor_pins):
        if GPIO.input(pin) == GPIO.LOW:
            return i  # Return the index of the first active sensor found
    return None
