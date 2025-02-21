import pygame
import math
import random
import time
from abc import ABC, abstractmethod

# Constants (Same as before)
ORIGINAL_PITCH_WIDTH = 300
ORIGINAL_PITCH_HEIGHT = 200
SCALE_FACTOR = 3
PITCH_WIDTH = int(ORIGINAL_PITCH_WIDTH * SCALE_FACTOR)
PITCH_HEIGHT = int(ORIGINAL_PITCH_HEIGHT * SCALE_FACTOR)
UI_WIDTH = 200
UI_HEIGHT = PITCH_HEIGHT
ROBOT_RADIUS = int(6 * SCALE_FACTOR)
BALL_RADIUS = int(2 * SCALE_FACTOR)
MOUTH_WIDTH = int(4 * SCALE_FACTOR)
MOUTH_LENGTH = int(2 * SCALE_FACTOR)
ROBOT_MAX_SPEED = 3 * SCALE_FACTOR
BALL_MAX_SPEED = 8 * SCALE_FACTOR
DT = 0.1
BALL_FRICTION = 0.05
GOAL_WIDTH = int(20 * SCALE_FACTOR)
GOAL_HEIGHT = int(40 * SCALE_FACTOR)
GOAL_DEPTH = int(2 * SCALE_FACTOR)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
UI_BACKGROUND = (220, 220, 220)
SHOOT_CHANCE = 0.2
PASS_CHANCE = 0.7  # Adjusted Pass Chance
PASS_DISTANCE = 5 * ROBOT_RADIUS
BLOCKING_DISTANCE = 4 * ROBOT_RADIUS
AGGRESSIVE_SHOOT_RANGE = 10 * ROBOT_RADIUS
LONG_SHOT_CHANCE = 0.1
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 30
BUTTON_X = PITCH_WIDTH - BUTTON_WIDTH - 10
BUTTON_Y = 10
BUTTON_COLOR = YELLOW
BUTTON_TEXT_COLOR = BLACK


def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def angle_between_points(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)


class Strategy(ABC):
    @abstractmethod
    def make_strategic_decision(self, robot, game, game_state):
        pass

