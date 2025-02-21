import pygame
import random
import math

# Constants
WIDTH, HEIGHT = 300, 200  # Pitch size in cm
ROBOT_RADIUS = 6  # Robot radius (12cm diameter)
BALL_RADIUS = 2    # Ball radius (4cm diameter)
FPS = 30

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH * 3, HEIGHT * 3))  # Scale for visibility
pygame.display.set_caption("Robot Soccer Simulation")
clock = pygame.time.Clock()

def draw_robot(pos, color):
    pygame.draw.circle(screen, color, (int(pos[0] * 3), int(pos[1] * 3)), ROBOT_RADIUS * 3)

def draw_ball(pos):
    pygame.draw.circle(screen, ORANGE, (int(pos[0] * 3), int(pos[1] * 3)), BALL_RADIUS * 3)

def distance(a, b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

class Robot:
    def __init__(self, x, y, team):
        self.x = x
        self.y = y
        self.team = team
        self.color = RED if team == "A" else BLUE
        self.speed = 2  # cm per frame

    def move_towards(self, target, robots):
        if distance((self.x, self.y), target) > ROBOT_RADIUS:
            angle = math.atan2(target[1] - self.y, target[0] - self.x)
            new_x = self.x + self.speed * math.cos(angle)
            new_y = self.y + self.speed * math.sin(angle)
            
            # Check for collisions with other robots
            for other in robots:
                if other != self and distance((new_x, new_y), (other.x, other.y)) < 2 * ROBOT_RADIUS:
                    return  # Stop movement if collision detected
            
            self.x, self.y = new_x, new_y
        
        # Keep within bounds
        self.x = max(ROBOT_RADIUS, min(WIDTH - ROBOT_RADIUS, self.x))
        self.y = max(ROBOT_RADIUS, min(HEIGHT - ROBOT_RADIUS, self.y))

    def check_collision(self, ball):
        if distance((self.x, self.y), (ball.x, ball.y)) < ROBOT_RADIUS + BALL_RADIUS:
            ball.speed_x = (ball.x - self.x) * 0.5
            ball.speed_y = (ball.y - self.y) * 0.5

    def draw(self):
        draw_robot((self.x, self.y), self.color)

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed_x = 0
        self.speed_y = 0

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_x *= 0.95  # Friction
        self.speed_y *= 0.95  # Friction
        
        # Keep ball within bounds
        if self.x - BALL_RADIUS < 0 or self.x + BALL_RADIUS > WIDTH:
            self.speed_x *= -1
            self.x = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, self.x))
        if self.y - BALL_RADIUS < 0 or self.y + BALL_RADIUS > HEIGHT:
            self.speed_y *= -1
            self.y = max(BALL_RADIUS, min(HEIGHT - BALL_RADIUS, self.y))

    def reposition(self, x, y):
        self.x = x
        self.y = y
        self.speed_x = 0
        self.speed_y = 0

    def draw(self):
        draw_ball((self.x, self.y))

# Initialize game objects
robots = [Robot(random.randint(20, WIDTH - 20), random.randint(20, HEIGHT - 20), "A") for _ in range(3)] + \
         [Robot(random.randint(20, WIDTH - 20), random.randint(20, HEIGHT - 20), "B") for _ in range(3)]
ball = Ball(WIDTH // 2, HEIGHT // 2)

def find_best_position(team, ball):
    if team == "A":
        return [(ball.x - 30, ball.y - 20), (ball.x + 30, ball.y - 20), (ball.x, ball.y + 30)]
    else:
        return [(ball.x - 30, ball.y + 20), (ball.x + 30, ball.y + 20), (ball.x, ball.y - 30)]

def execute_tactics():
    team_a = [r for r in robots if r.team == "A"]
    team_b = [r for r in robots if r.team == "B"]
    
    positions_a = find_best_position("A", ball)
    positions_b = find_best_position("B", ball)
    
    for i, robot in enumerate(team_a):
        robot.move_towards(positions_a[i], robots)
    for i, robot in enumerate(team_b):
        robot.move_towards(positions_b[i], robots)
    
    for robot in robots:
        robot.check_collision(ball)

running = True
while running:
    screen.fill(GREEN)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            ball.reposition(WIDTH // 2, HEIGHT // 2)
    
    ball.move()
    ball.draw()
    execute_tactics()
    
    for robot in robots:
        robot.draw()
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
