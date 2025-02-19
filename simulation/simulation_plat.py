import pygame
import math
import random
import time

# Constants
# Original Pitch Dimensions (in cm)
ORIGINAL_PITCH_WIDTH = 300
ORIGINAL_PITCH_HEIGHT = 200

# Scaling factor for 1920x1080 resolution
SCALE_FACTOR = 3  # Changed to 3

PITCH_WIDTH = int(ORIGINAL_PITCH_WIDTH * SCALE_FACTOR)
PITCH_HEIGHT = int(ORIGINAL_PITCH_HEIGHT * SCALE_FACTOR)

ROBOT_RADIUS = int(6 * SCALE_FACTOR)  # 12cm diameter / 2
BALL_RADIUS = int(2 * SCALE_FACTOR)  # 4cm diameter / 2
MOUTH_WIDTH = int(4 * SCALE_FACTOR)   # Adjust as needed - length of mouth opening
MOUTH_LENGTH = int(2 * SCALE_FACTOR)  # Adjust as needed - width of mouth opening
ROBOT_MAX_SPEED = 3 * SCALE_FACTOR
BALL_MAX_SPEED = 8 * SCALE_FACTOR
DT = 0.1  # Time step for simulation (adjust for stability/speed)

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

# AI Constants (tune these)
SHOOT_CHANCE = 0.1  # Base chance to shoot (Used by Team B for "Long Shots")
PASS_CHANCE = 0.9  # Increased passing chance
PASS_DISTANCE = 5 * ROBOT_RADIUS  # Preferred passing distance
BLOCKING_DISTANCE = 4 * ROBOT_RADIUS
AGGRESSIVE_SHOOT_RANGE = 10 * ROBOT_RADIUS  # Bonus shooting range
LONG_SHOT_CHANCE = 0.1 #Chance of long shot in Team B

#UI Button Parameters
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 30
BUTTON_X = PITCH_WIDTH - BUTTON_WIDTH - 10
BUTTON_Y = 10
BUTTON_COLOR = YELLOW
BUTTON_TEXT_COLOR = BLACK

def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

class Robot:
    def __init__(self, x, y, team, color, game):  # Pass game instance
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
        self.role = "attacker"  # Default Role - You can expand this

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
            return "shooting"
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

    def make_strategic_decision(self):
        """
        Implements the strategic decision-making based on the team strategy.
        """
        ball = self.game.ball

        if self.dribbling:  # Only make decisions if dribbling
            if self.team == "A":
                return self.team_a_strategy()  # Dribbling (Red Team)
            else:
                return self.team_b_strategy()  # Shooting/Passing (Blue Team)
        else: #if not dribbling
            # Always go for the ball
            angle_to_ball = math.atan2(ball.y - self.y, ball.x - self.x)
            dist_to_ball = distance(self.x, self.y, ball.x, ball.x)

            if dist_to_ball > ROBOT_RADIUS + BALL_RADIUS: #Is far from ball
                self.move(math.cos(angle_to_ball), math.sin(angle_to_ball)) #Head to ball
                return "heading to ball"
            else: #Idle behaviour
                return "idle"

    def team_a_strategy(self):
        """
        Team A: Prefers Dribbling - only shoots if absolutely unavoidable/forced
        """

        #Calculate angle to the opponent's goal.
        goal_x = self.game.goal_b.x + self.game.goal_b.width / 2
        goal_y = self.game.goal_b.y + self.game.goal_b.height / 2
        angle_to_goal = math.atan2(goal_y - self.y, goal_x - self.x)

        #Move towards the goal to dribble.
        self.move(math.cos(angle_to_goal), math.sin(angle_to_goal)) #Dribble towards goal.
        return "dribbling" #Dribbling State
    def team_b_strategy(self):
        """
        Team B: Prioritizes Shooting and Passing (Guaranteed to Shoot or Pass Every Time)
        """
        #If there is a teammate, and chance is present: Then pass!
        team_robots = [robot for robot in self.game.robots if robot.team == self.team and robot != self]
        teammate = team_robots[0] if team_robots else None

        goal_x = self.game.goal_a.x + self.game.goal_a.width / 2
        goal_y = self.game.goal_a.y + self.game.goal_a.height / 2
        angle_to_goal = math.atan2(goal_y - self.y, goal_x - self.x)
        dist_to_goal = distance(self.x, self.y, goal_x, goal_y)

        #Will only pass if a teammate exists.
        if teammate and random.random() < PASS_CHANCE: #If has teammate and passes under pass chance
                self.angle = math.atan2(teammate.y - self.y, teammate.x - self.x) #Then passes to teammate and is facing ball!
                return self.shoot(self.game.ball, 5 * SCALE_FACTOR)
        else: #Then simply shoot if all else fails: Long shot

            # Attempt Long Shot (Low Probability)
            if random.random() < LONG_SHOT_CHANCE: #Shoot with a long shot.
                self.angle = angle_to_goal #Face goal
                return self.shoot(self.game.ball, 10 * SCALE_FACTOR) #SHOOT LONG DISTANCE
            else:
                self.angle = angle_to_goal
                return self.shoot(self.game.ball, 10 * SCALE_FACTOR) #SHOOT in lieu of nothing.


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0

    def move(self):
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
        self.screen = pygame.display.set_mode((PITCH_WIDTH, PITCH_HEIGHT))
        pygame.display.set_caption("Robot Football")
        self.clock = pygame.time.Clock()

        # Initialize robots (two teams) - Initial positions will be set by the user
        self.robots = [
            Robot(0, 0, "A", RED, self),  # Initial positions are placeholders, pass game instance
            Robot(0, 0, "B", BLUE, self),
            Robot(0, 0, "A", RED, self),
            Robot(0, 0, "B", BLUE, self),
        ]

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

        self.setup_initial_positions()

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

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN: #Check clicks on manual intervention button!
                    if self.button_rect.collidepoint(event.pos):
                        self.manual_intervention = True
                        self.paused = True #Pause game.
                        self.reposition_ball() #Reposition the ball
                        self.paused = False #Unpause game.
                        self.manual_intervention = False #reset status

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
                        
