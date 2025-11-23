import time
import logging

from . import config, sensors, motors, audio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STATE_WAITING = 'waiting'
STATE_INTRO = 'intro'
STATE_RUNNING = 'running'

class DomeController:
    def __init__(self, led, button):
        self.led = led
        self.button = button
        self.current_sensor_index: int | None = None
        self.pending_sensor_index: int | None = None
        self.dwell_timer_start: float | None = None
        
        if config.DEBUG_SKIP_START_BUTTON:
            self.state = STATE_RUNNING
            logging.info("Debug mode: Skipping start button.")
            self.led.set_mode('pulsing')
        else:
            self.state = STATE_WAITING
            self.led.set_mode('pulsing')  # Initial state: waiting

    def _reset_to_start(self):
        """Resets the controller to the initial waiting state."""
        audio.stop_audio()
        self.current_sensor_index = None
        self.pending_sensor_index = None
        self.dwell_timer_start = None
        
        if config.DEBUG_SKIP_START_BUTTON:
            self.state = STATE_RUNNING
            self.led.set_mode('pulsing')
        else:
            self.state = STATE_WAITING
            self.led.set_mode('pulsing')

    def update(self):
        """Main method called in each iteration of the main loop."""
        
        # --- Button & State Management ---
        btn_event = self.button.check_status()
        
        if btn_event == 'long_press':
            logging.info("Long press detected: Restarting experience.")
            self._reset_to_start()
            return

        if self.state == STATE_WAITING:
            if btn_event == 'short_press':
                if audio.has_intro():
                    logging.info("Start button pressed. Playing intro.")
                    self.state = STATE_INTRO
                    audio.play_intro()
                    self.led.set_mode('on')
                else:
                    logging.warning("Start button pressed. Intro missing, skipping directly to sensors. Add a intro.mp3 file to the audios folder.")
                    self.state = STATE_RUNNING
                    self.led.set_mode('pulsing')
            return

        if self.state == STATE_INTRO:
            # Allow skipping intro with short press
            if btn_event == 'short_press':
                logging.info("Intro skipped by user.")
                audio.stop_audio(fade_out_ms=500)
                self.state = STATE_RUNNING
                self.led.set_mode('pulsing')
                return

            if not audio.is_playing():
                logging.info("Intro finished. Enabling sensors.")
                self.state = STATE_RUNNING
                self.led.set_mode('pulsing')
            return

        # --- Sensor Logic ---
        active_sensor_index = sensors.read_active_sensor()

        # Case 1: No sensor is active
        if active_sensor_index is None:
            # If we were waiting to switch to a sensor, cancel the wait.
            if self.pending_sensor_index is not None:
                logging.info(f"Canceled switch to sensor {self.pending_sensor_index + 1}.")
                self.pending_sensor_index = None
                self.dwell_timer_start = None
                
                # Restore LED state
                if self.current_sensor_index is not None:
                    self.led.set_mode('on')
                else:
                    self.led.set_mode('pulsing')
            
            # Logic to reset state only if audio has finished
            if self.current_sensor_index is not None and not audio.is_playing():
                logging.info(f"Audio finished and user left sensor {self.current_sensor_index + 1}. Resetting state.")
                self.current_sensor_index = None
                self.led.set_mode('pulsing')

            return

        # Ignore sensors that don't have an associated audio file
        if not audio.has_audio_for_sensor(active_sensor_index):
            return

        # Case 2: It's the first sensor to be activated
        if self.current_sensor_index is None:
            self._activate_new_sensor(active_sensor_index)
            return

        # Case 3: The active sensor is the same as the current one
        if active_sensor_index == self.current_sensor_index:
            # Debug: Log every 5 seconds if we are stuck on the same sensor
            if time.time() % 5 < config.LOOP_DELAY_S * 2: # Approximate check
                 logging.debug(f"Still detecting sensor {active_sensor_index + 1}")

            # If a switch was pending, cancel it because the user returned to the current sensor.
            if self.pending_sensor_index is not None:
                logging.info(f"Remained on sensor {self.current_sensor_index + 1}, canceling pending switch.")
                self.pending_sensor_index = None
                self.dwell_timer_start = None
                self.led.set_mode('on') # Restore LED to solid on
            return

        # Case 4: A different sensor is detected
        if active_sensor_index != self.current_sensor_index:
            # If we are already waiting on this sensor, check if the dwell time has passed
            if active_sensor_index == self.pending_sensor_index:
                if self.dwell_timer_start and (time.time() - self.dwell_timer_start >= config.DWELL_SECONDS):
                    logging.info(f"Confirmed switch to sensor {active_sensor_index + 1} after {config.DWELL_SECONDS}s.")
                    self._switch_to_sensor(active_sensor_index)
            else:
                # This is the first time we see this new sensor, start the timer
                logging.info(f"Sensor {active_sensor_index + 1} detected. Starting {config.DWELL_SECONDS}s timer to switch.")
                self.pending_sensor_index = active_sensor_index
                self.dwell_timer_start = time.time()
                self.led.set_mode('fast_blinking')  # Indicates that confirmation is pending

    def _activate_new_sensor(self, sensor_index: int):
        """Activates a sensor for the first time."""
        logging.info(f"Activating new sensor: {sensor_index + 1}")
        self.current_sensor_index = sensor_index
        self.led.set_mode('on')  # Solid LED while active
        motors.pulse(sensor_index)
        
        # Always play audio for new sensor activation
        audio.play_audio(sensor_index, fade_in_ms=config.FADE_MS)

    def _switch_to_sensor(self, new_sensor_index: int):
        """Performs the switch from one sensor to another after the dwell time."""
        # 1. Stop the current audio with a fade-out
        if audio.is_playing():
            audio.stop_audio(fade_out_ms=config.FADE_MS)
            # Allow time for the fade-out before starting the new audio
            time.sleep(config.FADE_MS / 1000.0)

        # 2. Update the state
        self.current_sensor_index = new_sensor_index
        self.led.set_mode('on') # The new sensor is now active
        self.pending_sensor_index = None
        self.dwell_timer_start = None

        # 3. Pulse the new motor
        motors.pulse(new_sensor_index)

        # 4. Play the new audio with a fade-in
        audio.play_audio(new_sensor_index, fade_in_ms=config.FADE_MS)
