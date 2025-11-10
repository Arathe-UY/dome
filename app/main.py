import sys
import time
import logging
import argparse
import RPi.GPIO as GPIO

from . import config, sensors, motors, audio
from .controller import DomeController
from .feedback_led import FeedbackLED

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Main entry point of the application."""
    parser = argparse.ArgumentParser(description="Control service for the Dome installation.")
    parser.add_argument(
        "--list-audios",
        action="store_true",
        help="Lists the detected audio files and their sensor mappings, then exits."
    )
    args = parser.parse_args()

    # Initialize subsystems
    audio.init_mixer()
    audio.load_audio_mappings()

    if args.list_audios:
        print("--- Detected Audio Mappings ---")
        available_map = audio.get_available_audio_map()
        if not available_map:
            print("No audio files found in the expected format (audio1.mp3, etc.).")
        else:
            for sensor_num, filename in sorted(available_map.items()):
                print(f"Sensor {sensor_num} -> {filename}")
        sys.exit(0)

    try:
        # Configure hardware
        # We set the BCM mode here once to ensure consistency.
        GPIO.setmode(GPIO.BCM)
        sensors.setup_sensors()
        motors.setup_motors() # No need to set mode again

        # Set up and start the feedback LED
        led = FeedbackLED()
        led.setup()
        led.start()

        controller = DomeController(led=led)
        logging.info("Starting main loop. Press Ctrl+C to exit.")

        while True:
            controller.update()
            time.sleep(config.LOOP_DELAY_S)

    except KeyboardInterrupt:
        logging.info("\nKeyboard interrupt detected. Exiting cleanly...")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        # Ensure resources are cleaned up
        audio.stop_audio()
        motors.cleanup()
        if 'led' in locals():
            led.stop()
        GPIO.cleanup()
        logging.info("Resources released. Goodbye.")

if __name__ == "__main__":
    main()
