# constants.py
import math
import numpy as np

ORIGINAL_PITCH_WIDTH = 300
ORIGINAL_PITCH_HEIGHT = 200
SCALE_FACTOR = 3
PITCH_WIDTH = int(ORIGINAL_PITCH_WIDTH * SCALE_FACTOR)
PITCH_HEIGHT = int(ORIGINAL_PITCH_HEIGHT * SCALE_FACTOR)
UI_WIDTH = 600
UI_HEIGHT = PITCH_HEIGHT
ROBOT_RADIUS = int(6 * SCALE_FACTOR)
BALL_RADIUS = int(2 * SCALE_FACTOR)
MOUTH_WIDTH = int(4 * SCALE_FACTOR)
MOUTH_LENGTH = int(2 * SCALE_FACTOR)
ROBOT_MAX_SPEED = 3 * SCALE_FACTOR
BALL_MAX_SPEED = 8 * SCALE_FACTOR
DT = 0.1
BALL_FRICTION = 0.03 # REDUCED BALL FRICTION - ball moves slightly faster, more dynamic
GOAL_WIDTH = int(2 * SCALE_FACTOR) # Goal width is line thickness
GOAL_LINE_LENGTH = ROBOT_RADIUS * 7.2
GOAL_DEPTH = int(2 * SCALE_FACTOR)  # WTH IS GOAL_DEPTH SIGNIFICANCE?!
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GREY = (200, 200, 200)
UI_BACKGROUND = (220, 220, 220)
TRANSPARENT_GREY = (100, 100, 100, 200)
SHOOT_CHANCE = 0.4  # INCREASED SHOOT CHANCE
PASS_CHANCE = 0.6   # SLIGHTLY REDUCED PASS CHANCE - encourage more shots, but still pass
PASS_DISTANCE = 5 * ROBOT_RADIUS
BLOCKING_DISTANCE = 4 * ROBOT_RADIUS
AGGRESSIVE_SHOOT_RANGE = 15 * ROBOT_RADIUS # INCREASED SHOOT RANGE
LONG_SHOT_CHANCE = 0.1
# Role switch probabilities
ROLE_SWITCH_PROBABILITY = 0.01
STRIKER_CHANCE = 0.4
SUPPORTER_CHANCE = 0.3
DEFENDER_CHANCE = 0.3
GOALKEEPER_CHANCE = 0.1 # New Goalkeeper Role

FORMATION_DIAMOND_ATTACK_RELATIVE = {
    "forward": {"distance": 0, "angle": 0},  # Reference point - Striker at 0 distance, 0 angle
    "left_mid": {"distance": ROBOT_RADIUS * 4, "angle": math.pi * 0.75},   # Left-mid, distance and angle offset from striker
    "right_mid": {"distance": ROBOT_RADIUS * 4, "angle": math.pi * 0.25},  # Right-mid, distance and angle offset from striker
    "back": {"distance": ROBOT_RADIUS * 6, "angle": math.pi}     # Back, behind striker
}

FORMATION_RECTANGLE_ATTACK_RELATIVE = {
    "forward_left": {"distance": ROBOT_RADIUS * 4, "angle": math.pi * 0.9}, # Top-left relative to striker
    "forward_right": {"distance": ROBOT_RADIUS * 4, "angle": math.pi * 0.1}, # Top-right relative to striker
    "back_left": {"distance": ROBOT_RADIUS * 6, "angle": math.pi * 0.9},    # Bottom-left relative to striker
    "back_right": {"distance": ROBOT_RADIUS * 6, "angle": math.pi * 0.1}    # Bottom-right relative to striker
}

FORMATION_KITE_ATTACK_RELATIVE = {
    "top": {"distance": ROBOT_RADIUS * 5, "angle": 0},       # Top point of kite - forward of striker
    "left_mid": {"distance": ROBOT_RADIUS * 4, "angle": math.pi * 0.75},   # Left-middle
    "right_mid": {"distance": ROBOT_RADIUS * 4, "angle": math.pi * 0.25},  # Right-middle
    "bottom": {"distance": ROBOT_RADIUS * 7, "angle": math.pi}      # Bottom point - behind striker
}

AVAILABLE_FORMATIONS_RELATIVE = { # Dictionary for relative formations
    "diamond": FORMATION_DIAMOND_ATTACK_RELATIVE,
    "rectangle": FORMATION_RECTANGLE_ATTACK_RELATIVE,
    "kite": FORMATION_KITE_ATTACK_RELATIVE,
}
DEFAULT_FORMATION_RELATIVE_NAME = "kite" # Default relative formation

def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def angle_between_points(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)

def preprocess_state(game_state):
    # Convert game_state dictionary to a numpy array (flattened state vector)
    state_list = []
    state_list.append(game_state["ball_x"] / game_state["pitch_width"]) # Normalize ball x
    state_list.append(game_state["ball_y"] / game_state["pitch_height"]) # Normalize ball y
    # ... Add other relevant game state features, normalize if needed ...
    for robot_info in game_state["teammates"]: # Team-mate robot positions
        state_list.append(robot_info.x / game_state["pitch_width"])
        state_list.append(robot_info.y / game_state["pitch_height"])
    for robot_info in game_state["opponent_robots"]: # Opponent robot positions
        state_list.append(robot_info["x"] / game_state["pitch_width"])
        state_list.append(robot_info["y"] / game_state["pitch_height"])

    return np.array([state_list]) # Return as numpy array, shape (1, state_size)
