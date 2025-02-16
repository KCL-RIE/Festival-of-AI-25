import cv2
import numpy as np
import socket
import time

class Node:
    def __init__(self, maze_coordinates):
        self.maze_coordinates = maze_coordinates
        self.parent = None
        self.children = []
        self.visited = False

class Maze:
    decimal = [
        [9, 8, 8, 12, 11, 12, 9, 8, 8, 14],
        [5, 1, 0, 4, 9, 4, 5, 3, 2, 12],
        [5, 5, 3, 4, 1, 4, 1, 14, 9, 4],
        [5, 1, 12, 1, 0, 0, 4, 15, 1, 6],
        [5, 3, 0, 2, 2, 4, 3, 10, 0, 12],
        [1, 12, 3, 8, 12, 1, 8, 8, 2, 4],
        [5, 5, 9, 4, 5, 3, 0, 0, 8, 6],
        [1, 6, 1, 6, 3, 12, 3, 2, 4, 15],
        [5, 9, 4, 9, 8, 0, 8, 12, 3, 4],
        [3, 2, 2, 2, 2, 6, 3, 2, 10, 6]
    ]
    binary = [[bin(num)[2:].zfill(4) for num in row] for row in decimal]
    
    def print_maze_to_console(self):
        for row in self.binary:
            print(' '.join(row))
            
    # initializes the maze's nodes and sets their children
    def __init__(self): 
        self.nodes = [[Node((i, j)) for j in range(len(self.binary[i]))] for i in range(len(self.binary))]
        for i in range(len(self.binary)):
            for j in range(len(self.binary[i])):
                cell = self.binary[i][j]
                node = self.nodes[i][j]
                if cell[0] == '0': #Top 
                    node.children.append(self.nodes[i - 1][j])
                if cell[1] == '0': #Right
                    node.children.append(self.nodes[i][j + 1])
                if cell[2] == '0': #Bottom
                    node.children.append(self.nodes[i + 1][j])
                if cell[3] == '0': #Left
                    node.children.append(self.nodes[i][j - 1])
    
    # resets the nodes
    def reset_nodes(self):
        for i in range(len(self.binary)):
            for j in range(len(self.binary[i])):
                self.nodes[i][j].visited = False
                self.nodes[i][j].parent = None

class Plan:
    def __init__(self, maze):
        self.maze = maze
        self.start = maze.nodes[0][4]
        self.goal = maze.nodes[9][5]
        self.path = self.update_path()
        
    # finds the path from the start node to the goal node
    def update_path(self):
        start = self.start
        goal = self.goal
        open_list = [start]
        start.visited = True
        while open_list:
            current_node = open_list.pop(0)
            if current_node == goal:
                path = []
                while current_node:
                    path.append(current_node)
                    current_node = current_node.parent    
                self.maze.reset_nodes()
                self.path = path[::-1]
                return path[::-1]
            if current_node is not None:
                for child in current_node.children:
                    if not child.visited:
                        child.parent = current_node
                        child.visited = True
                        open_list.append(child)

