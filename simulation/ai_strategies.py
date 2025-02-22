# ai_strategies.py
from abc import ABC, abstractmethod
import math
import random
from constants import * # Import constants and functions

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
