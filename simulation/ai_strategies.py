from abc import ABC, abstractmethod
import math
import random
from scipy.optimize import linear_sum_assignment
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from constants_and_util import * # Import constants and functions

class Strategy(ABC):
    @abstractmethod
    def make_strategic_decision(self, robot, game, game_state):
        pass

class LayeredCapabilitiesStrategy(Strategy): # Renamed and Refactored Strategy
    def make_strategic_decision(self, robot, game, game_state):
        if robot.role == "striker":
            return self.striker_decision(robot, game, game_state)
        elif robot.role == "supporter":
            return self.supporter_decision(robot, game, game_state)
        elif robot.role == "defender":
            return self.defender_decision(robot, game, game_state)
        elif robot.role == "goalkeeper":
            return self.goalkeeper_decision(robot, game, game_state)
        else:
            return self.default_decision(robot, game, game_state) # Default fallback

    def striker_decision(self, robot, game, game_state):
        # Layer 1: High-level decision (Attack, Return, Defend - simplified for striker to Attack/Return)
        if game_state["ball_x"] < game_state["pitch_width"] / 4 and robot.team == "A" or game_state["ball_x"] > game_state["pitch_width"] * 3/4 and robot.team == "B": # Ball VERY deep in own half, consider returning (less frequent now) - ADJUSTED THRESHOLD
            return self.return_state(robot, game, game_state) # Or Defend() depending on desired behavior
        else:
            return self.attack_decision(robot, game, game_state) # Otherwise, Attack

    def defender_decision(self, robot, game, game_state):
        # Layer 1 for Defender: Defend or Get Ball - MORE AGGRESSIVE GET BALL
        if game_state["ball_x"] < game_state["pitch_width"] / 3 and robot.team == "A" or game_state["ball_x"] > game_state["pitch_width"] * 2/3 and robot.team == "B": # Ball close to own goal
            return self.defend_position_state(robot, game, game_state)
        else:
            return self.get_ball_state(robot, game, game_state) # More proactive in getting the ball

    def supporter_decision(self, robot, game, game_state):
        return self.support_position_state(robot, game, game_state)

    def goalkeeper_decision(self, robot, game, game_state):
        return self.goalkeeper_position_state(robot, game, game_state)

    def default_decision(self, robot, game, game_state):
        return self.get_ball_state(robot, game, game_state)

    def attack_decision(self, robot, game, game_state):
        # Layer 2: Attack Capabilities (Advance, Dribble, Kick, Pass, Get close to ball)
        dist_to_ball = game_state["distance_to_ball"]

        if dist_to_ball > ROBOT_RADIUS + BALL_RADIUS * 1.2: # SLIGHTLY REDUCED DISTANCE THRESHOLD - more eager to get close
            return self.get_close_to_ball_state(robot, game, game_state) # Layer 3 is inside GetCloseToBall state
        elif robot.dribbling:
            if not self.is_shot_blocked(robot, game_state) and distance(robot.x, robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"]) < AGGRESSIVE_SHOOT_RANGE:
                return self.kick_state(robot, game, game_state) # Layer 3: Kick (Shoot)
            elif random.random() < PASS_CHANCE: # Keep pass chance, but increase overall action
                best_pass_action = self.pass_state(robot, game, game_state) # Layer 3: Pass
                if best_pass_action["action"] == "pass_ball":
                    return best_pass_action
                else:
                    return self.dribble_state(robot, game, game_state) # Fallback to Dribble if pass fails
            else:
                return self.dribble_state(robot, game, game_state) # Layer 3: Dribble
        else:
            return self.get_ball_state(robot, game, game_state) # If not dribbling but close, try to get ball again

    def get_ball_state(self, robot, game, game_state):
        angle_to_ball = angle_between_points(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])
        dist_to_ball = distance(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])
        if dist_to_ball > ROBOT_RADIUS + BALL_RADIUS:
            return {"action": "move", "parameters": {"angle": angle_to_ball}, "state_description": "GetBall - Moving towards ball"}
        else:
            return {"action": "idle", "state_description": "GetBall - Arrived at ball"}

    def advance_state(self, robot, game, game_state):
        opponent_goal_x = game_state["opponent_goal_x"]
        opponent_goal_y = game_state["opponent_goal_y"]
        angle_to_goal = angle_between_points(robot.x, robot.y, opponent_goal_x, opponent_goal_y)
        return {"action": "move", "parameters": {"angle": angle_to_goal}, "state_description": "Advance - Moving towards goal"}

    def dribble_state(self, robot, game, game_state):
        opponent_goal_x = game_state["opponent_goal_x"]
        opponent_goal_y = game_state["opponent_goal_y"]
        angle_to_goal = angle_between_points(robot.x, robot.y, opponent_goal_x, opponent_goal_y)
        return {"action": "move", "parameters": {"angle": angle_to_goal}, "state_description": "Dribble - Moving with ball towards goal"}

    def kick_state(self, robot, game, game_state):
        return {"action": "shoot", "parameters": {}, "state_description": "Kick - Shooting the ball"} # Power parameter could be added

    def pass_state(self, robot, game, game_state):
        best_teammate = self.find_best_pass(robot, game, game_state)
        if best_teammate:
            angle_to_teammate = angle_between_points(robot.x, robot.y, best_teammate.x, best_teammate.y)
            return {"action": "pass_ball", "parameters": {"angle": angle_to_teammate, "target_teammate": best_teammate}, "state_description": "Pass - Passing to teammate"}
        else:
            return {"action": "dribble", "parameters": {}, "state_description": "Pass - No good pass, dribbling instead"} # Fallback to dribble if no pass

    def get_close_to_ball_state(self, robot, game, game_state):
        return self.follow_ball_state(robot, game, game_state) # Directly go to FollowBall - MORE AGGRESSIVE - REMOVED LOOKATBALL FOR SIMPLICITY

    def follow_ball_state(self, robot, game, game_state):
        angle_to_ball = angle_between_points(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])
        return {"action": "move", "parameters": {"angle": angle_to_ball}, "state_description": "FollowBall - Moving towards ball"}

    def return_state(self, robot, game, game_state):
        own_goal_x = game_state["own_goal_x"]
        own_goal_y = game_state["own_goal_y"]
        angle_to_goal = angle_between_points(robot.x, robot.y, own_goal_x, own_goal_y) # Return towards own goal area
        return {"action": "move", "parameters": {"angle": angle_to_goal}, "state_description": "Return - Returning towards own goal"}

    def support_position_state(self, robot, game, game_state):
        striker = None
        for team_robot in game.robots:
            if team_robot.team == robot.team and team_robot.role == "striker":
                striker = team_robot
                break

        if striker:
            support_dist = 2.5 * ROBOT_RADIUS
            support_angle_offset = math.pi / 4
            angle_to_goal = angle_between_points(striker.x, striker.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"])

            support_angle_left = angle_to_goal + support_angle_offset
            support_angle_right = angle_to_goal - support_angle_offset

            support_x_left = striker.x + support_dist * math.cos(support_angle_left)
            support_y_left = striker.y + support_dist * math.sin(support_angle_left)
            support_x_right = striker.x + support_dist * math.cos(support_angle_right)
            support_y_right = striker.y + support_dist * math.sin(support_angle_right)

            goal_x, goal_y = support_x_left, support_y_left
            return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, goal_x, goal_y)}, "state_description": "SupportPosition - Moving to support striker"}
        return {"action": "idle", "state_description": "SupportPosition - No striker to support"}

    def defend_position_state(self, robot, game, game_state):
        ball_x = game_state["ball_x"]
        ball_y = game_state["ball_y"]
        own_goal_x = game_state["own_goal_x"]
        own_goal_y = game_state["own_goal_y"]

        defend_pos_x = (ball_x + own_goal_x) / 2
        defend_pos_y = game_state["own_goal_y"]
        offset_dist = 2 * ROBOT_RADIUS
        angle_to_goal = angle_between_points(ball_x, ball_y, own_goal_x, own_goal_y)
        defend_pos_x += offset_dist * math.cos(angle_to_goal + math.pi)
        defend_pos_y += offset_dist * math.sin(angle_to_goal + math.pi)

        goal_x, goal_y = defend_pos_x, defend_pos_y
        return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, goal_x, goal_y)}, "state_description": "DefendPosition - Moving to defensive position"}

    def goalkeeper_position_state(self, robot, game, game_state):
        own_goal_x = game_state["own_goal_x"]
        own_goal_y = game_state["own_goal_y"]
        ball_y = game_state["ball_y"]

        # Goalkeeper tries to stay on the goal line, horizontally aligned with the ball
        goal_x = own_goal_x
        goal_y = max(game.GOAL_DEPTH / 2 + ROBOT_RADIUS, min(ball_y, game.PITCH_HEIGHT - (game.GOAL_DEPTH/2 + ROBOT_RADIUS))) # Clamp y to goal bounds.

        return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, goal_x, goal_y)}, "state_description": "GoalkeeperPosition - Positioning in goal"}


    def find_best_pass(self, robot, game, game_state):
        best_teammate = None
        for teammate in game.robots:
            if teammate.team == robot.team and teammate != robot:
                if not self.is_path_blocked(robot, teammate, game_state):
                    best_teammate = teammate
                    break
        return best_teammate

    def is_shot_blocked(self, robot, game_state):
        opponent_goal_x = game_state["opponent_goal_x"]
        opponent_goal_y = game_state["opponent_goal_y"]
        for opponent in game_state["opponent_robots"]:
            dist_to_opponent = self.distance_to_line(opponent["x"], opponent["y"], robot.x, robot.y, opponent_goal_x, opponent_goal_y)
            if dist_to_opponent < 2 * ROBOT_RADIUS:
                return True
        return False

    def is_path_blocked(self, robot, target, game_state):
        for opponent in game_state["opponent_robots"]:
            dist_to_opponent = self.distance_to_line(opponent["x"], opponent["y"], robot.x, robot.y, target.x, target.y)
            if dist_to_opponent < 2 * ROBOT_RADIUS:
                return True
        return False

    def distance_to_line(self, point_x, point_y, line_x1, line_y1, line_x2, line_y2):
        d = abs((line_x2 - line_x1) * (line_y1 - point_y) - (line_x1 - point_x) * (line_y2 - line_y1)) / distance(line_x1, line_y1, line_x2, line_y2)
        return d

    def find_closest_teammate_with_ball(self, robot, game):
        closest_teammate = None
        min_distance = float('inf')
        for teammate in game.robots:
            if teammate.team == robot.team and teammate != robot:
                dist_to_ball = distance(teammate.x, teammate.y, game.ball.x, game.ball.y)
                if dist_to_ball < min_distance:
                    min_distance = dist_to_ball
                    closest_teammate = teammate
        return closest_teammate