class Display:
    def __init__(self, frame, maze):
        self.cell_size = int(frame.shape[0]/11)
        self.start_coordinates = (int(frame.shape[1]/2 - len(maze.binary[0]) * self.cell_size/2), int(frame.shape[0]/2 - len(maze.binary) * self.cell_size/2))
        
    def draw_maze(self, frame, maze):
        for i in range(len(maze.binary)):
            for j in range(len(maze.binary[i])):
                cell = maze.binary[i][j]
                x = self.start_coordinates[0] + j * self.cell_size
                y = self.start_coordinates[1] + i * self.cell_size
                maze.nodes[i][j].pixel_coordinates = (int(x + self.cell_size/2), int(y + self.cell_size/2))
                if cell[0] == '1': #Top wall
                    cv2.line(frame, (x, y), (x + self.cell_size, y), (0, 255, 255), 2)
                if cell[1] == '1': #Right wall
                    cv2.line(frame, (x + self.cell_size, y), (x + self.cell_size, y + self.cell_size), (0, 255, 255), 2)
                if cell[2] == '1': #Bottom wall
                    cv2.line(frame, (x, y + self.cell_size), (x + self.cell_size, y + self.cell_size), (0, 255, 255), 2)
                if cell[3] == '1': #Left wall
                    cv2.line(frame, (x, y), (x, y + self.cell_size), (0, 255, 255), 2)
                    
    # detects the aruco markers and sets the start and goal nodes
    def detect_aruco_markers(self, frame, maze, plan, bot):
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters =  cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
        corners, ids, _ = detector.detectMarkers(frame)
        if ids is not None:
            for _ in range(len(ids)):
                cv2.aruco.drawDetectedMarkers(frame, corners, ids, (0, 255, 0))
            for marker_id, corner in zip(ids, corners):
                top_left, top_right, bottom_right, bottom_left = corner[0][0], corner[0][1], corner[0][2], corner[0][3]
                center = (int((top_left[0] + bottom_right[0])/2), int((top_left[1] + bottom_right[1])/2))
                angle = np.arctan2(top_right[1] - top_left[1], top_right[0] - top_left[0]) * 180/np.pi
                u = int((center[0] - self.start_coordinates[0])//(self.cell_size))
                v = int((center[1] - self.start_coordinates[1])//(self.cell_size))
                u=0 if u<0 else u
                v=0 if v<0 else v
                u=9 if u>9 else u
                v=9 if v>9 else v
                if marker_id[0] == 0:
                    bot.update_bot_status(center, angle)
                    plan.start = maze.nodes[v][u]    
                if marker_id[0] == 1:
                    plan.goal = maze.nodes[v][u]

    # draws the path in the frame
    def draw_path(self, frame, plan):
        for i in range(len(plan.path) - 1):
            cv2.line(frame, plan.path[i].pixel_coordinates, plan.path[i + 1].pixel_coordinates, (0, 255, 0), 2)
        return frame
    
class Bot:
    def __init__(self):
        self.position = None
        self.angle = None
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        esp_ip = '192.168.188.116'  # IP of the ESP32
        port = 80
        self.s.connect((esp_ip, port))

    def send_to_esp32(self, message):
        message += '\n'
        self.s.sendall(message.encode())

    def send_movement_commands(self, plan):
            if len(plan.path) < 3:
                print("Game Over")
                return
            if self.position is None or self.angle is None:
                return
            else:
                next_destination = plan.path[1].pixel_coordinates
                target_angle = np.arctan2(next_destination[1] - self.position[1], next_destination[0] - self.position[0]) * 180/np.pi
                angle_difference = target_angle - self.angle
                if angle_difference < -180:
                    angle_difference += 360
                elif angle_difference > 180:
                    angle_difference -= 360
                if abs(angle_difference) < 10:
                    move_command = "forward"
                elif angle_difference < 0:
                    move_command = "left"
                else:
                    move_command = "right"
                self.send_to_esp32(move_command)
                print(f"bot angle: {self.angle}, target_angle: {target_angle}, Sent {move_command}")
                time.sleep(0.5)  

    def update_bot_status(self, position, angle):
        self.position = position
        self.angle = angle
    
if __name__ == "__main__":
    
    cap = cv2.VideoCapture(2)
    
    maze = Maze()
    plan = Plan(maze)
    bot = Bot()
    
    while True:
        ret, frame_rotated = cap.read()
        frame = cv2.rotate(frame_rotated, cv2.ROTATE_180)
        if not ret:
            break

        display = Display(frame, maze)
        display.detect_aruco_markers(frame, maze, plan, bot)
        display.draw_maze(frame, maze)
        plan.update_path()
        display.draw_path(frame, plan)
        bot.send_movement_commands(plan)
        cv2.imshow("Video Feed", frame)
        if cv2.waitKey(1) == ord('q'):
            breakpoint
            
    cap.release()
    cv2.destroyAllWindows()