class RoleBasedStrategy(Strategy): #New Role Based Strategy!!
    def make_strategic_decision(self, robot, game, game_state):
        if robot.role == "striker":
            return self.striker_decision(robot, game, game_state)
        elif robot.role == "supporter":
            return self.supporter_decision(robot, game, game_state)
        elif robot.role == "defender":
            return self.defender_decision(robot, game, game_state)
        else:
            return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])}}  # Default: Go to ball

    def striker_decision(self, robot, game, game_state):
        opponent_goal_x = game_state["opponent_goal_x"]
        opponent_goal_y = game_state["opponent_goal_y"]
        angle_to_goal = angle_between_points(robot.x, robot.y, opponent_goal_x, opponent_goal_y)
        dist_to_goal = distance(robot.x, robot.y, opponent_goal_x, opponent_goal_y)

        # Check for passing opportunity if blocked
        best_pass_target = self.find_best_pass(robot, game, game_state)
        if best_pass_target and self.is_shot_blocked(robot, game_state):
            return {"action": "pass", "parameters": {"target": best_pass_target}}

        # Attempt to shoot if in range and not blocked (or has clear shot)
        if dist_to_goal < AGGRESSIVE_SHOOT_RANGE or not self.is_shot_blocked(robot, game_state):
             return {"action": "shoot", "parameters": {}} #shoot
        # otherwise move!
        return {"action": "move", "parameters": {"angle": angle_to_goal}}

    def supporter_decision(self, robot, game, game_state):
        # Stay in a good passing position, support the striker.
        striker = self.find_closest_teammate_with_ball(robot, game)

        if striker:
            # Move to a position that is offset from the striker, creating a passing lane.
            offset_distance = 2 * ROBOT_RADIUS  # Distance to keep away
            angle_offset = math.pi / 4  # Offset angle (45 degrees)
            offset_x = striker.x + offset_distance * math.cos(striker.angle + angle_offset)
            offset_y = striker.y + offset_distance * math.sin(striker.angle + angle_offset)
            angle_to_position = angle_between_points(robot.x, robot.y, offset_x, offset_y)

            # If the supporter has the ball, consider passing or shooting
            if distance(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"]) < ROBOT_RADIUS + BALL_RADIUS:
                best_pass_target = self.find_best_pass(robot, game, game_state)
                if best_pass_target:
                    return {"action": "pass", "parameters": {"target": best_pass_target}}
                elif not self.is_shot_blocked(robot, game_state):
                    return {"action": "shoot", "parameters": {}}  # Shoot if a pass isn't good and the shot is clear
            return {"action": "move", "parameters": {"angle": angle_to_position}} #Otherwise move there
        return {"action": "move", "parameters": {"angle": angle_between_points(robot.x, robot.y, game_state["ball_x"], game_state["ball_y"])}}  # Go to ball if no striker


    def defender_decision(self, robot, game, game_state):
        # Stay near own goal and block shots
        own_goal_x = game_state["own_goal_x"]
        own_goal_y = game_state["own_goal_y"]

        # Position yourself between the ball and your goal
        angle_to_goal = angle_between_points(robot.x, robot.y, own_goal_x, own_goal_y)
        dist_to_goal = distance(robot.x, robot.y, own_goal_x, own_goal_y)
        ball_distance_to_goal = distance(game_state["ball_x"], game_state["ball_y"], own_goal_x, own_goal_y)

        #Defensive line, closer to goal if ball is close to goal.
        defensive_line_distance = min(ROBOT_RADIUS * 5, ball_distance_to_goal - BALL_RADIUS * 2) #Cannot be too far from goal, or in own goal.

        defensive_x = own_goal_x + defensive_line_distance * math.cos(angle_to_goal)
        defensive_y = own_goal_y + defensive_line_distance * math.sin(angle_to_goal)

        angle_to_defensive_position = angle_between_points(robot.x, robot.y, defensive_x, defensive_y)
        return {"action": "move", "parameters": {"angle": angle_to_defensive_position}} #move there

    def find_best_pass(self, robot, game, game_state):
        # Find the best teammate to pass to
        best_teammate = None
        #best_angle = None
        for teammate in game.robots:
            if teammate.team == robot.team and teammate != robot:
                #angle = angle_between_points(robot.x, robot.y, teammate.x, teammate.y)
                #Pass only to those clear of enemy robots
                if not self.is_path_blocked(robot, teammate, game_state):
                    best_teammate = teammate
                    #best_angle = angle
                    break #Return first available
        return best_teammate #Returns the best teammate


    def is_shot_blocked(self, robot, game_state):
        # Check if the shot to the opponent's goal is blocked by an opponent robot
        opponent_goal_x = game_state["opponent_goal_x"]
        opponent_goal_y = game_state["opponent_goal_y"]
        for opponent in game_state["opponent_robots"]: #Iterate opponents
            dist_to_opponent = self.distance_to_line(opponent["x"], opponent["y"], robot.x, robot.y, opponent_goal_x, opponent_goal_y)
            if dist_to_opponent < 2 * ROBOT_RADIUS:  # If an opponent is close to the line, consider the shot blocked
                return True
        return False

    def is_path_blocked(self, robot, target, game_state):
        # Check if the path to the target teammate is blocked by an opponent robot
        for opponent in game_state["opponent_robots"]:
            dist_to_opponent = self.distance_to_line(opponent["x"], opponent["y"], robot.x, robot.y, target.x, target.y)
            if dist_to_opponent < 2 * ROBOT_RADIUS:  # If an opponent is close to the line, consider the path blocked
                return True
        return False

    def distance_to_line(self, point_x, point_y, line_x1, line_y1, line_x2, line_y2):
        # Helper function to calculate the distance from a point to a line
        d = abs((line_x2 - line_x1) * (line_y1 - point_y) - (line_x1 - point_x) * (line_y2 - line_y1)) / distance(line_x1, line_y1, line_x2, line_y2)
        return d

    def find_closest_teammate_with_ball(self, robot, game):
        # Find the teammate closest to the ball
        closest_teammate = None
        min_distance = float('inf')
        for teammate in game.robots:
            if teammate.team == robot.team and teammate != robot:
                dist_to_ball = distance(teammate.x, teammate.y, game.ball.x, game.ball.y)
                if dist_to_ball < min_distance:
                    min_distance = dist_to_ball
                    closest_teammate = teammate
        return closest_teammate

class Robot:
    def __init__(self, x, y, team, color, game, strategy):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.team = team
        self.color = color
        self.dribbling = False
        self.mouth_offset = ROBOT_RADIUS + BALL_RADIUS
        self.vx = 0
        self.vy = 0
        self.game = game
        self.role = "attacker"  # Default role
        self.strategy = strategy
        self.current_action = "idle"

    def move(self, dx, dy):
        magnitude = math.sqrt(dx**2 + dy**2)
        if magnitude > 0:
            dx = (dx / magnitude) * ROBOT_MAX_SPEED * DT
            dy = (dy / magnitude) * ROBOT_MAX_SPEED * DT

        self.vx = dx
        self.vy = dy

        new_x = self.x + dx
        new_y = self.y + dy

        self.x = max(ROBOT_RADIUS, min(new_x, PITCH_WIDTH - ROBOT_RADIUS))
        self.y = max(ROBOT_RADIUS, min(new_y, PITCH_HEIGHT - ROBOT_RADIUS))

        if dx != 0 or dy != 0:
            self.angle = math.atan2(dy, dx)

    def check_collision(self, other):
        dist = distance(self.x, self.y, other.x, other.y)
        return dist <= ROBOT_RADIUS + BALL_RADIUS if isinstance(other, Ball) else dist <= 2 * ROBOT_RADIUS

    def dribble(self, ball):
        mouth_angle = self.angle
        ball_angle = math.atan2(ball.y - self.y, ball.x - self.x)
        angle_diff = (ball_angle - mouth_angle + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_diff) < math.pi / 6 and distance(self.x, self.y, ball.x, ball.y) <= ROBOT_RADIUS + BALL_RADIUS:
            self.dribbling = True
            ball.vx = 0
            ball.vy = 0
            ball.x = self.x + self.mouth_offset * math.cos(self.angle)
            ball.y = self.x + self.mouth_offset * math.sin(self.angle) #typo here
            return True
        else:
            self.dribbling = False
            return False

    def shoot(self, ball, power):
        if self.dribbling:
            self.dribbling = False
            release_speed = 1.5 * ROBOT_MAX_SPEED
            ball.vx = release_speed * math.cos(self.angle)
            ball.vy = release_speed * math.sin(self.angle)
            ball.x = self.x + (ROBOT_RADIUS + BALL_RADIUS + 1) * math.cos(self.angle)
            ball.y = self.y + (ROBOT_RADIUS + BALL_RADIUS + 1) * math.sin(self.angle)
            self.current_action = "shooting"
            return "shooting"
        self.current_action = "idle"
        return None

    def draw(self, screen):
        points = []
        for i in range(6):
            angle = self.angle + 2 * math.pi / 6 * i
            x = self.x + ROBOT_RADIUS * math.cos(angle)
            y = self.y + ROBOT_RADIUS * math.sin(angle)
            points.append((int(x), int(y)))

        pygame.draw.polygon(screen, self.color, points, 0)
        mouth_index = 0
        start_index = mouth_index
        end_index = (mouth_index + 1) % 6
        pygame.draw.line(screen, BLACK, points[start_index], points[end_index], int(3*SCALE_FACTOR))

    def get_game_state(self):
        teammates = []
        opponent_robots = []
        for team_robot in self.game.robots:
            if team_robot.team == self.team and team_robot != self:
                teammates.append(team_robot)
            if team_robot.team != self.team:
                opponent_robots.append({"x": team_robot.x, "y": team_robot.y})

        game_state = {
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
            "vx": self.vx,
            "vy": self.vy,
            "dribbling": self.dribbling,
            "team": self.team,
            "role": self.role,
            "ball_x": self.game.ball.x,
            "ball_y": self.game.ball.y,
            "ball_vx": self.game.ball.vx,
            "ball_vy": self.game.ball.vy,
            "teammates": teammates, #List of teammates
            "opponent_robots": opponent_robots,
            "own_goal_x": self.game.goal_a.x + self.game.goal_a.width / 2 if self.team == "B" else self.game.goal_b.x + self.game.goal_b.width / 2,
            "own_goal_y": self.game.goal_a.y + self.game.goal_a.height / 2 if self.team == "B" else self.game.goal_b.y + self.game.goal_b.height / 2,
            "opponent_goal_x": self.game.goal_b.x + self.game.goal_b.width / 2 if self.team == "A" else self.game.goal_a.x + self.game.goal_a.width / 2,
            "opponent_goal_y": self.game.goal_b.y + self.game.goal_b.height / 2 if self.team == "A" else self.game.goal_a.y + self.game.goal_a.height / 2,
            "pitch_width": PITCH_WIDTH,
            "pitch_height": PITCH_HEIGHT
        }
        return game_state

    def make_strategic_decision(self):
        game_state = self.get_game_state()
        action = self.strategy.make_strategic_decision(self, self.game, game_state)
        if action is None:
            return

        if self.dribbling:
            if isinstance(action, dict) and "action" in action:  #Check that action is DICT and key "action" is in action, otherwise it's none!
                if action["action"] == "move":
                    self.current_action = "moving"
                    self.move(math.cos(action["parameters"]["angle"]), math.sin(action["parameters"]["angle"]))
                elif action["action"] == "shoot":
                    state = self.shoot(self.game.ball, 10 * SCALE_FACTOR)
                    if state:
                        self.current_action = "shooting"
                elif action["action"] == "pass":
                    target = action["parameters"]["target"]
                    if target: # Check there IS a target to pass to.
                        angle = angle_between_points(self.x, self.y, target.x, target.y)
                        self.angle = angle
                        state = self.shoot(self.game.ball, 5 * SCALE_FACTOR)
                        if state:
                            self.current_action = "passing"
                    else:
                        self.current_action = "no pass target"
                else:
                    self.current_action = "idle" # If no action, do nothing

        else:
            if isinstance(action, dict) and "action" in action: # Check if action is DICT and key "action" is in action, otherwise it's none!
                if action["action"] == "move":
                    if "parameters" in action:  # Check if parameters exist
                        self.move(math.cos(action["parameters"]["angle"]), math.sin(action["parameters"]["angle"]))
                        self.current_action = "moving"
                        return self.current_action
                else:
                    self.current_action = "idle" #If anything else like "shoot", set it as IDLE as it's doing nothing!

            # Go for ball if no specific action is given.
            angle_to_ball = math.atan2(self.game.ball.y - self.y, self.game.ball.x - self.x)
            dist_to_ball = distance(self.x, self.y, self.game.ball.x, self.game.ball.y)
            if dist_to_ball > ROBOT_RADIUS + BALL_RADIUS:  # Is far from ball
                self.move(math.cos(angle_to_ball), math.sin(angle_to_ball))  # Head to ball
            self.current_action = "heading to ball"

        return self.current_action

class Ball: #unchanged
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0

    def move(self):
        #Apply ball friction - deceleration
        self.vx -= BALL_FRICTION * self.vx * DT
        self.vy -= BALL_FRICTION * self.vy * DT

        #If extremely small speed, force set to 0
        if abs(self.vx) < 0.1:
            self.vx = 0
        if abs(self.vy) < 0.1:
            self.vy = 0

        self.x += self.vx * DT
        self.y += self.vy * DT

        # Boundary collisions (elastic)
        if self.x - BALL_RADIUS < 0:
            self.x = BALL_RADIUS
            self.vx *= -1
        if self.x + BALL_RADIUS > PITCH_WIDTH:
            self.x = PITCH_WIDTH - BALL_RADIUS
            self.vx *= -1
        if self.y - BALL_RADIUS < 0:
            self.y = BALL_RADIUS
            self.vy *= -1
        if self.y + BALL_RADIUS > PITCH_HEIGHT:
            self.y = PITCH_HEIGHT - BALL_RADIUS
            self.vy *= -1

    def check_collision(self, other):
        dist = distance(self.x, self.y, other.x, other.y)
        return dist <= ROBOT_RADIUS + BALL_RADIUS

    def draw(self, screen):
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), BALL_RADIUS)

