import pygame
import math
import random
import time
from abc import ABC, abstractmethod

# Constants
# Original Pitch Dimensions (in cm)
ORIGINAL_PITCH_WIDTH = 300
ORIGINAL_PITCH_HEIGHT = 200

# Scaling factor for 1920x1080 resolution
SCALE_FACTOR = 3  # Changed to 3

PITCH_WIDTH = int(ORIGINAL_PITCH_WIDTH * SCALE_FACTOR)
PITCH_HEIGHT = int(ORIGINAL_PITCH_HEIGHT * SCALE_FACTOR)
UI_WIDTH = 200  # Space to show messages about team members
UI_HEIGHT = PITCH_HEIGHT # Make UI full height

ROBOT_RADIUS = int(6 * SCALE_FACTOR)  # 12cm diameter / 2
BALL_RADIUS = int(2 * SCALE_FACTOR)  # 4cm diameter / 2
MOUTH_WIDTH = int(4 * SCALE_FACTOR)   # Adjust as needed - length of mouth opening
MOUTH_LENGTH = int(2 * SCALE_FACTOR)  # Adjust as needed - width of mouth opening
ROBOT_MAX_SPEED = 3 * SCALE_FACTOR
BALL_MAX_SPEED = 8 * SCALE_FACTOR
DT = 0.1  # Time step for simulation (adjust for stability/speed)
BALL_FRICTION = 0.05  # Friction coefficient to decelerate ball.

# Goalnet dimensions
GOAL_WIDTH = int(20 * SCALE_FACTOR)   # Swapped width and height
GOAL_HEIGHT = int(40 * SCALE_FACTOR)  # Swapped width and height
GOAL_DEPTH = int(2 * SCALE_FACTOR)  # Thickness of the goalnet lines

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
UI_BACKGROUND = (220, 220, 220) #Light Gray

# AI Constants (tune these)
SHOOT_CHANCE = 0.2  # Base chance to shoot (Used by Team B for "Long Shots")
PASS_CHANCE = 0.9  # Increased passing chance
PASS_DISTANCE = 5 * ROBOT_RADIUS  # Preferred passing distance
BLOCKING_DISTANCE = 4 * ROBOT_RADIUS
AGGRESSIVE_SHOOT_RANGE = 10 * ROBOT_RADIUS  # Bonus shooting range
LONG_SHOT_CHANCE = 0.1  # Chance of long shot in Team B

#UI Button Parameters
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 30
BUTTON_X = PITCH_WIDTH - BUTTON_WIDTH - 10
BUTTON_Y = 10
BUTTON_COLOR = YELLOW
BUTTON_TEXT_COLOR = BLACK

def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

class Strategy(ABC):
    @abstractmethod
    def make_strategic_decision(self, robot, game, game_state):
        """
        This method is the entry point for the strategy.

        Args:
            robot (Robot): The robot making the decision.
            game (FootballGame): The current game state.
            game_state: All robot positions and ball positions etc.

        Returns:
            str: A description of the action taken (e.g., "shooting", "passing", "dribbling").
        """
        pass

class DribbleStrategy(Strategy):
    def make_strategic_decision(self, robot, game, game_state):
        # Code to implement the dribbling strategy.
        goal_x = game.goal_b.x + game.goal_b.width / 2
        goal_y = game.goal_b.y + game.goal_b.height / 2
        angle_to_goal = math.atan2(goal_y - robot.y, goal_x - robot.x)

        # Move towards the goal to dribble.
        return {"action": "move", "parameters": {"angle": angle_to_goal}}  # Return move towards ball and not shoot

class PassAndShootStrategy(Strategy):
    def make_strategic_decision(self, robot, game, game_state):
        # Code to implement the passing and shooting strategy

        team_robots = [r for r in game.robots if r.team == robot.team and r != robot]
        teammate = team_robots[0] if team_robots else None
        shootAction = {"action": "shoot", "parameters": {}}
        if teammate:
            if random.random() < PASS_CHANCE:
                return {"action": "pass", "parameters": {}}
        #Otherwise fall back on shooting it anyway

        return shootAction

