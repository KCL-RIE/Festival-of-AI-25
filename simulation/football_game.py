# football_game.py (Main Simulation File)
import pygame
import math
import random
import time
from abc import ABC, abstractmethod
from ai_strategies import Strategy, LayeredCapabilitiesStrategy, DynamicRoleStrategy, SimpleGoToBallStrategy, FormationPassingStrategy
from constants_and_util import * # Import constants and functions


class Robot:
    def __init__(self, robot_id, x, y, team, color, game, strategy_class): # Pass strategy_class
        self.robot_id = robot_id
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
        self.role = "attacker" # Default role
        self.strategy = strategy_class() # Instantiate strategy here
        self.current_action = "idle"
        self.current_state_description = "Initial State" # For UI display

    @property
    def state_description(self):
        return self.current_state_description

    @state_description.setter
    def state_description(self, value):
        self.current_state_description = value


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
            self.y = self.y + self.mouth_offset * math.sin(self.angle)
            return True
        else:
            self.dribbling = False
            return False

    def shoot(self, ball, power=1.0): # Power parameter added, default 1.0
        if self.dribbling:
            self.dribbling = False
            release_speed = 1.5 * ROBOT_MAX_SPEED * power # Power influences release speed
            ball.vx = release_speed * math.cos(self.angle)
            ball.vy = release_speed * math.sin(self.angle)
            ball.x = self.x + (ROBOT_RADIUS + BALL_RADIUS + 1) * math.cos(self.angle)
            ball.y = self.y + (ROBOT_RADIUS + BALL_RADIUS + 1) * math.sin(self.angle)
            self.current_action = "shooting"
            return "shooting"
        self.current_action = "idle"
        return None

    def pass_ball(self, ball, angle, power=0.8): # Pass action
        if self.dribbling:
            self.dribbling = False
            release_speed = 1.2 * ROBOT_MAX_SPEED * power # Pass speed slightly less than shoot
            ball.vx = release_speed * math.cos(angle)
            ball.vy = release_speed * math.sin(angle)
            ball.x = self.x + (ROBOT_RADIUS + BALL_RADIUS + 1) * math.cos(angle)
            ball.y = self.y + (ROBOT_RADIUS + BALL_RADIUS + 1) * math.sin(angle)
            self.current_action = "passing"
            return "passing"
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

        label_text = self.game.font_robot_label.render(self.robot_id, True, WHITE)
        label_rect = label_text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(label_text, label_rect)

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
            "teammates": teammates,
            "opponent_robots": opponent_robots,
            "own_goal_x": self.game.goal_a.x + GOAL_WIDTH/2 if self.team == "A" else self.game.goal_b.x + GOAL_WIDTH/2 ,
            "own_goal_y": self.game.goal_a.y + (PITCH_HEIGHT/2) if self.team == "A" else self.game.goal_b.y+ (PITCH_HEIGHT/2),
            "opponent_goal_x": self.game.goal_b.x + GOAL_WIDTH/2 if self.team == "A" else self.game.goal_a.x + GOAL_WIDTH/2,
            "opponent_goal_y": self.game.goal_b.y+ (PITCH_HEIGHT/2) if self.team == "A" else self.game.goal_a.y+ self.game.goal_a.height / 2,
            "pitch_width": PITCH_WIDTH,
            "pitch_height": PITCH_HEIGHT,
            "distance_to_ball": distance(self.x, self.y, self.game.ball.x, self.game.ball.y)
        }
        return game_state

    def make_strategic_decision(self):
        game_state = self.get_game_state()
        action_result = self.strategy.make_strategic_decision(self, self.game, game_state) # Call external strategy

        if isinstance(action_result, dict) and action_result and "action" in action_result:
            action_type = action_result["action"]
            parameters = action_result.get("parameters", {})
            self.state_description = action_result.get("state_description", "Executing Action") # Update state description

            if action_type == "move":
                self.move(math.cos(parameters["angle"]), math.sin(parameters["angle"]))
                self.current_action = "moving"
            elif action_type == "shoot":
                self.shoot(self.game.ball)
                self.current_action = "shooting"
            elif action_type == "pass_ball":
                self.pass_ball(self.game.ball, parameters["angle"])
                self.current_action = "passing"
            elif action_type == "dribble":
                opponent_goal_x = game_state["opponent_goal_x"]
                opponent_goal_y = game_state["opponent_goal_y"]
                angle_to_goal = angle_between_points(self.x, self.y, opponent_goal_x, opponent_goal_y)
                self.move(math.cos(angle_to_goal), math.sin(angle_to_goal))
                self.current_action = "dribbling_strategic"
            elif action_type == "idle":
                self.current_action = "idle_strategic"
            else:
                self.current_action = "unknown_action" # Handle other action types as needed
        else:
            angle_to_ball = angle_between_points(self.x, self.y, self.game.ball.x, self.game.ball.y)
            dist_to_ball = distance(self.x, self.y, self.game.ball.x, self.game.ball.y)
            if dist_to_ball > ROBOT_RADIUS + BALL_RADIUS:
                self.move(math.cos(angle_to_ball), math.sin(angle_to_ball))
                self.current_action = "heading_to_ball_default"
            else:
                self.current_action = "idle_default"
            self.state_description = "Default - Heading to ball" # Default action description


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0

    def move(self):
        self.vx -= BALL_FRICTION * self.vx * DT
        self.vy -= BALL_FRICTION * self.vy * DT

        if abs(self.vx) < 0.1:
            self.vx = 0
        if abs(self.vy) < 0.1:
            self.vy = 0

        self.x += self.vx * DT
        self.y += self.vy * DT

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
        self.x = x
        self.y = y # vertical center of goal line
        self.width = GOAL_WIDTH # Line thickness
        self.height = GOAL_LINE_LENGTH # Line length - vertical
        self.team = team
        self.line_offset_horizontal = GOAL_WIDTH // 2 # Horizontal offset for line center
        self.GOAL_DEPTH = GOAL_DEPTH
        self.PITCH_HEIGHT = PITCH_HEIGHT

    def check_collision(self, ball):
        if self.team == "A":
            return ball.x <= self.x + self.line_offset_horizontal + BALL_RADIUS and self.y - self.height/2 <= ball.y <= self.y + self.height/2
        elif self.team == "B":
            return ball.x >= self.x - self.line_offset_horizontal - BALL_RADIUS and self.y - self.height/2 <= ball.y <= self.y + self.height/2
        return False

    def draw(self, screen):
        line_thickness = GOAL_WIDTH
        goal_line_length = GOAL_LINE_LENGTH

        goal_line_top_y = self.y - goal_line_length // 2 # Vertically center goal line

        if self.team == "A": # Team A goal - LEFT edge
            pygame.draw.line(screen, WHITE, (self.x+ self.line_offset_horizontal, goal_line_top_y), (self.x+ self.line_offset_horizontal, goal_line_top_y + goal_line_length), line_thickness) # Vertical line at left edge, shorter length
        elif self.team == "B": # Team B goal - RIGHT edge
            pygame.draw.line(screen, WHITE, (self.x- self.line_offset_horizontal, goal_line_top_y), (self.x- self.line_offset_horizontal, goal_line_top_y + goal_line_length), line_thickness) # Vertical line at right edge - shorter length


class FootballGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((PITCH_WIDTH + UI_WIDTH, PITCH_HEIGHT))
        pygame.display.set_caption("Robot Football")
        self.clock = pygame.time.Clock()

        # Initialize game time
        self.game_time = 0.0

        # Define pitch regions
        self.pitch_regions = {}
        self._define_pitch_regions()

        # Define formations
        self.formations = {}
        self._define_formations()
        self.current_formation = "attack"

        # Define available strategies (now just strategy classes, not instances)
        self.strategies = {
            "LayeredCapabilities": LayeredCapabilitiesStrategy,
            "DynamicRole": DynamicRoleStrategy,
            "SimpleGoToBall": SimpleGoToBallStrategy,
            "FormationPass": FormationPassingStrategy,
        }

        self.team_strategies = {
            "A": "DynamicRole",
            "B": "FormationPass"
        }

        # Initialize robots - NOW 4 ROBOTS PER TEAM!
        self.robots = []
        robot_ids = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]
        for i, robot_id in enumerate(robot_ids):
            team = "A" if i < 4 else "B"
            color = RED if team == "A" else BLUE
            strategy_name = self.team_strategies[team]
            strategy_class = self.strategies[strategy_name] # Get strategy class from name
            self.robots.append(Robot(robot_id, 0, 0, team, color, self, strategy_class)) # Pass strategy_class to Robot

        self.assign_roles()

        for robot in self.robots:
            robot.color = RED if robot.team == "A" else BLUE

        print ("Available Roles are: Striker, Supporter, Defender, Goalkeeper.")

        self.ball = Ball(PITCH_WIDTH // 2, PITCH_HEIGHT // 2)
        self.ball.vx = 0
        self.ball.vy = 0

        # Initialize goalnets - GOALNETS NOW VERTICAL LINES IN CENTRE OF GOAL REGIONS
        # Corrected GoalNet positions for 5x5 grid - using regions at the edges.
        region_goal_a_left = self.pitch_regions[0]  # Region 0 is at the leftmost edge
        region_goal_a_right = self.pitch_regions[5] # Region 5 is also at the leftmost edge, below region 0
        region_goal_b_left = self.pitch_regions[4]  # Region 4 is at the rightmost edge
        region_goal_b_right = self.pitch_regions[9] # Region 9 is also at the rightmost edge, below region 4

        # Goal A (left side) is positioned at the left edge of the pitch.
        # X-coordinate is set to the left edge of region_goal_a_left.
        # Y-coordinate is now set to the vertical center of the pitch (PITCH_HEIGHT / 2).
        self.goal_a = GoalNet(region_goal_a_left.left, PITCH_HEIGHT / 2, "A") # Vertical center of pitch

        # Goal B (right side) is positioned at the right edge of the pitch.
        # X-coordinate is set to the right edge of region_goal_b_right.
        # Y-coordinate is now set to the right edge of region_goal_b_right.
        self.goal_b = GoalNet(region_goal_b_right.right, PITCH_HEIGHT / 2, "B") # Vertical center of pitch

        self.goals = [self.goal_a, self.goal_b]
        self.GOAL_DEPTH = GOAL_DEPTH
        self.PITCH_HEIGHT = PITCH_HEIGHT

        self.game_over = False
        self.winning_team = None
        self.paused = False
        self.manual_intervention = False

        self.font = pygame.font.Font(None, int(24 * SCALE_FACTOR))

        self.font_action_small = pygame.font.Font(None, int(12 * SCALE_FACTOR))
        self.font_action = pygame.font.Font(None, int(20 * SCALE_FACTOR))
        self.font_region_label = pygame.font.Font(None, int(14 * SCALE_FACTOR))
        self.font_robot_label = pygame.font.Font(None, int(14 * SCALE_FACTOR))
        self.font_reposition_ball = pygame.font.Font(None, int(24 * SCALE_FACTOR))
        self.setup_initial_positions()

    def _define_pitch_regions(self):
        num_regions_x = 5 # Changed to 5
        num_regions_y = 5 # Changed to 5

        region_width = PITCH_WIDTH / num_regions_x
        region_height = PITCH_HEIGHT / num_regions_y

        region_id_counter = 0
        self.pitch_regions = {}

        for y_region in range(num_regions_y):
            for x_region in range(num_regions_x):
                x_start = x_region * region_width
                y_start = y_region * region_height
                region_rect = pygame.Rect(x_start, y_start, region_width, region_height)
                self.pitch_regions[region_id_counter] = region_rect
                region_id_counter += 1

    def _define_formations(self):
        # Formations are defined using region IDs.
        # Make sure the region IDs used here are valid for the 5x5 grid (0 to 24).
        self.formations = {
            "attack": {
                "striker": [22, 23, 24, 21, 20], # Example regions for striker in 5x5 grid
                "supporter": [17, 18, 19, 16, 15, 10, 11, 12], # Example regions for supporter in 5x5 grid
                "defender": [5, 6, 7, 8, 9, 0, 1, 2, 3, 4], # Example regions for defender in 5x5 grid
                "goalkeeper": [0, 1, 2, 3, 4], # Example regions for goalkeeper in 5x5 grid
            },
            "defense": {
                "striker": [17, 18, 19], # Example regions for striker in 5x5 grid
                "supporter": [12, 13, 14, 15, 16], # Example regions for supporter in 5x5 grid
                "defender": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], # Example regions for defender in 5x5 grid
                "goalkeeper": [0, 1, 2, 3, 4], # Example regions for goalkeeper in 5x5 grid
            }
        }

    def get_region_center(self, region_id):
        if region_id in self.pitch_regions:
            region_rect = self.pitch_regions[region_id]
            return region_rect.center
        return None

    def draw_pitch_regions(self, screen):
        for region_id, region_rect in self.pitch_regions.items():
            pygame.draw.rect(screen, BLACK, region_rect, 1)
            label_text = self.font_region_label.render(str(region_id), True, BLACK)
            label_rect = label_text.get_rect(center=region_rect.center)
            screen.blit(label_text, label_rect)

    def assign_roles(self):
        for team in ["A", "B"]:
            team_robots = [robot for robot in self.robots if robot.team == team]

            if len(team_robots) >= 4:
                 random.shuffle(team_robots)

                 team_robots[0].role = "striker"
                 team_robots[1].role = "supporter"
                 team_robots[2].role = "defender"
                 team_robots[3].role = "goalkeeper"
            else:
                print ("ERROR: Number of robots does not match number of roles. ")

    def setup_initial_positions(self):
        formation = self.formations["attack"]

        team_a_robots = [robot for robot in self.robots if robot.team == "A"]
        team_b_robots = [robot for robot in self.robots if robot.team == "B"]

        roles = ["striker", "supporter", "defender", "goalkeeper"]
        pitch_midline_x = PITCH_WIDTH / 2

        # Position Team A robots (LEFT half)
        team_a_regions = [region_id for region_id, rect in self.pitch_regions.items() if rect.centerx < pitch_midline_x]
        for i, role in enumerate(roles):
            target_region_ids = [reg for reg in formation[role] if reg in team_a_regions]
            if target_region_ids:
                region_center = self.get_region_center(random.choice(target_region_ids))
                if region_center:
                    team_a_robots[i].x, team_a_robots[i].y = region_center
            else:
                print(f"Warning: No suitable starting region for Team A, role: {role}. Placing at default.")
                team_a_robots[i].x, team_a_robots[i].y = ROBOT_RADIUS + GOAL_WIDTH + i * 2 * ROBOT_RADIUS, ROBOT_RADIUS + i * 2 * ROBOT_RADIUS

        # Position Team B robots (RIGHT half)
        team_b_regions = [region_id for region_id, rect in self.pitch_regions.items() if rect.centerx >= pitch_midline_x]
        for i, role in enumerate(roles):
            target_region_ids = [reg for reg in formation[role] if reg in team_b_regions]
            if target_region_ids:
                region_center = self.get_region_center(random.choice(target_region_ids))
                if region_center:
                    team_b_robots[i].x, team_b_robots[i].y = region_center
            else:
                print(f"Warning: No suitable starting region for Team B, role: {role}. Placing at default.")
                team_b_robots[i].x, team_b_robots[i].y = PITCH_WIDTH - (ROBOT_RADIUS+ GOAL_WIDTH + i * 2 * ROBOT_RADIUS), ROBOT_RADIUS + i * 2 * ROBOT_RADIUS

        self.ball.x = PITCH_WIDTH // 2
        self.ball.y = PITCH_HEIGHT // 2
        self.ball.vx = 0
        self.ball.vy = 0


    def handle_collisions(self):
        for i in range(len(self.robots)):
            for j in range(i + 1, len(self.robots)):
                robot1 = self.robots[i]
                robot2 = self.robots[j]
                if robot1.check_collision(robot2):
                    dx = robot2.x - robot1.x
                    dy = robot2.y - robot1.y
                    angle = math.atan2(dy, dx)
                    overlap = ROBOT_RADIUS * 2 - distance(robot1.x, robot1.y, robot2.x, robot2.y)

                    robot1.x -= (overlap/2) * math.cos(angle)
                    robot1.y -= (overlap/2) * math.sin(angle)
                    robot2.x += (overlap/2) * math.cos(angle)
                    robot2.y += (overlap/2) * math.sin(angle)


        for robot in self.robots:
            if not robot.dribbling and self.ball.check_collision(robot):
                dx = self.ball.x - robot.x
                dy = self.ball.y - robot.y
                angle = math.atan2(dy, dx)

                self.ball.vx = robot.vx + (BALL_MAX_SPEED * 1.2) * math.cos(angle)
                self.ball.vy = robot.vy + (BALL_MAX_SPEED * 1.2) * math.sin(angle)

                overlap = ROBOT_RADIUS + BALL_RADIUS - distance(robot.x, robot.y, self.ball.x, self.ball.y)
                self.ball.x += (overlap/2) * math.cos(angle)
                self.ball.y += (overlap/2) * math.sin(angle)


    def check_goal(self):
        if self.goal_a.check_collision(self.ball):
            self.game_over = True
            self.winning_team = "B"
            return True
        if self.goal_b.check_collision(self.ball):
            self.game_over = True
            self.winning_team = "A"
            return True

        return False

    def reposition_ball(self):
        font = self.font_reposition_ball
        ball_placed = False
        text = font.render("Reposition the Ball. Click to place.", True, WHITE)
        text_rect = text.get_rect(center=(PITCH_WIDTH // 2, PITCH_HEIGHT // 2))

        transparent_surface = pygame.Surface((PITCH_WIDTH, PITCH_HEIGHT), pygame.SRCALPHA)
        transparent_surface.fill(TRANSPARENT_GREY)

        while not ball_placed:
            self.screen.fill(GREEN)

            self.screen.blit(transparent_surface, (0,0))

            self.draw_pitch_regions(self.screen)
            self.ball.draw(self.screen)
            for robot in self.robots:
                robot.draw(self.screen)

            self.screen.blit(text, text_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x = event.pos[0]
                    y = event.pos[1]
                    if BALL_RADIUS <= x <= PITCH_WIDTH - BALL_RADIUS and BALL_RADIUS <= y <= PITCH_HEIGHT - BALL_RADIUS:
                        self.ball.x = x
                        self.ball.y = y
                        self.ball.vx = 0
                        self.ball.vy = 0
                        ball_placed = True
                        break
                    else:
                        print("Invalid position. Place within the pitch boundaries.")

    def get_closest_robot_to_ball(self, current_robot): # NEW helper function - find closest robot to ball (any team)
        closest_robot = None
        min_distance = float('inf')
        for robot in self.robots:
            dist_to_ball = distance(robot.x, robot.y, self.ball.x, self.ball.y)
            if dist_to_ball < min_distance:
                min_distance = dist_to_ball
                closest_robot = robot
        return closest_robot

    def run(self):
        running = True
        dribbling_robot = None
        team_a_actions = ["None"] * 4 # Now 4 robots per team
        team_b_actions = ["None"] * 4 # Now 4 robots per team
        # Main loop
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.paused = True
                        self.reposition_ball()
                        self.paused = False

            if self.game_over or self.paused:
                continue

            for i, robot in enumerate(self.robots):
                robot_action = "idle"
                robot_state_desc = "No State" # Initialize state description

                if robot.dribbling:
                    robot_action = "dribbling"
                    robot_state_desc = "Dribbling" # Basic dribbling state
                else:
                    action_result = robot.make_strategic_decision() # Get action result dictionary
                    robot_state_desc = robot.state_description # Get description from robot state

                    if isinstance(action_result, dict) and action_result and "action" in action_result:
                        if action_result["action"] == "move":
                            robot_action = "moving"
                        elif action_result["action"] == "shoot":
                            robot_action = "shooting"
                        elif action_result["action"] == "pass_ball":
                            robot_action = "passing"
                        elif action_result["action"] == "dribble":
                            robot_action = "dribbling_strategic"
                        elif action_result["action"] == "idle":
                            robot_action = "idle_strategic"
                        else:
                            robot_action = "role positioning" # Default for other role-based actions


                if robot.team == "A":
                    team_a_actions[i % 4] = f"{robot.role}: {robot_action} ({robot_state_desc})" # Now 4 robots per team, include state description
                else:
                    team_b_actions[i % 4] = f"{robot.role}: {robot_action} ({robot_state_desc})" # Now 4 robots per team, include state description

            dribbling_robot = None
            for robot in self.robots:
                if robot.dribble(self.ball):
                    dribbling_robot = robot
                    break

            if not dribbling_robot:
                self.ball.move()

            self.handle_collisions()

            if self.check_goal():
                print(f"Team {self.winning_team} wins!")
                time.sleep(3)
                running = False
                break

            self.screen.fill(GREEN)

            self.draw_pitch_regions(self.screen)

            pygame.draw.rect(self.screen, UI_BACKGROUND, (PITCH_WIDTH, 0, UI_WIDTH, UI_HEIGHT))

            self.ball.draw(self.screen)
            for robot in self.robots:
                robot.draw(self.screen)

            self.goal_a.draw(self.screen)
            self.goal_b.draw(self.screen)


            ui_text_y_offset = 10
            team_a_text = self.font_action.render("Team A:", True, RED)
            self.screen.blit(team_a_text, (PITCH_WIDTH + 10, ui_text_y_offset))
            ui_text_y_offset += 30
            a1_text = self.font_action_small.render(f"A1: {team_a_actions[0]}", True, RED)
            self.screen.blit(a1_text, (PITCH_WIDTH + 10, ui_text_y_offset))
            ui_text_y_offset += 30
            a2_text = self.font_action_small.render(f"A2: {team_a_actions[1]}", True, RED)
            self.screen.blit(a2_text, (PITCH_WIDTH + 10, ui_text_y_offset))
            ui_text_y_offset += 30
            a3_text = self.font_action_small.render(f"A3: {team_a_actions[2]}", True, RED)
            self.screen.blit(a3_text, (PITCH_WIDTH + 10, ui_text_y_offset))
            ui_text_y_offset += 30
            a4_text = self.font_action_small.render(f"A4: {team_a_actions[3]}", True, RED)
            self.screen.blit(a4_text, (PITCH_WIDTH + 10, ui_text_y_offset))

            ui_text_y_offset += 40

            team_b_text = self.font_action.render("Team B:", True, BLUE)
            self.screen.blit(team_b_text, (PITCH_WIDTH + 10, ui_text_y_offset))
            ui_text_y_offset += 30
            b1_text = self.font_action_small.render(f"B1: {team_b_actions[0]}", True, BLUE)
            self.screen.blit(b1_text, (PITCH_WIDTH + 10, ui_text_y_offset))
            ui_text_y_offset += 30
            b2_text = self.font_action_small.render(f"B2: {team_b_actions[1]}", True, BLUE)
            self.screen.blit(b2_text, (PITCH_WIDTH + 10, ui_text_y_offset))
            ui_text_y_offset += 30
            b3_text = self.font_action_small.render(f"B3: {team_b_actions[2]}", True, BLUE)
            self.screen.blit(b3_text, (PITCH_WIDTH + 10, ui_text_y_offset))
            ui_text_y_offset += 30
            b4_text = self.font_action_small.render(f"B4: {team_b_actions[3]}", True, BLUE)
            self.screen.blit(b4_text, (PITCH_WIDTH + 10, ui_text_y_offset))


            if self.game_over:
                font = pygame.font.Font(None, int(50 * SCALE_FACTOR))
                text = font.render(f"Team {self.winning_team} Wins!", True, YELLOW)
                text_rect = text.get_rect(center=(PITCH_WIDTH // 2,  (PITCH_HEIGHT) + (UI_HEIGHT/2)) )
                self.screen.blit(text, text_rect)

            pygame.display.flip()
            self.game_time += DT # Increment game time
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    game = FootballGame()
    game.run()
