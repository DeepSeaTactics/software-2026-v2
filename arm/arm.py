import lgpio
import time

# PWM pulse widths in microseconds
ARM_CLOSE_WIDTH = 1600
ARM_NEUTRAL_WIDTH = 1500
ARM_OPEN_WIDTH = 1400


class Arm:
    """Create and manage robotic arm servo using lgpio on RPi 5"""

    def __init__(self, arm_signal_pin, chip_num=4):
        self.pin = arm_signal_pin
        self.chip_num = chip_num

        # Open connection to RP1 GPIO chip (gpiochip4 on Pi 5)
        try:
            self.chip = lgpio.gpiochip_open(self.chip_num)
            print(f"Connected to gpiochip{self.chip_num} via lgpio.")
        except Exception as e:
            raise RuntimeError(f"Failed to open gpiochip{self.chip_num}: {e}")

        # Claim the GPIO pin as an output
        lgpio.gpio_claim_output(self.chip, self.pin)

        # Initialize pin to neutral state at 50Hz
        self.stop()

    def close(self):
        '''Sends PWM signals to close arm'''
        print("Closing arm...")
        lgpio.tx_servo(self.chip, self.pin, ARM_CLOSE_WIDTH, 50)

    def open(self):
        '''Sends PWM signals to open arm'''
        print("Opening arm...")
        lgpio.tx_servo(self.chip, self.pin, ARM_OPEN_WIDTH, 50)

    def stop(self):
        '''Sends neutral PWM signal to hold/stop arm'''
        print("Arm neutral...")
        lgpio.tx_servo(self.chip, self.pin, ARM_NEUTRAL_WIDTH, 50)

    def cleanup(self):
        '''Releases GPIO resources and closes the gpiochip handle'''
        self.stop()
        time.sleep(0.1)
        lgpio.gpiochip_close(self.chip)
        print("Arm GPIO handle closed successfully.")


if __name__ == "__main__":
    # Specify the target signal GPIO pin
    ARM_PIN = 18

    # Instantiate the arm (defaults to gpiochip4 for RPi 5)
    armTest = Arm(arm_signal_pin=ARM_PIN)

    try:
        while True:
            armTest.open()
            time.sleep(2)

            armTest.stop()
            time.sleep(2)

            armTest.close()
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    finally:
        armTest.cleanup()