class Robot:
    def __init__(self, x, y, team, color, game, strategy):  # Pass game instance
        self.x = x
        self.y = y
        self.angle = 0  # Facing direction in radians
        self.speed = 0
        self.team = team
        self.color = color
        self.dribbling = False  # Flag to indicate if dribbling the ball
        self.mouth_offset = ROBOT_RADIUS + BALL_RADIUS  # Distance from center of robot to center of ball
        self.vx = 0  # Add x-velocity
        self.vy = 0  # Add y-velocity
        self.game = game  # Store the game instance
        self.role = "attacker"
        self.strategy = strategy # Added strategy
        self.current_action = "idle" #Initial state

    def move(self, dx, dy):
        # Normalize the movement vector and scale by speed
        magnitude = math.sqrt(dx**2 + dy**2)
        if magnitude > 0:
            dx = (dx / magnitude) * ROBOT_MAX_SPEED * DT
            dy = (dy / magnitude) * ROBOT_MAX_SPEED * DT

        self.vx = dx
        self.vy = dy

        new_x = self.x + dx
        new_y = self.y + dy

        # Keep within bounds
        self.x = max(ROBOT_RADIUS, min(new_x, PITCH_WIDTH - ROBOT_RADIUS))
        self.y = max(ROBOT_RADIUS, min(new_y, PITCH_HEIGHT - ROBOT_RADIUS))

        # Update angle based on movement direction (if moving)
        if dx != 0 or dy != 0:
            self.angle = math.atan2(dy, dx)

    def check_collision(self, other):
        dist = distance(self.x, self.y, other.x, other.y)
        return dist <= ROBOT_RADIUS + BALL_RADIUS if isinstance(other, Ball) else dist <= 2 * ROBOT_RADIUS

    def dribble(self, ball):
        # Hexagon Dribbling Condition: Only dribble if ball is near the 'mouth' side
        mouth_angle = self.angle #Angle of the mouth
        ball_angle = math.atan2(ball.y - self.y, ball.x - self.x) #Angle of ball with respect to center of robot
        angle_diff = (ball_angle - mouth_angle + math.pi) % (2 * math.pi) - math.pi #Normalize angle difference to [-pi, pi]

        if abs(angle_diff) < math.pi / 6 and distance(self.x, self.y, ball.x, ball.y) <= ROBOT_RADIUS + BALL_RADIUS: # pi/6 radian range around mouth angle (30 degree range)
            self.dribbling = True
            ball.vx = 0  # Stop the ball's movement when dribbling
            ball.vy = 0
            # Attach the ball to the robot's mouth position
            ball.x = self.x + self.mouth_offset * math.cos(self.angle)
            ball.y = self.y + self.mouth_offset * math.sin(self.angle)
            return True
        else:
            self.dribbling = False
            return False

    def shoot(self, ball, power):
        if self.dribbling:
            self.dribbling = False  # Release the ball
            # Apply a force to the ball in the direction the robot is facing
            release_speed = 1.5 * ROBOT_MAX_SPEED  # Velocity scaling (1.5x Robot speed)
            ball.vx = release_speed * math.cos(self.angle)
            ball.vy = release_speed * math.sin(self.angle)
            #Move ball away from the robot:
            ball.x = self.x + (ROBOT_RADIUS + BALL_RADIUS + 1) * math.cos(self.angle) #+1 prevents instant re-grab
            ball.y = self.y + (ROBOT_RADIUS + BALL_RADIUS + 1) * math.sin(self.angle)
            self.current_action = "shooting"
            return "shooting"
        self.current_action = "idle"
        return None

    def draw(self, screen):
        # Draw the hexagon
        points = []
        for i in range(6):
            angle = self.angle + 2 * math.pi / 6 * i
            x = self.x + ROBOT_RADIUS * math.cos(angle)
            y = self.y + ROBOT_RADIUS * math.sin(angle)
            points.append((int(x), int(y)))

        pygame.draw.polygon(screen, self.color, points, 0)  # Filled hexagon

        # Bolden the mouth side
        mouth_index = 0  # Define mouth index
        start_index = mouth_index
        end_index = (mouth_index + 1) % 6
        pygame.draw.line(screen, BLACK, points[start_index], points[end_index], int(3*SCALE_FACTOR)) # Thicker mouth line

    def get_game_state(self): # Turns game state into inputs for various strategies
        teammate = None
        for team_robot in self.game.robots:
            if team_robot.team == self.team and team_robot != self:
                teammate = team_robot
                break

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
            "teammate_present": teammate is not None,
            "teammate_x": teammate.x if teammate else None,
            "teammate_y": teammate.y if teammate else None,
            "own_goal_x": self.game.goal_a.x + self.game.goal_a.width / 2 if self.team == "B" else self.game.goal_b.x + self.game.goal_b.width / 2,
            "own_goal_y": self.game.goal_a.y + self.game.goal_a.height / 2 if self.team == "B" else self.game.goal_b.y + self.game.goal_b.height / 2,
            "opponent_goal_x": self.game.goal_b.x + self.game.goal_b.width / 2 if self.team == "A" else self.game.goal_a.x + self.game.goal_a.width / 2,
            "opponent_goal_y": self.game.goal_b.y + self.game.goal_b.height / 2 if self.team == "A" else self.game.goal_a.y + self.game.goal_a.height / 2,
            "pitch_width": PITCH_WIDTH,
            "pitch_height": PITCH_HEIGHT
        }
        return game_state

    def make_strategic_decision(self):
        """Delegates the decision to the current strategy, passing the game state."""
        game_state = self.get_game_state()
        action = self.strategy.make_strategic_decision(self, self.game, game_state)
        if not action:
            return

        #Only take actions if they have the ball!
        if self.dribbling:
            if action["action"] == "move":
                self.current_action = "moving"
                self.move(math.cos(action["parameters"]["angle"]), math.sin(action["parameters"]["angle"])) #Move!
            elif action["action"] == "shoot" or action["action"] == "pass":
                state = self.shoot(self.game.ball, 10 * SCALE_FACTOR) #This is where to implement the ball shooting
                if state:
                    self.current_action = "shooting"

        return self.current_action

