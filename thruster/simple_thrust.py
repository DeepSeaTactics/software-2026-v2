import lgpio
import time
import numpy as np

# Inputs: [Surge, Sway, Heave, Roll, Pitch, Yaw]
# Outputs: [FL, FR, BL, BR, MFL, MFR, MBL, MBR]

# Angle factor 0.707 is 1/sqrt(2) for 45-degree vectored thrusters
S = 0.707

ESC_MAX = 1712       # Max pulse width in microseconds
ESC_MIN = 1288       # Min pulse width in microseconds
ESC_NEUTRAL = 1500   # Neutral pulse width (arming signal)
AMPERAGE_LIMIT = 22  # Max total amperage

mixer = np.array([
    [S,  S,  0,  0,  0,  1],  # FL
    [-S,  S,  0,  0,  0, -1],  # FR
    [-S, -S,  0,  0,  0,  1],  # BL
    [S, -S,  0,  0,  0, -1],  # BR
    [0,  0,  1, -1,  1,  0],  # MFL
    [0,  0,  1,  1,  1,  0],  # MFR
    # [0,  0,  1, -1, -1,  0],  # MBL
    # [0,  0,  1,  1, -1,  0]   # MBR
])

thruster_pins = [16, 17, 27, 22, 25, 26]


class Thruster:
    '''Class to control thrusters using the mixer matrix and lgpio on RPi 5'''

    def __init__(self, mixer, thruster_pins, chip_num=4):
        self.thruster_pins = thruster_pins
        self.mixer = np.array(mixer)
        self.amperage_limit_per_unit = AMPERAGE_LIMIT / len(thruster_pins)

        # Open connection to RP1 GPIO Chip (gpiochip4 on Pi 5)
        try:
            self.chip = lgpio.gpiochip_open(chip_num)
            print(f"Connected to gpiochip{chip_num} via lgpio.")
        except Exception as e:
            raise RuntimeError(f"Failed to open gpiochip{chip_num}: {e}")

        # Claim output pins and initialize ESCs to neutral (arming)
        for pin in self.thruster_pins:
            lgpio.gpio_claim_output(self.chip, pin)
            # Send 1500us neutral pulse at 50Hz for ESC arming
            lgpio.tx_servo(self.chip, pin, ESC_NEUTRAL, 50)

        time.sleep(2)  # Allow time for ESCs to arm

    def set_thruster(self, input_vector):
        '''
        input_vector: 6-element array [Surge, Sway, Heave, Roll, Pitch, Yaw], range [-1, 1]
        '''
        input_arr = np.array(input_vector)

        # Matrix multiplication to calculate thruster force vectors
        thruster_outputs = np.matmul(self.mixer, input_arr).T

        # Normalize outputs if any value exceeds absolute range of 1.0
        max_value = np.max(np.abs(thruster_outputs))
        if max_value > 1.0:
            thruster_outputs /= max_value

        # Scale outputs from [-1, 1] to microseconds range around ESC_NEUTRAL
        # e.g., 1.0 -> 1700us, -1.0 -> 1300us
        pwm_us = (thruster_outputs * 212 + ESC_NEUTRAL).astype(int)

        # Clamp values strictly between ESC boundaries
        pwm_us = np.clip(pwm_us, ESC_MIN, ESC_MAX)

        # Send updated servo signals to all connected pins
        for pin, pulse_width in zip(self.thruster_pins, pwm_us):
            lgpio.tx_servo(self.chip, pin, int(pulse_width), 50)

    def stop(self):
        '''Set all thruster pulse widths back to neutral'''
        for pin in self.thruster_pins:
            lgpio.tx_servo(self.chip, pin, ESC_NEUTRAL, 50)

    def cleanup(self):
        '''Stop signals and release gpiochip handle'''
        self.stop()
        time.sleep(0.1)
        lgpio.gpiochip_close(self.chip)
        print("GPIO chip connection closed successfully.")


if __name__ == "__main__":
    # Instantiating Thruster with mixer matrix and pin assignments
    thrustsys = Thruster(mixer, thruster_pins)

    try:
        print("Applying forward surge...")
        thrustsys.set_thruster([1, 0, 0, 0, 0, 0])
        time.sleep(5)

    finally:
        thrustsys.stop()
        thrustsys.cleanup()
        print("Thrusters stopped and cleaned up.")


'''
class ThrusterSystem:
    # Class to manage multiple thrusters with multithreading
   
    def __init__(self, mixer, thruster_pins):
    # Defines list of SingleThruster objects
        self.thrusters = [SingleThruster(mixer, pin) for pin in thruster_pins]

    def set_thrusters(self, input_vector):
    # sets all thrusters based on the input vector using multithreading for simultaneous control
        threads = []
        for thruster in self.thrusters:
            thread = Thread(target=thruster.set_thruster, args=(input_vector,))
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()  # Wait for all threads to finish

    def stop_all(self):
    # Stops all thrusters 
        for thruster in self.thrusters:
            thruster.stop()
'''
