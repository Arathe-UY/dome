import RPi.GPIO as GPIO
import threading
import logging

from . import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_motor_pins = config.MOTOR_PINS
_active_timers = []

def setup_motors():
    """Initializes the GPIO pins for all motors as outputs."""
    GPIO.setmode(GPIO.BCM)
    for pin in _motor_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)  # Ensure all motors are off at startup
    logging.info(f"Motors configured on pins: {_motor_pins}")

def _turn_off_motor(pin):
    """Internal function to turn off a motor."""
    try:
        GPIO.output(pin, GPIO.LOW)
    except RuntimeError:
        # Ignore errors if GPIO has already been cleaned up
        pass

def pulse(motor_index: int, duration_ms: int = config.PULSE_MS):
    """
    Activates a motor for a set duration without blocking the main thread.

    Args:
        motor_index (int): The index of the motor to activate (0-9).
        duration_ms (int): The duration of the vibration in milliseconds.
    """
    if not (0 <= motor_index < len(_motor_pins)):
        logging.warning(f"Motor index out of range: {motor_index}")
        return

    motor_pin = _motor_pins[motor_index]
    logging.info(f"Pulsing motor {motor_index + 1} (pin {motor_pin}) for {duration_ms} ms.")

    # Turn the motor on
    try:
        GPIO.output(motor_pin, GPIO.HIGH)
    except RuntimeError:
        logging.error("GPIO not configured. Cannot pulse motor.")
        return

    # Use a timer to turn the motor off after the specified duration.
    # This avoids blocking the main program loop.
    timer = threading.Timer(duration_ms / 1000.0, _turn_off_motor, args=[motor_pin])
    _active_timers.append(timer)
    timer.start()

def cleanup():
    """Cleans up the motor GPIO pins."""
    logging.info("Cleaning up motor GPIO pins.")
    
    # Cancel any pending timers
    for timer in _active_timers:
        if timer.is_alive():
            timer.cancel()
    _active_timers.clear()

    for pin in _motor_pins:
        try:
            GPIO.output(pin, GPIO.LOW)
        except RuntimeError:
            pass
