import pygame
# from dotenv import load_dotenv
from controls.default_config import ACTION_TO_DOF
from controls.default_config import default_config
from controls.controls import Controller
from arm.arm import Arm
from thruster.simple_thrust import Thruster, mixer


# Running
clock = pygame.time.Clock()
running = True

# Object initialization
ctrls = Controller(0, default_config=default_config)
ArmObj = Arm(23)
ThrusterObj = Thruster(mixer, [16, 17, 27, 22, 25, 26])  # Use default mixer

# Binding action inputs to functions
ctrls.bind_action_to_function("Arm Open", lambda: ArmObj.open())
ctrls.bind_action_to_function("Arm Close", lambda: ArmObj.close())

# Runs the main loop
while running:
    if pygame.KEYDOWN and pygame.key == pygame.K_ESCAPE:
        running = False

    ctrls.handle_events()
    vec = ctrls.get_input_vector()
    # For testing, print the input vector to see the values being generated when keys are pressed. This should show a 6-element array corresponding to the DOFs based on the key presses.
    print(vec)
    # Send the input vector to the thruster system to update thruster outputs
    ThrusterObj.set_thruster(vec)
    clock.tick(10)  # Limit to 30 frames per second

ThrusterObj.cleanup()
ArmObj.cleanup()
pygame.quit()

'''
This chunk of code is for the Flask video stream. It does NOT work
import paramiko
import os

# Load environment variables from .env file
load_dotenv()

# start client to RPI using SSH
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Start Flask video stream on the RPI
client.connect(hostname='192.168.0.2', username=os.getenv('rpi_username'), password=os.getenv('rpi_password'))
(stdin, stdout, stderr) = client.exec_command('python3 software-2026/camera/cam.py')
stdin.close()
'''
