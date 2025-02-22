# ai_strategies.py
from abc import ABC, abstractmethod
import math
import random
from constants import * # Import constants and functions
from scipy.optimize import linear_sum_assignment # Hungarian Algorithm
import numpy as np

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
    def __init__(self):
        self.last_role_assignment = {} # To track previous roles for stability

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
        cost = 0

        if role == "striker":
            # Lower cost if robot is closer to the ball and opponent goal, higher cost otherwise
            dist_to_ball_cost = distance(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])
            pos_x_normalized = robot.x / game_state["pitch_width"]
            goal_proximity_benefit =  pos_x_normalized if robot.team == "B" else (1-pos_x_normalized) # Higher x for Team B, lower for Team A is closer to goal
            cost = dist_to_ball_cost - (goal_proximity_benefit * 100) # Subtract benefit to reduce cost for good striker positions

        elif role == "supporter":
            # Moderate distance to ball, closer to striker, in open space
            dist_to_ball_cost = distance(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])
            striker = self.get_closest_teammate_with_role(robot, game, "striker")
            dist_to_striker_cost = distance(robot.x, robot.y, striker.x, striker.y) if striker else 0 # If no striker, cost is higher
            opponent_proximity_cost = self.get_closest_opponent_distance(robot, game_state) # Higher cost if near opponents

            cost = dist_to_ball_cost * 0.5 + dist_to_striker_cost + opponent_proximity_cost * 2 # Weighted costs

        elif role == "defender":
            # Closer to own goal, further from opponent goal, maybe intercept ball path
            dist_to_own_goal_cost = distance(robot.x, robot.y, game_state["own_goal_x"], game_state["own_goal_y"])
            opponent_goal_proximity_cost = distance(robot.x, robot.y, game_state["opponent_goal_x"], game_state["opponent_goal_y"])
            ball_proximity_benefit = 0 #distance(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"]) # Benefit if close to ball in own half?

            cost = dist_to_own_goal_cost * 0.8 - (opponent_goal_proximity_cost * 0.2) - (ball_proximity_benefit * 0.1) # Favor own goal proximity, penalize opponent goal proximity

        elif role == "goalkeeper":
            # Close to own goal, aligned with ball Y position
            dist_to_goal_x_cost = abs(robot.x - game_state["own_goal_x"]) # X position to goal line
            dist_to_ball_y_cost = abs(robot.y - game_state["ball_y"]) * 0.7 # Y position to ball Y (weighted less)

            cost = dist_to_goal_x_cost * 2 + dist_to_ball_y_cost # Prioritize X position, then Y alignment

        # Role Stability - Add a small penalty for changing roles (optional)
        last_role = self.last_role_assignment.get(robot.robot_id)
        if last_role == role:
            cost -= 5  # Small negative cost (benefit) for staying in the same role

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