#####################################################################################
#####################################################################################

class DynamicRoleStrategy(Strategy):
    def __init__(self, dqn_agent=None): # Pass DQN agent during initialization
        self.last_role_assignment = {}
        self.dqn_agent = dqn_agent # Store DQN agent

    def make_strategic_decision(self, robot, game, game_state):
        team_robots = [r for r in game.robots if r.team == robot.team]
        roles = ["striker", "supporter", "defender", "goalkeeper"]

        # Re-assign roles periodically (e.g., every 2 seconds - adjust as needed)
        if game.game_time % 2.0 == 0: # Check game time in seconds
            self.assign_roles_hungarian(team_robots, roles, game, game_state)

        # Execute role-specific behavior (using LayeredCapabilitiesStrategy's logic for now)
        if robot.role == "striker":
            return LayeredCapabilitiesStrategy().striker_decision(robot, game, game_state) # Reuse LayeredCapabilities logic
        elif robot.role == "supporter":
            return LayeredCapabilitiesStrategy().supporter_decision(robot, game, game_state)
        elif robot.role == "defender":
            return LayeredCapabilitiesStrategy().defender_decision(robot, game, game_state)
        elif robot.role == "goalkeeper":
            return LayeredCapabilitiesStrategy().goalkeeper_decision(robot, game, game_state)
        else:
            return LayeredCapabilitiesStrategy().default_decision(robot, game, game_state)

    def assign_roles_hungarian(self, robots, roles, game, game_state):
        num_robots = len(robots)
        num_roles = len(roles)

        if num_robots != num_roles: # Basic check, adjust if you want more/fewer robots than roles
            print("Error: Number of robots must match number of roles for DynamicRoleStrategy (currently assuming 4 robots, 4 roles).")
            return

        cost_matrix = np.zeros((num_robots, num_roles))

        for i, robot in enumerate(robots):
            for j, role in enumerate(roles):
                cost_matrix[i, j] = self.calculate_role_cost(robot, role, game, game_state)

        robot_indices, role_indices = linear_sum_assignment(cost_matrix) # Hungarian Algorithm

        new_role_assignment = {}
        for robot_index, role_index in zip(robot_indices, role_indices):
            robot_id = robots[robot_index].robot_id
            assigned_role = roles[role_index]
            robots[robot_index].role = assigned_role # Assign the role to the robot
            new_role_assignment[robot_id] = assigned_role

        # Role Stability (optional - can be adjusted or removed)
        for robot in robots:
            last_role = self.last_role_assignment.get(robot.robot_id)
            if last_role and last_role != robot.role:
                print(f"Robot {robot.robot_id} role changed from {last_role} to {robot.role}")
        self.last_role_assignment = new_role_assignment # Update last assignment


    def calculate_role_cost(self, robot, role, game, game_state):
        if self.dqn_agent is None: # Fallback to original cost function if no agent provided (for testing maybe)
            cost = 0
            if role == "striker":
                dist_to_ball_cost = distance(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])
                pos_x_normalized = robot.x / game_state["pitch_width"]
                goal_proximity_benefit =  pos_x_normalized if robot.team == "B" else (1-pos_x_normalized)
                cost = dist_to_ball_cost - (goal_proximity_benefit * 100)
            elif role == "supporter":
                dist_to_ball_cost = distance(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])
                striker = self.get_closest_teammate_with_role(robot, game, "striker")
                dist_to_striker_cost = distance(robot.x, robot.y, striker.x, striker.y) if striker else 0
                opponent_proximity_cost = self.get_closest_opponent_distance(robot, game_state)
                cost = dist_to_ball_cost * 0.5 + dist_to_striker_cost + opponent_proximity_cost * 2
            elif role == "defender":
                dist_to_own_goal_cost = distance(robot.x, robot.y, game_state["own_goal_x"], game_state["own_goal_y"])
                opponent_goal_proximity_cost = distance(robot.x, robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"])
                ball_proximity_benefit = 0
                cost = dist_to_own_goal_cost * 0.8 - (opponent_goal_proximity_cost * 0.2) - (ball_proximity_benefit * 0.1)
            elif role == "goalkeeper":
                dist_to_goal_x_cost = abs(robot.x - game_state["own_goal_x"])
                dist_to_ball_y_cost = abs(robot.y - game_state["ball_y"]) * 0.7
                cost = dist_to_goal_x_cost * 2 + dist_to_ball_y_cost
            last_role = self.last_role_assignment.get(robot.robot_id)
            if last_role == role:
                cost -= 5
            return cost

        # --- Use DQN Agent to predict costs ---
        state = preprocess_state(game_state) # Preprocess game state for NN input
        roles = ["striker", "supporter", "defender", "goalkeeper"]
        role_index = roles.index(role) # Get index of the role
        input_state = np.concatenate([state.flatten(), np.array([role_index])]) # Append role index to state - ADJUST STATE REPRESENTATION IF NEEDED
        input_state = np.expand_dims(input_state, axis=0) # Add batch dimension

        q_values = self.dqn_agent.q_network.predict(input_state) # Predict Q-values from DQN
        cost = -q_values[0][role_index] # Get cost for the specific role - NEGATE Q-VALUE as Hungarian algo minimizes cost, while DQN maximizes Q-values (which represent expected rewards)

        return cost

    def get_closest_teammate_with_role(self, robot, game, target_role):
        closest_teammate = None
        min_distance = float('inf')
        for teammate in game.robots:
            if teammate.team == robot.team and teammate != robot and teammate.role == target_role:
                dist = distance(robot.x, robot.y, teammate.x, teammate.y)
                if dist < min_distance:
                    min_distance = dist
                    closest_teammate = teammate
        return closest_teammate

    def get_closest_opponent_distance(self, robot, game_state):
        min_distance = float('inf')
        for opponent in game_state["opponent_robots"]:
            dist = distance(robot.x, robot.y, opponent["x"], opponent["y"])
            min_distance = min(min_distance, dist)
        return min_distance

#####################################################################################
#####################################################################################

# SimpleGoToBallStrategy (keep this for testing/comparison)
class SimpleGoToBallStrategy(Strategy):
    def make_strategic_decision(self, robot, game, game_state):
        angle_to_ball = angle_between_points(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])
        return {"action": "move", "parameters": {"angle": angle_to_ball}, "state_description": "SimpleGoToBall - Always moving towards ball"}