class Ball:
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

class GoalNet:
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

class FootballGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((PITCH_WIDTH + UI_WIDTH, PITCH_HEIGHT))
        pygame.display.set_caption("Robot Football")
        self.clock = pygame.time.Clock()

        # Define available strategies
        self.strategies = {
            "Dribble": DribbleStrategy(),
            "PassAndShoot": PassAndShootStrategy()
            # Add more strategies here as needed
        }

        # Assign initial strategies to teams
        self.team_strategies = {
            "A": "Dribble",  # Team A starts with Dribble strategy
            "B": "PassAndShoot"  # Team B starts with PassAndShoot strategy
        }

        # Initialize robots (two teams) - Initial positions will be set by the user
        self.robots = [
            Robot(0, 0, "A", RED, self, self.strategies[self.team_strategies["A"]]),  # Initial positions are placeholders, pass game instance
            Robot(0, 0, "B", BLUE, self, self.strategies[self.team_strategies["B"]]),
            Robot(0, 0, "A", RED, self, self.strategies[self.team_strategies["A"]]),
            Robot(0, 0, "B", BLUE, self, self.strategies[self.team_strategies["B"]]),
        ]

        #Team A's default
        for robot in self.robots:
            if robot.team == "A":
                robot.color = RED

        #Team B's default
        for robot in self.robots:
            if robot.team == "B":
                robot.color = BLUE

        #A note about which team does what - for the user.
        print ("Team A (Red) always dribbles. Team B (Blue) will always shoot/pass. ")

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

    def change_strategy(self, team, strategy_name):
        """Changes the strategy for a team."""
        if strategy_name in self.strategies:
            self.team_strategies[team] = strategy_name
            # Update the strategy for all robots on that team
            for robot in self.robots:
                if robot.team == team:
                    robot.strategy = self.strategies[strategy_name]
            print(f"Team {team} strategy changed to {strategy_name}")
        else:
            print(f"Error: Strategy '{strategy_name}' not found.")


    def setup_initial_positions(self):
        font = pygame.font.Font(None, int(30 * SCALE_FACTOR))
        robot_index = 0
        while robot_index < len(self.robots):
            self.screen.fill(GREEN)
            text = font.render(f"Place Robot {robot_index + 1} (Team {self.robots[robot_index].team}). Click to place.", True, WHITE)
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

    def handle_collisions(self):
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


    def check_goal(self):
        if self.goal_a.check_collision(self.ball):
            self.game_over = True
            self.winning_team = "B"  # Team B scored on Team A's goal
            return True
        if self.goal_b.check_collision(self.ball):
            self.game_over = True
            self.winning_team = "A"  # Team A scored on Team B's goal
            return True

        return False

    def reposition_ball(self):
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
        team_a_actions = ["None"] * 2  # Two robots
        team_b_actions = ["None"] * 2  # Two robots
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
                    if event.key == pygame.K_w:  # Move robot 0 forward
                        self.robots[0].move(math.cos(self.robots[0].angle), math.sin(self.robots[0].angle))
                    if event.key == pygame.K_s:  # Move robot 0 backward
                        self.robots[0].move(-math.cos(self.robots[0].angle), -math.sin(self.robots[0].angle))
                    if event.key == pygame.K_a:  # Rotate robot 0 left
                        self.robots[0].angle -= 0.1
                    if event.key == pygame.K_d:  # Rotate robot 0 right
                        self.robots[0].angle += 0.1
                    if event.key == pygame.K_SPACE:
                        self.robots[0].shoot(self.ball, 10 * SCALE_FACTOR)  # Shoot with power 10

                    # Control for robot 1 (Team B)
                    if event.key == pygame.K_UP:  # Move robot 1 forward
                        self.robots[1].move(math.cos(self.robots[1].angle), math.sin(self.robots[1].angle))
                    if event.key == pygame.K_DOWN:  # Move robot 1 backward
                        self.robots[1].move(-math.cos(self.robots[1].angle), -math.sin(self.robots[1].angle))
                    if event.key == pygame.K_LEFT:  # Rotate robot 1 left
                        self.robots[1].angle -= 0.1
                    if event.key == pygame.K_RIGHT:  # Rotate robot 1 right
                        self.robots[1].angle += 0.1
                    if event.key == pygame.K_RETURN:
                        self.robots[1].shoot(self.ball, 10 * SCALE_FACTOR)  # Shoot with power 10

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
                # Make strategic decision (shoot or pass)
                if robot.dribbling:  # Cannot act unless dribbling ball
                    action = robot.make_strategic_decision()  # Get action state
                    if action:  # If action state
                        if action["action"] == "shoot":
                            state = robot.shoot(self.ball, 10 * SCALE_FACTOR)  # Only execute after you shoot.
                            if state:  # If there is a shooting.
                                robot_action = "shooting"
                        elif action["action"] == "move":
                            if "parameters" in action:  # Check if parameters exist again
                                robot.move(math.cos(action["parameters"]["angle"]), math.sin(action["parameters"]["angle"]))  # Move!
                                robot_action = "moving"
                        elif action["action"] == "pass":
                            robot.shoot(self.ball, 5 * SCALE_FACTOR)
                            robot_action = "passing"
                else:
                    # Always go for the ball unless doing something
                    angle_to_ball = math.atan2(self.ball.y - robot.y, self.ball.x - robot.x)
                    dist_to_ball = distance(robot.x, robot.y, self.ball.x, self.ball.y)

                    if dist_to_ball > ROBOT_RADIUS + BALL_RADIUS:  # Is far from ball
                        robot.move(math.cos(angle_to_ball), math.sin(angle_to_ball))  # Head to ball
                    robot_action = "heading to ball"

                # Set action message for the robot (This must be running regardless)
                if robot.team == "A":
                    team_a_actions[i % 2] = robot_action  # Store into A
                else:
                    team_b_actions[i % 2] = robot_action  # Store into B

            # Dribbling logic:  One robot can dribbling_robot = None  # No robot is currently dribbling

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

            team_b_text = self.font_action.render("Team B:", True, BLUE)
            self.screen.blit(team_b_text, (PITCH_WIDTH / 2 +10, 10))  # Move further to right
            b1_text = self.font_action.render(f"B1: {team_b_actions[0]}", True, BLUE)
            self.screen.blit(b1_text, (PITCH_WIDTH / 2 +10, 25))  # Move further to right
            b2_text = self.font_action.render(f"B2: {team_b_actions[1]}", True, BLUE)
            self.screen.blit(b2_text, (PITCH_WIDTH / 2 +10, 40))  # Move further to right

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
