import RPi.GPIO as GPIO
import threading
import time
import logging
import math

from . import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FeedbackLED:
    """Controls a feedback LED in a separate thread to prevent blocking."""

    def __init__(self, pin=config.LED_PIN):
        self._pin = pin
        self._mode = 'off'  # 'off', 'on', 'blinking', 'fast_blinking', 'pulsing'
        self._thread = None
        self._running = False
        self._pwm = None

        # Frequencies and durations for the patterns
        self.patterns = {
            'blinking': (0.5, 0.5),        # 0.5s on, 0.5s off
            'fast_blinking': (0.15, 0.15),  # 0.15s on, 0.15s off
        }

    def setup(self):
        """Sets up the GPIO pin for the LED."""
        # The BCM mode should already be set, but we ensure it here.
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._pin, GPIO.OUT)
        self._pwm = GPIO.PWM(self._pin, 100)  # PWM at 100Hz for the pulse effect
        self._pwm.start(0)  # Start with duty cycle 0 (off)
        logging.info(f"Feedback LED configured on pin {self._pin}")

    def start(self):
        """Starts the LED control thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_led_control, daemon=True)
        self._thread.start()
        logging.info("LED control thread started.")

    def stop(self):
        """Stops the control thread and cleans up resources."""
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join()
        if self._pwm:
            self._pwm.stop()
        GPIO.output(self._pin, GPIO.LOW)  # Turn off at the end
        logging.info("LED control thread stopped.")

    def set_mode(self, mode: str):
        """
        Sets the LED's operating mode.
        Valid modes: 'off', 'on', 'blinking', 'fast_blinking', 'pulsing'.
        """
        if mode in ['off', 'on', 'blinking', 'fast_blinking', 'pulsing']:
            if self._mode != mode:
                self._mode = mode
                logging.info(f"LED mode changed to: {mode}")
        else:
            logging.warning(f"Invalid LED mode: {mode}")

    def _run_led_control(self):
        """Main loop that runs in the thread to control the LED."""
        is_pwm = False
        while self._running:
            current_mode = self._mode

            if current_mode == 'pulsing':
                if not is_pwm:
                    self._pwm.start(0)
                    is_pwm = True
                # Breathing effect using a sine wave
                for i in range(360):
                    if self._mode != 'pulsing' or not self._running: break
                    # Map the sine wave from 0-1 to a 0-100 duty cycle
                    duty_cycle = (math.sin(math.radians(i)) + 1) / 2 * 100
                    self._pwm.ChangeDutyCycle(duty_cycle)
                    time.sleep(0.02)
            else:
                if is_pwm:
                    self._pwm.stop()
                    is_pwm = False
                
                if current_mode == 'on':
                    GPIO.output(self._pin, GPIO.HIGH)
                    time.sleep(0.1) # Short pause to avoid 100% CPU usage
                elif current_mode == 'off':
                    GPIO.output(self._pin, GPIO.LOW)
                    time.sleep(0.1)
                elif current_mode in self.patterns:
                    on_duration, off_duration = self.patterns[current_mode]
                    GPIO.output(self._pin, GPIO.HIGH)
                    time.sleep(on_duration)
                    if self._mode != current_mode or not self._running: continue
                    GPIO.output(self._pin, GPIO.LOW)
                    time.sleep(off_duration)