class GoalNet: #unchanged
    def __init__(self, x, y, team):
        self.x = x  # Top-left x-coordinate
        self.y = y  # Top-left y-coordinate
        self.width = GOAL_WIDTH
        self.height = GOAL_HEIGHT
        self.team = team

    def check_collision(self, ball):
        # Simplified AABB (Axis-Aligned Bounding Box) collision check.  More accurate collision might be needed.
        if self.x <= ball.x <= self.x + self.width and self.y <= ball.y <= self.y + self.height:
            return True
        return False

    def draw(self, screen):
        # Draw the goalnet as a rectangle
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height), GOAL_DEPTH)  # White outline

class FootballGame: #Main game loop
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((PITCH_WIDTH + UI_WIDTH, PITCH_HEIGHT))
        pygame.display.set_caption("Robot Football")
        self.clock = pygame.time.Clock()

        # Define available strategies
        self.strategies = {
            "RoleBased": RoleBasedStrategy() #Now only role based strategy!
        }

        # Assign initial strategies to teams
        self.team_strategies = {
            "A": "RoleBased",
            "B": "RoleBased"
        }

        # Initialize robots (three teams)
        self.robots = [
            Robot(0, 0, "A", RED, self, self.strategies[self.team_strategies["A"]]),
            Robot(0, 0, "A", RED, self, self.strategies[self.team_strategies["A"]]),
            Robot(0, 0, "A", RED, self, self.strategies[self.team_strategies["A"]]),
            Robot(0, 0, "B", BLUE, self, self.strategies[self.team_strategies["B"]]),
            Robot(0, 0, "B", BLUE, self, self.strategies[self.team_strategies["B"]]),
            Robot(0, 0, "B", BLUE, self, self.strategies[self.team_strategies["B"]]),
        ]

        #Assign Roles
        self.assign_roles()

        #Team A's default
        for robot in self.robots:
            if robot.team == "A":
                robot.color = RED

        #Team B's default
        for robot in self.robots:
            if robot.team == "B":
                robot.color = BLUE

        #A note about which team does what - for the user.
        print ("Both teams are now role-based. Roles are: Striker, Supporter, Defender.")

        self.ball = Ball(PITCH_WIDTH // 2, PITCH_HEIGHT // 2)
        self.ball.vx = 0
        self.ball.vy = 0  # Ball starts with zero velocity

        # Initialize goalnets at opposite ends of the pitch
        self.goal_a = GoalNet(0, PITCH_HEIGHT // 2 - GOAL_HEIGHT // 2, "A")  # Team A's goal
        self.goal_b = GoalNet(PITCH_WIDTH - GOAL_WIDTH, PITCH_HEIGHT // 2 - GOAL_HEIGHT // 2, "B")  # Team B's goal
        self.goals = [self.goal_a, self.goal_b]

        self.game_over = False
        self.winning_team = None
        self.paused = False  # For pausing and repositioning the ball
        self.manual_intervention = False #For button state

        #Setup the button to be able to reposition ball - text in the button.
        self.button_rect = pygame.Rect(BUTTON_X, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.font = pygame.font.Font(None, int(24 * SCALE_FACTOR))
        self.button_text = self.font.render("Place Ball", True, BUTTON_TEXT_COLOR)
        self.button_text_rect = self.button_text.get_rect(center=self.button_rect.center)

        self.font_action = pygame.font.Font(None, int(20 * SCALE_FACTOR)) #Font for robot action.
        self.setup_initial_positions()

    def assign_roles(self):
        #Assign roles to robots
        for team in ["A", "B"]:
            team_robots = [robot for robot in self.robots if robot.team == team]
            random.shuffle(team_robots)  #Randomize the list

            #Assign 1 striker, 1 supporter, 1 defender (Can change as needed)
            team_robots[0].role = "striker"
            team_robots[1].role = "supporter"
            team_robots[2].role = "defender"

    def change_strategy(self, team, strategy_name): #Removed, not needed
        pass


    def setup_initial_positions(self):
        font = pygame.font.Font(None, int(30 * SCALE_FACTOR))
        robot_index = 0
        while robot_index < len(self.robots):
            self.screen.fill(GREEN)
            text = font.render(f"Place Robot {robot_index + 1} (Team {self.robots[robot_index].team}, Role: {self.robots[robot_index].role}). Click to place.", True, WHITE)
            text_rect = text.get_rect(center=(PITCH_WIDTH // 2, PITCH_HEIGHT // 4))  # Position text higher
            self.screen.blit(text, text_rect)
            pygame.display.flip()

            placing = True
            while placing:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()  # Exit the program
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        # Ensure robot is placed within bounds
                        if ROBOT_RADIUS <= x <= PITCH_WIDTH - ROBOT_RADIUS and ROBOT_RADIUS <= y <= PITCH_HEIGHT - ROBOT_RADIUS:
                            self.robots[robot_index].x = x
                            self.robots[robot_index].y = y
                            placing = False
                            break
                        else:
                            print("Invalid position. Place within the pitch boundaries.")
            robot_index += 1

        # After placing robots, place the ball
        ball_placed = False
        while not ball_placed:
            self.screen.fill(GREEN)
            text = font.render("Place the Ball. Click to place.", True, WHITE)
            text_rect = text.get_rect(center=(PITCH_WIDTH // 2, PITCH_HEIGHT // 4))  # Position text higher
            self.screen.blit(text, text_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if BALL_RADIUS <= x <= PITCH_WIDTH - BALL_RADIUS and BALL_RADIUS <= y <= PITCH_HEIGHT - BALL_RADIUS:
                        self.ball.x = x
                        self.ball.y = y
                        self.ball.vx = 0
                        self.ball.vy = 0
                        ball_placed = True
                        break
                    else:
                        print("Invalid position. Place within the pitch boundaries.")

    def handle_collisions(self): #unchanged
        # Robot-Robot collisions - robots should not pass each other!
        for i in range(len(self.robots)):
            for j in range(i + 1, len(self.robots)):
                robot1 = self.robots[i]
                robot2 = self.robots[j]
                if robot1.check_collision(robot2):
                    #Separate the robots (crude but functional)
                    dx = robot2.x - robot1.x
                    dy = robot2.y - robot1.y
                    angle = math.atan2(dy, dx)
                    overlap = ROBOT_RADIUS * 2 - distance(robot1.x, robot1.y, robot2.x, robot2.y) #distance of overlap to resolve

                    robot1.x -= (overlap/2) * math.cos(angle)
                    robot1.y -= (overlap/2) * math.sin(angle)
                    robot2.x += (overlap/2) * math.cos(angle)
                    robot2.y += (overlap/2) * math.sin(angle)

                    #No velocity change, as robots are not elastic.


        # Robot-Ball collisions. All collisions are elastic.
        for robot in self.robots:
            if not robot.dribbling and self.ball.check_collision(robot):
                #Elastic collision response
                dx = self.ball.x - robot.x
                dy = self.ball.y - robot.y
                angle = math.atan2(dy, dx)

                #Transfer momentum
                self.ball.vx = robot.vx + (BALL_MAX_SPEED * 1.2) * math.cos(angle) #Ball has some momentum based on robot.
                self.ball.vy = robot.vy + (BALL_MAX_SPEED * 1.2) * math.sin(angle)

                #Separate.
                overlap = ROBOT_RADIUS + BALL_RADIUS - distance(robot.x, robot.y, self.ball.x, self.ball.y)
                self.ball.x += (overlap/2) * math.cos(angle) #seperate ball from robot.
                self.ball.y += (overlap/2) * math.sin(angle)


    def check_goal(self): #Unchanged
        if self.goal_a.check_collision(self.ball):
            self.game_over = True
            self.winning_team = "B"  # Team B scored on Team A's goal
            return True
        if self.goal_b.check_collision(self.ball):
            self.game_over = True
            self.winning_team = "A"  # Team A scored on Team B's goal
            return True

        return False

    def reposition_ball(self): #Unchanged
        font = pygame.font.Font(None, int(30 * SCALE_FACTOR))
        ball_placed = False

        while not ball_placed:
            self.screen.fill(GREEN)
            text = font.render("Reposition the Ball. Click to place.", True, WHITE)
            text_rect = text.get_rect(center=(PITCH_WIDTH // 2, PITCH_HEIGHT // 4))  # Position text higher
            self.screen.blit(text, text_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if BALL_RADIUS <= x <= PITCH_WIDTH - BALL_RADIUS and BALL_RADIUS <= y <= PITCH_HEIGHT - BALL_RADIUS:
                        self.ball.x = x
                        self.ball.y = y
                        self.ball.vx = 0
                        self.ball.vy = 0
                        ball_placed = True
                        break
                    else:
                        print("Invalid position. Place within the pitch boundaries.")

    def run(self):
        running = True
        dribbling_robot = None
        team_a_actions = ["None"] * 3  # Three robots
        team_b_actions = ["None"] * 3  # Three robots
        # Main loop
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:  # Check clicks on manual intervention button!
                    if self.button_rect.collidepoint(event.pos):
                        self.manual_intervention = True
                        self.paused = True  # Pause game.
                        self.reposition_ball()  # Reposition the ball
                        self.paused = False  # Unpause game.
                        self.manual_intervention = False  # reset status

                # Basic keyboard control for the first two robots.  Expand as needed.
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Reposition ball
                        self.paused = True
                        self.reposition_ball()
                        self.paused = False

            if self.game_over:
                continue  # Skip game logic if game is over

            if self.paused:
                continue  # Skip game logic if paused

            # Robot movement (basic AI - replace with more sophisticated logic)
            for i, robot in enumerate(self.robots):
                robot_action = "idle"  # Default action

                # Make strategic decision (shoot or pass)
                if robot.dribbling:  # Cannot act unless dribbling ball
                    action = robot.make_strategic_decision()  # Get action state
                    if isinstance(action, dict) and action is not None and "action" in action:  # If action state
                        if action["action"] == "shoot":
                            state = robot.shoot(self.ball, 10 * SCALE_FACTOR)  # Only execute after you shoot.
                            if state:  # If there is a shooting.
                                robot_action = "shooting"
                        elif action["action"] == "move":
                            if "parameters" in action:  # Check if parameters exist again
                                robot.move(math.cos(action["parameters"]["angle"]), math.sin(action["parameters"]["angle"]))  # Move!
                                robot_action = "moving"
                        elif action["action"] == "pass":
                            target = action["parameters"]["target"] # get the target teammate from action
                            if target:
                                angle = angle_between_points(robot.x, robot.y, target.x, target.y) #Angle to that robot
                                robot.angle = angle #turn to that robot.
                                state = robot.shoot(self.ball, 5 * SCALE_FACTOR) #SHOOT at that angle
                                if state:
                                    robot_action = "passing"
                            else:
                                robot_action = "no pass target" #passing with no target
                        else:
                            robot_action = "idle" #unspecified action with the ball
                    else:
                        robot_action = "thinking..." #Still has ball but no longer has an action

                else:
                    action = robot.make_strategic_decision()  # Get action state

                    if isinstance(action, dict) and action is not None and "action" in action:  # If action state
                        if action["action"] == "move":
                            if "parameters" in action:  # Check if parameters exist again
                                robot.move(math.cos(action["parameters"]["angle"]), math.sin(action["parameters"]["angle"]))  # Move!
                                robot_action = "moving"
                        else: #If anything else like "shoot", set it as IDLE as it's doing nothing!
                            robot_action = "idle"
                    else: #Go to ball if no specific action is given.
                        angle_to_ball = math.atan2(self.ball.y - robot.y, self.ball.x - robot.x)
                        dist_to_ball = distance(robot.x, robot.y, self.ball.x, self.ball.y)
                        if dist_to_ball > ROBOT_RADIUS + BALL_RADIUS:  # Is far from ball
                            robot.move(math.cos(angle_to_ball), math.sin(angle_to_ball))  # Head to ball
                        robot_action = "heading to ball"

                # Set action message for the robot (This must be running regardless)
                if robot.team == "A":
                    team_a_actions[i % 3] = f"{robot.role}: {robot_action}" # Also include role
                else:
                    team_b_actions[i % 3] = f"{robot.role}: {robot_action}"  # Also include role

            # Dribbling logic:  One robot can dribbling_robot = None  # No robot is currently dribbling
            for robot in self.robots: #Check dribbling for robots
                if robot.dribble(self.ball):  #Robot can only dribble IF it's near the ball
                    dribbling_robot = robot #This is the robot dribbling
                    break #only 1 robot at a time
                else: #not dribbling.
                    dribbling_robot = None #Reset

            # Ball movement
            if not dribbling_robot:
                self.ball.move()

            # Collision detection and handling
            self.handle_collisions()

            # Check for goal
            if self.check_goal():
                print(f"Team {self.winning_team} wins!")
                time.sleep(3)  # Display message for 3 seconds
                running = False  # End the game loop
                break

            # Clear the screen
            self.screen.fill(GREEN)  # Pitch color

            #Draw UI here and then draw.
            pygame.draw.rect(self.screen, UI_BACKGROUND, (0, 0, PITCH_WIDTH + UI_WIDTH, UI_HEIGHT)) #draw rectangle at the top of pitch

            # Draw everything
            self.ball.draw(self.screen)
            for robot in self.robots:
                robot.draw(self.screen)

            # Draw the goalnets
            self.goal_a.draw(self.screen)
            self.goal_b.draw(self.screen)

            #Draw button!
            pygame.draw.rect(self.screen, BUTTON_COLOR, self.button_rect)
            self.screen.blit(self.button_text, self.button_text_rect) # Blit text on the button

            #Draw all text on the screen for UI:
            team_a_text = self.font_action.render("Team A:", True, RED)
            self.screen.blit(team_a_text, (10, 10))
            a1_text = self.font_action.render(f"A1: {team_a_actions[0]}", True, RED)
            self.screen.blit(a1_text, (10, 25))
            a2_text = self.font_action.render(f"A2: {team_a_actions[1]}", True, RED)
            self.screen.blit(a2_text, (10, 40))
            a3_text = self.font_action.render(f"A3: {team_a_actions[2]}", True, RED)
            self.screen.blit(a3_text, (10, 55))

            team_b_text = self.font_action.render("Team B:", True, BLUE)
            self.screen.blit(team_b_text, (PITCH_WIDTH / 2 +10, 10))  # Move further to right
            b1_text = self.font_action.render(f"B1: {team_b_actions[0]}", True, BLUE)
            self.screen.blit(b1_text, (PITCH_WIDTH / 2 +10, 25))  # Move further to right
            b2_text = self.font_action.render(f"B2: {team_b_actions[1]}", True, BLUE)
            self.screen.blit(b2_text, (PITCH_WIDTH / 2 +10, 40))  # Move further to right
            b3_text = self.font_action.render(f"B3: {team_b_actions[2]}", True, BLUE)
            self.screen.blit(b3_text, (PITCH_WIDTH / 2 +10, 55))  # Move further to right

            # Display game over message if game is over
            if self.game_over:
                font = pygame.font.Font(None, int(50 * SCALE_FACTOR))  # Scaled font size
                text = font.render(f"Team {self.winning_team} Wins!", True, YELLOW)
                text_rect = text.get_rect(center=(PITCH_WIDTH // 2,  (PITCH_HEIGHT) + (UI_HEIGHT/2)) ) #use new height also!
                self.screen.blit(text, text_rect)

            # Update the display
            pygame.display.flip()

            # Limit frame rate
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = FootballGame()
    game.run()