#####################################################################################
#####################################################################################

class FormationPassingStrategy(Strategy):
    def __init__(self, formation_name=DEFAULT_FORMATION_RELATIVE_NAME):
        super().__init__()
        self.formation_name = formation_name
        self.formation = AVAILABLE_FORMATIONS_RELATIVE.get(formation_name, FORMATION_KITE_ATTACK_RELATIVE) # Get relative formation, default to kite
        self.formation_roles = list(self.formation.keys())
        self.last_formation_assignment = {}

        # --- Decision Tree for Forward Role ---
        self.forward_role_dtree = DecisionTreeClassifier(max_depth=3) # Example max_depth - tune this
        self.forward_role_features = ["shot_blocked", "distance_to_goal", "opponent_pressure", "pass_available"]
        self.forward_role_actions = ["shoot", "pass", "dribble"]
        training_features_forward = [ # Example training data for forward role
            [0, 500, 100, 1], [0, 200, 50, 0], [1, 300, 200, 1], [1, 400, 100, 0], [0, 300, 150, 1]
        ]
        training_labels_forward = [1, 0, 1, 2, 1]
        self.forward_role_dtree.fit(training_features_forward, training_labels_forward)

        # --- Decision Tree for Mid Role ---
        self.mid_role_dtree = DecisionTreeClassifier(max_depth=3) # Example max_depth - tune this
        self.mid_role_features = ["shot_blocked", "distance_to_goal", "opponent_pressure", "pass_to_forward_available"] # Different features for mid role
        self.mid_role_actions = ["pass_forward", "pass_mid", "shoot_mid", "dribble_mid"] # Different actions for mid role
        training_features_mid = [ # Example training data for mid role
            [0, 600, 80, 1], [0, 400, 120, 0], [1, 500, 200, 1], [1, 700, 100, 0], [0, 500, 150, 1]
        ]
        training_labels_mid = [0, 2, 0, 3, 1] # 0: pass_forward, 1: pass_mid, 2: shoot_mid, 3: dribble_mid
        self.mid_role_dtree.fit(training_features_mid, training_labels_mid)

        # --- Decision Tree for Back Role ---
        self.back_role_dtree = DecisionTreeClassifier(max_depth=3) # Example max_depth - tune this
        self.back_role_features = ["shot_blocked", "distance_to_goal", "opponent_pressure", "pass_to_mid_available"] # Different features for back role
        self.back_role_actions = ["pass_midfield", "long_shot", "defensive_clear", "dribble_back"] # Different actions for back role
        training_features_back = [ # Example training data for back role
            [0, 800, 50, 1], [0, 600, 100, 0], [1, 700, 150, 1], [1, 900, 80, 0], [0, 700, 120, 1], [1, 800, 100, 1] # Added a new data point
        ]
        training_labels_back = [0, 1, 0, 3, 1, 2] # 0: pass_midfield, 1: long_shot, 2: defensive_clear, 3: dribble_back # Corrected training labels - now includes label '2' for 'defensive_clear'
        self.back_role_dtree.fit(training_features_back, training_labels_back)

        # --- Print Decision Tree Rules (for visualization and debugging) ---
        print("\n--- Forward Role Decision Tree Rules ---\n")
        print(export_text(self.forward_role_dtree, feature_names=self.forward_role_features, class_names=self.forward_role_actions))
        print("\n--- Mid Role Decision Tree Rules ---\n")
        print(export_text(self.mid_role_dtree, feature_names=self.mid_role_features, class_names=self.mid_role_actions))
        print("\n--- Back Role Decision Tree Rules ---\n")
        print(export_text(self.back_role_dtree, feature_names=self.back_role_features, class_names=self.back_role_actions))
        print("\n--- End Decision Tree Rules ---\n")


    def make_strategic_decision(self, robot, game, game_state):
        team_robots = [r for r in game.robots if r.team == robot.team] # Get team robots list here
        self.assign_formation_roles(robot, game, game_state, team_robots) # Pass team_robots list to assign_formation_roles

        # --- Defensive Transition Logic ---
        if self.is_in_defensive_half(robot, game_state): # Check if in defensive half
            closest_robot_to_ball = game.get_closest_robot_to_ball(robot) # Helper function in FootballGame needed
            if closest_robot_to_ball == robot: # If closest to ball in defensive half, prioritize defense
                return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])}, "state_description": "FormationPass-Defender: Defensive Get Ball (Priority)"} # Get ball defensively
            else: # If not closest, move to defend formation/position (can be expanded later)
                return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, game_state["own_goal_x"], game_state["ball_y"])}, "state_description": "FormationPass-Defender: Defensive Positioning"} # Move towards own goal, intercept ball path
        # --- End Defensive Transition Logic ---

        # --- Counter-Attack and Attacking Ball Acquisition Logic ---
        elif not self.is_in_defensive_half(robot, game_state): # If NOT in defensive half (attacking or midfield)
            teammate_with_ball = self.get_teammate_with_ball(robot, game) # Helper function to find teammate with ball

            if teammate_with_ball: # If a teammate has the ball in attacking half - Counter-Attack Formation
                if robot.formation_role == "top": # "Top" role (forward) - try to get open for pass
                    return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, game_state["opponent_goal_x"], robot.y)}, "state_description": "FormationPass-Forward: Counter-Attack - Getting Open"} # Move towards opponent goal, get open on wing
                else: # Other formation roles - Support ball carrier in attack
                    return self.get_in_formation_position(robot, game, game_state, team_robots, reference_robot=teammate_with_ball) # Move to formation relative to ball carrier
            else: # No teammate has ball in attacking half - Aggressive Ball Acquisition by "top" role
                if robot.formation_role == "top": # "Top" role (forward) - prioritize getting the ball in attacking half
                    closest_robot_to_ball = game.get_closest_robot_to_ball(robot)
                    if closest_robot_to_ball == robot: # If closest, get the ball aggressively
                        return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])}, "state_description": "FormationPass-Forward: Attacking Get Ball (Priority - Aggressive)"}
                    else: # If not closest, still move towards ball in attacking area (less priority)
                        return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])}, "state_description": "FormationPass-Forward: Attacking Move to Ball (Support)"} # Move towards ball to support
        # --- End Counter-Attack and Attacking Ball Acquisition Logic ---


        if robot.formation_role == "top": # Updated role names to match kite formation
            return self.forward_role_decision(robot, game, game_state, team_robots) # Call forward role decision tree
        elif robot.formation_role == "left_mid" or robot.formation_role == "right_mid":
            return self.mid_role_decision(robot, game, game_state, team_robots) # Call mid role decision tree
        elif robot.formation_role == "bottom":
            return self.back_role_decision(robot, game, game_state, team_robots) # Call back role decision tree
        else:
            return {"action": "idle", "state_description": "FormationPass - No Formation Role"}

    def get_in_formation_position(self, robot, game, game_state, team_robots, reference_robot=None): # UPDATED signature - added reference_robot parameter with DEFAULT VALUE
        reference_robot = None
        formation_assignment = self.last_formation_assignment
        for r_id, role in formation_assignment.items():
            if role == ("top" if self.formation_name == "kite" else "forward"): # Find the reference robot again
                reference_robot_id = r_id
                break
        reference_robot = self.find_robot_in_list_by_id(team_robots, reference_robot_id) # Find robot object from ID

        if reference_robot:
            relative_offset = self.formation[robot.formation_role] # Get relative offset for robot's role
            target_x_relative = relative_offset["distance"] * math.cos(relative_offset["angle"] + reference_robot.angle) # Angle relative to robot's forward
            target_y_relative = relative_offset["distance"] * math.sin(relative_offset["angle"] + reference_robot.angle)

            ideal_goal_x_formation = reference_robot.x + target_x_relative # Calculate absolute formation spot based on reference robot
            ideal_goal_y_formation = reference_robot.y + target_y_relative

            # --- NEW - Consider Openness for Formation Position ---
            best_goal_x, best_goal_y = ideal_goal_x_formation, ideal_goal_y_formation # Default to ideal formation spot
            max_openness = -float('inf') # Initialize with minimum openness

            for angle_offset in [-math.pi/8, 0, math.pi/8]: # Check 3 angles around ideal spot - you can adjust angles/number of samples
                test_goal_x = ideal_goal_x_formation + ROBOT_RADIUS * 1.5 * math.cos(angle_offset + angle_between_points(reference_robot.x, reference_robot.y, ideal_goal_x_formation, ideal_goal_y_formation)) # Offset spot slightly
                test_goal_y = ideal_goal_y_formation + ROBOT_RADIUS * 1.5 * math.sin(angle_offset + angle_between_points(reference_robot.x, reference_robot.y, ideal_goal_x_formation, ideal_goal_y_formation))

                test_openness = self.calculate_teammate_openness({"x": test_goal_x, "y": test_goal_y}, game_state) # Calculate openness of TEST SPOT - Passing Dictionary with 'x', 'y'

                if test_openness > max_openness: # Found a more open spot
                    max_openness = test_openness
                    best_goal_x, best_goal_y = test_goal_x, test_goal_y # Update best spot

            goal_x, goal_y = best_goal_x, best_goal_y # Use the most open spot as target

            # --- End Openness Consideration ---

            return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, goal_x, goal_y)}, "state_description": f"FormationPass-{robot.formation_role}: Moving to Formation (Openness Considered)"}
        else:
            return {"action": "idle", "parameters": {}, "state_description": f"FormationPass-{robot.formation_role}: No Reference Robot"} # Cannot find reference robot

    def assign_formation_roles(self, robot, game, game_state, team_robots): # Pass team_robots list to assign_formation_roles
        formation_roles = self.formation_roles

        if len(team_robots) != len(formation_roles):
            print("Error: Number of robots in team does not match formation roles.")
            return

        # Designate reference robot (e.g., robot closest to opponent goal)
        reference_robot = None
        min_goal_distance = float('inf')
        for team_robot in team_robots:
            dist_to_goal = distance(team_robot.x, team_robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"])
            if dist_to_goal < min_goal_distance:
                min_goal_distance = dist_to_goal
                reference_robot = team_robot

        if not reference_robot: # Fallback if no robots
            reference_robot = team_robots[0] # Just pick the first one

        formation_assignment = {}
        assigned_robots = set()
        assigned_robots.add(reference_robot) # Reference robot is always assigned first

        formation_assignment[reference_robot.robot_id] = "top" if self.formation_name == "kite" else "forward" # Assign "forward" or "top" role to reference robot
        reference_role_name = "top" if self.formation_name == "kite" else "forward"

        for role_name in formation_roles:
            if role_name == reference_role_name: # Skip reference role as it's already assigned
                continue

            relative_offset = self.formation[role_name]
            target_x_relative = relative_offset["distance"] * math.cos(relative_offset["angle"] + reference_robot.angle) # Angle relative to robot's forward
            target_y_relative = relative_offset["distance"] * math.sin(relative_offset["angle"] + reference_robot.angle)

            target_x_absolute = reference_robot.x + target_x_relative # Absolute target position based on reference robot
            target_y_absolute = reference_robot.y + target_y_relative

            best_robot = None
            min_distance = float('inf')

            for team_robot in team_robots:
                if team_robot not in assigned_robots and team_robot != reference_robot: # Skip reference robot and already assigned robots
                    dist_to_spot = distance(team_robot.x, team_robot.y, target_x_absolute, target_y_absolute)
                    if dist_to_spot < min_distance:
                        min_distance = dist_to_spot
                        best_robot = team_robot

            if best_robot:
                formation_assignment[best_robot.robot_id] = role_name
                assigned_robots.add(best_robot)

        for team_robot in team_robots:
            robot_id = team_robot.robot_id
            assigned_role = formation_assignment.get(robot_id)
            team_robot.formation_role = assigned_role
            if assigned_role:
                team_robot.role = f"formation_{assigned_role}"
            else:
                team_robot.role = "formation_none"

        self.last_formation_assignment = formation_assignment

    def forward_role_decision(self, robot, game, game_state, team_robots): # ADD team_robots parameter
        # --- Decision Tree Prediction for Forward Role ---
        features = self.get_forward_role_features(robot, game, game_state) # Function to extract features
        action_index = self.forward_role_dtree.predict([features])[0] # Predict action index from decision tree
        action_name = self.forward_role_actions[action_index] # Get action name from index

        if action_name == "shoot":
             return {"action": "shoot", "parameters": {}, "state_description": "FormationPass-Forward: Decision Tree - Shooting"}
        elif action_name == "pass":
            best_pass_action = self.find_best_formation_pass(robot, game, game_state, preferred_roles=["left_mid", "right_mid", "back"]) # Pass using existing logic
            if best_pass_action:
                return best_pass_action
            else:
                return {"action": "dribble", "parameters": {}, "state_description": "FormationPass-Forward: Decision Tree - Dribbling (No Pass)"} # Fallback to dribble if no pass
        elif action_name == "dribble":
            return {"action": "dribble", "parameters": {}, "state_description": "FormationPass-Forward: Decision Tree - Dribbling"}
        else:
            return {"action": "idle", "state_description": "FormationPass-Forward: Decision Tree - Idle (Unknown Action)"} # Default idle for unknown action

    def mid_role_decision(self, robot, game, game_state, team_robots): # NEW - Decision Tree for Mid Role
        # --- Decision Tree Prediction for Mid Role ---
        features = self.get_mid_role_features(robot, game, game_state) # Function to extract features
        action_index = self.mid_role_dtree.predict([features])[0] # Predict action index from decision tree
        action_name = self.mid_role_actions[action_index] # Get action name from index

        if action_name == "pass_forward":
             best_pass_action = self.find_best_formation_pass(robot, game, game_state, preferred_roles=["forward"]) # Pass to forward if possible
             if best_pass_action:
                return best_pass_action
             else:
                return {"action": "dribble", "parameters": {}, "state_description": "FormationPass-Mid: Decision Tree - Dribble (No Forward Pass)"} # Dribble if no forward pass

        elif action_name == "pass_mid":
            best_pass_action = self.find_best_formation_pass(robot, game, game_state, preferred_roles=["left_mid", "right_mid", "back"]) # Pass to other mids/back
            if best_pass_action:
                return best_pass_action
            else:
                return {"action": "dribble", "parameters": {}, "state_description": "FormationPass-Mid: Decision Tree - Dribble (No Mid Pass)"} # Dribble if no mid pass

        elif action_name == "shoot_mid": # Mid-range shot
            return {"action": "shoot", "parameters": {}, "state_description": "FormationPass-Mid: Decision Tree - Shooting (Mid-Range)"} # Attempt mid-range shot

        elif action_name == "dribble_mid":
            return {"action": "dribble", "parameters": {}, "state_description": "FormationPass-Mid: Decision Tree - Dribbling"} # Dribble in mid-field
        else:
            return {"action": "idle", "state_description": "FormationPass-Mid: Decision Tree - Idle (Unknown Action)"} # Default idle for unknown action


    def back_role_decision(self, robot, game, game_state, team_robots): # ADD team_robots parameter
        if robot.dribbling:
            robot_pressure = self.calculate_opponent_pressure(robot, game_state) # Calculate pressure
            if robot_pressure > ROBOT_RADIUS * 1.5: # If under pressure, prioritize passing from back
                best_pass_action = self.find_best_formation_pass(robot, game, game_state, preferred_roles=["left_mid", "right_mid", "forward"]) # Prioritize pass under pressure
                if best_pass_action:
                    return best_pass_action # Pass to relieve pressure

            if not self.is_shot_blocked(robot, game_state) and distance(robot.x, robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"]) < AGGRESSIVE_SHOOT_RANGE * 2.0: # Increased long shot range for back - even more range
                if random.random() < LONG_SHOT_CHANCE * 2: # INCREASED chance for long shots from back - doubled chance
                    return {"action": "shoot", "parameters": {}, "state_description": "FormationPass-Back: Long Shot (High Chance)"} # Higher chance for long shot
                else: # If long shot chance fails, consider passing
                    best_pass_action = self.find_best_formation_pass(robot, game, game_state, preferred_roles=["left_mid", "right_mid", "forward"]) # Check for pass even if long shot chance fails
                    if best_pass_action:
                        return best_pass_action
                    else:
                        return {"action": "dribble", "parameters": {}, "state_description": "FormationPass-Back: Dribbling (No Pass, Fallback Dribble-Shot)"} # Dribble if no pass, try to create shooting chance
            else: # No clear shot (or long shot chance failed) - Default Dribble or Pass
                best_pass_action = self.find_best_formation_pass(robot, game, game_state, preferred_roles=["left_mid", "right_mid", "forward"]) # Check for pass
                if best_pass_action:
                    return best_pass_action
                else:
                    return {"action": "dribble", "parameters": {}, "state_description": "FormationPass-Back: Dribbling (No Pass/Shot, Default Dribble)"} # Default dribble if no pass or shot
        else:
            return self.get_in_formation_position(robot, game, game_state, team_robots) # Move to formation position


    def get_forward_role_features(self, robot, game, game_state): # NEW - Feature extraction for forward role
        shot_blocked = 1 if self.is_shot_blocked(robot, game_state) else 0 # Binary: 1 if blocked, 0 if not # CORRECTED - removed 'game' argument from call        dist_to_goal = distance(robot.x, robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"])
        dist_to_goal = distance(robot.x, robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"])
        opponent_pressure = self.calculate_opponent_pressure(robot, game_state)
        pass_available = 1 if self.find_best_formation_pass(robot, game, game_state, preferred_roles=["left_mid", "right_mid", "back"]) else 0 # Binary: 1 if pass available, 0 if not

        return [shot_blocked, dist_to_goal, opponent_pressure, pass_available] # Return features as list

    def get_mid_role_features(self, robot, game, game_state): # NEW - Feature extraction for Mid Role
        shot_blocked = 1 if self.is_shot_blocked(robot, game_state) else 0 # Binary: 1 if blocked, 0 if not # CORRECTED - removed 'game' argument from call        dist_to_goal = distance(robot.x, robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"])
        dist_to_goal = distance(robot.x, robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"])
        opponent_pressure = self.calculate_opponent_pressure(robot, game_state)
        pass_to_forward_available = 1 if self.find_best_formation_pass(robot, game, game_state, preferred_roles=["forward"]) else 0 # Binary: 1 if pass to forward available, 0 if not

        return [shot_blocked, dist_to_goal, opponent_pressure, pass_to_forward_available] # Return features as list

    def get_back_role_features(self, robot, game, game_state): # NEW - Feature extraction for Back Role
        shot_blocked = 1 if self.is_shot_blocked(robot, game_state) else 0 # Binary: 1 if blocked, 0 if not
        dist_to_goal = distance(robot.x, robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"]) # NEW - Define dist_to_goal - MISSING LINE
        opponent_pressure = self.calculate_opponent_pressure(robot, game_state)
        pass_to_mid_available = 1 if self.find_best_formation_pass(robot, game, game_state, preferred_roles=["left_mid", "right_mid"]) else 0 # Binary: 1 if pass to mid available, 0 if not

        return [shot_blocked, dist_to_goal, opponent_pressure, pass_to_mid_available] # Return features as list

    def find_best_formation_pass(self, robot, game, game_state, preferred_roles):
        best_teammate_pass_action = None
        best_pass_score = -1 # Initialize with a low score

        robot_pressure = self.calculate_opponent_pressure(robot, game_state) # Calculate pressure

        for preferred_role in preferred_roles:
            best_teammate = None
            for teammate in game.robots:
                if teammate.team == robot.team and teammate != robot and teammate.formation_role == preferred_role:
                    if not self.is_path_blocked(robot, game_state): # Path clear to teammate
                        teammate_openness = self.calculate_teammate_openness(teammate, game_state) # NEW - Calculate teammate openness
                        pass_distance = distance(robot.x, robot.y, teammate.x, teammate.y)
                        pass_angle_to_goal = angle_between_points(teammate.x, teammate.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"])
                        pass_forward_progress = math.cos(pass_angle_to_goal) # Closer to 0 degrees (directly towards goal) is better

                        pass_score = teammate_openness * 0.6 + pass_forward_progress * 0.05 # Re-weighted score - emphasize openness and shot potential - removed pass_distance weight

                        if robot_pressure > 2 * ROBOT_RADIUS: # Increase pass score if robot is under pressure - makes passing more urgent
                            pass_score *= 1.4 # Boost pass score if under pressure - slightly reduced boost again

                        # --- Teammate Shooting Potential - HUGE BOOST ---
                        teammate_shot_clear = not self.is_shot_blocked(teammate, game_state) # Check if teammate's shot is clear
                        if teammate_shot_clear and distance(teammate.x, teammate.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"]) < AGGRESSIVE_SHOOT_RANGE: # Check if teammate shot is clear and in range
                            pass_score *= 3.0 # Triple pass score if teammate has a clear shot! - HUGE BOOST
                        # --- End Teammate Shooting Potential ---

                        pass_score += teammate_openness * 0.2 # NEW - Add direct openness bonus to pass score - encourage passes to open teammates

                        # --- NEW - Pass Length Bonus - Encourage Longer Passes ---
                        pass_length_bonus = pass_distance / PITCH_WIDTH # Normalize pass distance by pitch width (0 to 1 bonus)
                        pass_score += pass_length_bonus * 0.2 # Add pass length bonus - 20% weight - encourage longer passes
                        # --- End Pass Length Bonus ---


                        if pass_score > best_pass_score: # Found a better pass
                            best_pass_score = pass_score
                            best_teammate_pass_action = {"action": "pass_ball", "parameters": {"angle": angle_between_points(robot.x, robot.y, teammate.x, teammate.y), "target_teammate": teammate}, "state_description": f"FormationPass-{robot.formation_role}: Passing to {preferred_role} (Score: {pass_score:.2f})"}

        return best_teammate_pass_action # Return best pass action found (if any)


    def is_shot_blocked(self, robot, game_state):
        opponent_goal_x = game_state["opponent_goal_x"]
        opponent_goal_y = game_state["opponent_goal_y"]
        for opponent in game_state["opponent_robots"]:
            dist_to_opponent = self.distance_to_line(opponent["x"], opponent["y"], robot.x, robot.y, opponent_goal_x, opponent_goal_y)
            if dist_to_opponent < 2 * ROBOT_RADIUS:
                return True
        return False

    def is_path_blocked(self, robot, target, game_state):
        for opponent in game_state["opponent_robots"]:
            dist_to_opponent = self.distance_to_line(opponent["x"], opponent["y"], robot.x, robot.y, target.x, target.y)
            if dist_to_opponent < 2 * ROBOT_RADIUS:
                return True
        return False

    def distance_to_line(self, point_x, point_y, line_x1, line_y1, line_x2, line_y2):
        d = abs((line_x2 - line_x1) * (line_y1 - point_y) - (line_x1 - point_x) * (line_y2 - line_y1)) / distance(line_x1, line_y1, line_x2, line_y2)
        return d

    def find_closest_teammate_with_ball(self, robot, game):
        closest_teammate = None
        min_distance = float('inf')
        for teammate in game.robots:
            if teammate.team == robot.team and teammate != robot:
                dist_to_ball = distance(teammate.x, teammate.y, game.ball.x, game.ball.y)
                if dist_to_ball < min_distance:
                    min_distance = dist_to_ball
                    closest_teammate = teammate
        return closest_teammate

    def find_robot_in_list_by_id(self, robot_list, robot_id_to_find): # NEW helper function - find robot in a given list
        for robot in robot_list:
            if robot.robot_id == robot_id_to_find:
                return robot
        return None # Return None if robot with given ID is not found

    def is_in_defensive_half(self, robot, game_state): # NEW helper function - check if in defensive half
        if robot.team == "A":
            return game_state["ball_x"] < game_state["pitch_width"] / 2 # Team A's defensive half is left side
        elif robot.team == "B":
            return game_state["ball_x"] > game_state["pitch_width"] / 2 # Team B's defensive half is right side
        return False # Default case - not in defensive half

    def get_teammate_with_ball(self, robot, game): # NEW helper function - check if teammate has ball
        for teammate in game.robots:
            if teammate.team == robot.team and teammate != robot and teammate.dribbling:
                return teammate # Return the teammate who is dribbling
        return None # No teammate dribbling

    def calculate_opponent_pressure(self, robot, game_state): # NEW helper function - calculate opponent pressure
        pressure = 0
        for opponent in game_state["opponent_robots"]:
            dist_to_opponent = distance(robot.x, robot.y, opponent["x"], opponent["y"])
            if dist_to_opponent < BLOCKING_DISTANCE: # Consider opponents within BLOCKING_DISTANCE as applying pressure
                pressure += (BLOCKING_DISTANCE - dist_to_opponent) # Pressure increases as opponent gets closer
        return pressure

    def calculate_teammate_openness(self, teammate, game_state): # NEW helper function - calculate teammate openness
        openness = float('inf') # Initialize with maximum openness
        teammate_x = teammate["x"] if isinstance(teammate, dict) else teammate.x # Handle both Robot object and position dictionary - NEW TYPE CHECKING LOGIC
        teammate_y = teammate["y"] if isinstance(teammate, dict) else teammate.y # Handle both Robot object and position dictionary - NEW TYPE CHECKING LOGIC

        for opponent in game_state["opponent_robots"]:
            dist_to_opponent = distance(teammate_x, teammate_y, opponent["x"], opponent["y"]) # Use teammate_x, teammate_y
            openness = min(openness, dist_to_opponent) # Openness is limited by closest opponent
        return openness