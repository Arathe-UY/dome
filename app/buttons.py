import time
import logging
import RPi.GPIO as GPIO

class StartButton:
    def __init__(self, pin, long_press_duration):
        self.pin = pin
        self.long_press_duration = long_press_duration
        self._is_pressed = False
        self._press_start_time = 0.0
        self._long_press_triggered = False

    def setup(self):
        """Configures the GPIO pin for the button."""
        # Using internal pull-up resistor. 
        # Button should connect Pin -> Ground.
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        logging.info(f"Start button configured on GPIO {self.pin}")

    def check_status(self):
        """
        Checks the button state and returns an event string if applicable.
        
        Returns:
            None: No action
            'short_press': Button was pressed and released quickly
            'long_press': Button was held down for the configured duration
        """
        # Read state (LOW = Pressed because of Pull-Up)
        is_active = (GPIO.input(self.pin) == GPIO.LOW)
        current_time = time.time()
        result = None

        if is_active:
            if not self._is_pressed:
                # Edge: Just pressed
                self._is_pressed = True
                self._press_start_time = current_time
                self._long_press_triggered = False
            else:
                # State: Held down
                duration = current_time - self._press_start_time
                if duration >= self.long_press_duration and not self._long_press_triggered:
                    self._long_press_triggered = True
                    result = 'long_press'
        else:
            if self._is_pressed:
                # Edge: Just released
                self._is_pressed = False
                duration = current_time - self._press_start_time
                
                # If it wasn't a long press, it's a short press
                # (Simple debounce: ignore < 50ms presses)
                if not self._long_press_triggered and duration > 0.05:
                    result = 'short_press'
                
        return result