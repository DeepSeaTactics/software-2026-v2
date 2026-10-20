# import sdl3
# import sockets

import pygame
import copy  # for deep copying the default config to avoid mutating it when creating new Controller instances
import numpy as np
import os
try:
    from default_config import ACTION_TO_DOF
except ImportError:
    print("Default config could not be found")

# os.environ["SDL_VIDEODRIVER"] = "dummy"


class Controller:
    def __init__(self, joystick, config_file=None, default_config=None):
        # Initialize pygame and joystick
        pygame.init()
        pygame.joystick.init()
        # 1x1 pixel, basically invisible
        screen = pygame.display.set_mode((1, 1))
        pygame.display.iconify()    # immediately minimizes it
        self.action_function_map = {}  # Map actions to their corresponding functions

        # Load configuration for input bindings
        if config_file is None:
            self.config = copy.deepcopy(default_config)
        else:
            # Load config from file if provided, otherwise use default
            self.config = copy.deepcopy(config_file)

        # Establishes joystick details if available
        joystick_count = pygame.joystick.get_count()
        if joystick_count > 0:
            self.controller = pygame.joystick.Joystick(joystick)
            self.controller.init()
            num_hats = self.controller.get_numhats()
            num_axis = self.controller.get_numaxes()
            num_buttons = self.controller.get_numbuttons()
            print(
                f"Joystick Name: {self.controller.get_name()}, Number of hats: {num_hats}, Number of axes: {num_axis}, Number of buttons: {num_buttons}")
        else:
            print("No joysticks connected. Using keyboard controls.")
            print("Keyboard controls enabled.")
            self.controller = None  # Set controller to None to indicate we're using keyboard controls

    def find_action(self, input_type, input_key):
        # Search through the config for the given input type then input key to find the corresponding action
        for action, bindings in self.config.get(input_type, {}).items():
            if input_key in bindings:
                return action
        return None

    def bind_action_to_function(self, action, func):
        # Binds a function to a specific action
        # print(type(self.action_function_map))
        self.action_function_map[action] = func

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                exit()

    # polls for inputs and check if it's connected to a movement action, if yes, change zero to 1 or -1 with respect to its index

    def read_gamepad(self, vec):
        InvertedAxis = []
        for axis in range(self.controller.get_numaxes()):
            raw = float(self.controller.get_axis(axis))
            if axis in InvertedAxis:
                raw *= -1
            if abs(raw) > 0.1:  # deadzone
                direction = 1 if raw > 0 else -1
                input_key = (axis, direction)
                action = self.find_action("Controller", input_key)
                if action != None and action in ACTION_TO_DOF:
                    idx, scale = ACTION_TO_DOF[action]
                    vec[idx] += raw

        for btn in range(self.controller.get_numbuttons()):
            if self.controller.get_button(btn):
                action = self.find_action("Controller", btn)
                if action != None and action in ACTION_TO_DOF:
                    idx, scale = ACTION_TO_DOF[action]
                    vec[idx] += scale

        for hat in range(self.controller.get_numhats()):
            value = self.controller.get_hat(hat)
            for direction in [(0, 1), (0, -1), (1, 0), (-1, 0)]:  # up, down, right, left
                if value == (0, 0):
                    continue
                elif value == direction:
                    input_key = (hat, direction)
                    action = self.find_action("Controller", input_key)
                    if action != None and action in ACTION_TO_DOF:
                        idx, scale = ACTION_TO_DOF[action]
                        vec[idx] += scale

    # polls for inputs and check if it's connected to a movement action, if yes, change zero to 1 or -1 with respect to its index
    def read_keyboard(self, vec):
        pressed = pygame.key.get_pressed()

        for action, key_bindings in self.config.get("Keyboard", {}).items():
            if action not in ACTION_TO_DOF:
                continue
            idx, scale = ACTION_TO_DOF[action]

            for key_name in key_bindings:
                # Skip if the key binding is None or empty
                if not key_name:
                    continue
                try:
                    # pygame.key.key_code natively handles 'space', 'left shift', etc.
                    pygame_key = pygame.key.key_code(str(key_name))
                    if pressed[pygame_key]:
                        vec[idx] += scale
                        # +1 or -1 being added to the int in the specific vec index corresponding to the DOF
                except ValueError:
                    print(f"Warning: Invalid key name '{key_name}' in config.")
                    continue

    def get_input_vector(self):
        vec = np.zeros(6)
        if self.controller:
            self.read_gamepad(vec)
        else:
            self.read_keyboard(vec)
        return np.clip(vec, -1.0, 1.0)    # Ensure values are between -1 and 1
