import os
import threading
import time
import random
import urllib.request
import math
from collections import deque

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import arcade

# ------------------------ CONFIGURAÇÕES ------------------------
ACCURACY = 0.04
WIDTH, HEIGHT = 1280, 720
FPS = 60
MAX_PEOPLE = 5

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "img")
MODEL_FILE = os.path.join(SCRIPT_DIR, 'pose_landmarker_full.task')

def ensure_model(path: str):
    if os.path.exists(path):
        return
    url = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task'
    try:
        urllib.request.urlretrieve(url, path)
        print("Modelo descarregado")
    except Exception as e:
        print("ERRO ao descarregar modelo:", e)
        raise

def calculate_angle(a, b, c):
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * (180 / math.pi))
    return angle if angle <= 180 else 360 - angle

def detect_gesture(landmarks):
    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
    LEFT_ELBOW, RIGHT_ELBOW = 13, 14
    LEFT_WRIST, RIGHT_WRIST = 15, 16
    LEFT_HIP, RIGHT_HIP = 23, 24
    LEFT_KNEE, RIGHT_KNEE = 25, 26
    LEFT_ANKLE, RIGHT_ANKLE = 27, 28

    if len(landmarks) <= RIGHT_WRIST:
        return []

    gestures = []

    right_shoulder = [landmarks[RIGHT_SHOULDER].x, landmarks[RIGHT_SHOULDER].y]
    right_elbow = [landmarks[RIGHT_ELBOW].x, landmarks[RIGHT_ELBOW].y]
    right_wrist = [landmarks[RIGHT_WRIST].x, landmarks[RIGHT_WRIST].y]
    angle_r = calculate_angle(right_shoulder, right_elbow, right_wrist)
    height_diff_r = right_shoulder[1] - right_wrist[1]
    if angle_r > 160 and height_diff_r > 0.15:
        gestures.append(("ELEVATE_RIGHT", 17))

    left_shoulder = [landmarks[LEFT_SHOULDER].x, landmarks[LEFT_SHOULDER].y]
    left_elbow = [landmarks[LEFT_ELBOW].x, landmarks[LEFT_ELBOW].y]
    left_wrist = [landmarks[LEFT_WRIST].x, landmarks[LEFT_WRIST].y]
    angle_l = calculate_angle(left_shoulder, left_elbow, left_wrist)
    height_diff_l = left_shoulder[1] - left_wrist[1]
    if angle_l > 160 and height_diff_l > 0.15:
        gestures.append(("ELEVATE_LEFT", 17))

    angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
    y_diff = abs(right_wrist[1] - right_shoulder[1])
    if angle > 160 and y_diff < 0.1:
        gestures.append(("T_STOP_RIGHT", 20))

    angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
    y_diff = abs(left_wrist[1] - left_shoulder[1])
    if angle > 160 and y_diff < 0.1:
        gestures.append(("T_STOP_LEFT", 20))

    angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
    height_diff = right_shoulder[1] - right_wrist[1]
    if 60 < angle < 120 and height_diff > 0.1:
        gestures.append(("WAVE_RIGHT", 10))

    angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
    height_diff = left_shoulder[1] - left_wrist[1]
    if 60 < angle < 120 and height_diff > 0.1:
        gestures.append(("WAVE_LEFT", 10))

    shoulder_distance = abs(landmarks[LEFT_SHOULDER].x - landmarks[RIGHT_SHOULDER].x)
    if shoulder_distance < 0.08:
        gestures.append(("ROTATION", 25))

    right_hip = [landmarks[RIGHT_HIP].x, landmarks[RIGHT_HIP].y]
    right_knee = [landmarks[RIGHT_KNEE].x, landmarks[RIGHT_KNEE].y]
    right_ankle = [landmarks[RIGHT_ANKLE].x, landmarks[RIGHT_ANKLE].y]
    
    knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
    
    if knee_angle < 170:
        gestures.append(("MARCH_RIGHT", 15))

    left_hip = [landmarks[LEFT_HIP].x, landmarks[LEFT_HIP].y]
    left_knee = [landmarks[LEFT_KNEE].x, landmarks[LEFT_KNEE].y]
    left_ankle = [landmarks[LEFT_ANKLE].x, landmarks[LEFT_ANKLE].y]
    
    knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
    
    if knee_angle < 170:
        gestures.append(("MARCH_LEFT", 15))

    return gestures

# ------------------------ POSE TRACKER (THREAD) ------------------------
class PoseTracker:
    """Executa a captura da webcam e processa com MediaPipe PoseLandmarker em background.

    Guarda uma lista de pessoas detectadas em formato: [[(x,y), ...], ...]
    As coordenadas x,y são NORMALIZADAS (0..1), com origem no canto superior-esquerdo.
    """

    def __init__(self, max_people=MAX_PEOPLE):
        ensure_model(MODEL_FILE)

        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

        base_options = BaseOptions(model_asset_path=MODEL_FILE, delegate='GPU')
        options = PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=RunningMode.VIDEO,
            num_poses=MAX_PEOPLE,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.detector = PoseLandmarker.create_from_options(options)

        self.lock = threading.Lock()
        self.people = []
        self.gestures = []
        self.running = False
        self.thread = None
        self.pose_history = [deque(maxlen=5) for _ in range(MAX_PEOPLE)]

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        try:
            self.detector.close()
        except Exception:
            pass

    def _capture_loop(self):
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("ERRO: não foi possível abrir a webcam")
            self.running = False
            return

        timestamp = 0
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.001)   
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            try:
                results = self.detector.detect_for_video(mp_image, timestamp)
            except Exception as e:

                print("Aviso: falha ao processar frame:", e)
                results = None

            timestamp += 33  

            new_people = []
            new_gestures = []
            if results and results.pose_landmarks:
                for i, person in enumerate(results.pose_landmarks):
                    
                    lm_xy = [(lm.x, lm.y) for lm in person]
                    
                    self.pose_history[i].append(lm_xy)
                    
                    if len(self.pose_history[i]) > 0:
                        smoothed_lm = []
                        num_frames = len(self.pose_history[i])
                        for j in range(len(lm_xy)):
                            avg_x = sum(frame[j][0] for frame in self.pose_history[i]) / num_frames
                            avg_y = sum(frame[j][1] for frame in self.pose_history[i]) / num_frames
                            smoothed_lm.append((avg_x, avg_y))
                        new_people.append(smoothed_lm)
                    else:
                        new_people.append(lm_xy)
                    
                    for gesture, score in detect_gesture(person):
                        new_gestures.append((gesture, score))

            with self.lock:
                self.people = new_people
                self.gestures = new_gestures

            time.sleep(0.005)

        cap.release()


def load_texture_safe(path):
    if os.path.exists(path):
        try:
            return arcade.load_texture(path)
        except Exception as e:
            print(f"Erro ao carregar {path}: {e}")
    return arcade.make_soft_square_texture(64, (255, 0, 255), 255)


bg_original = load_texture_safe(os.path.join(IMG_DIR, 'Fundo.jpg'))

imagens_basic = [
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'PUB (2).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'Three1 (2).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'Three2 (2).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'BusStop.png')),
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'Statue1.png')),
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'Statue2.png')),
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'Poster.png')),
    load_texture_safe(os.path.join(IMG_DIR, 'BasicElements', 'PostLamp.png')),
]

imagens_direita = [
    load_texture_safe(os.path.join(IMG_DIR, 'ElementosDir', f'Element_{i}.png'))
    for i in range(1, 5)
]

imagens_esquerda = [
    load_texture_safe(os.path.join(IMG_DIR, 'ElementosEsq', f'Elemento_{i}.png'))
    for i in range(1, 5)
]

imagem_trunfo = load_texture_safe(os.path.join(IMG_DIR, 'ElementsUniqueEsq', 'Trunfo.png'))
imagem_torre = load_texture_safe(os.path.join(IMG_DIR, 'ElementoFixo', 'Torre.png'))

imagens_birds = [
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'birds (1).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'birds (2).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'birds (3).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'birds (4).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'birds (5).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'birds (6).png')),
]

imagem_car_right = load_texture_safe(os.path.join(IMG_DIR, 'animate', 'car_right.png'))
imagem_car_left = load_texture_safe(os.path.join(IMG_DIR, 'animate', 'car_left.png'))

imagens_clouds = [
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'cloud (1).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'cloud (2).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'cloud (3).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'cloud (4).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'cloud (5).png')),
    load_texture_safe(os.path.join(IMG_DIR, 'animate', 'cloud (6).png')),
]


def get_basic_texture():
    rand = random.random()
    if rand < 0.45:  
        return imagens_basic[1]  
    elif rand < 0.45 + 0.45:  
        return imagens_basic[2]  
    elif rand < 0.45 + 0.45 + 0.0167: 
        return imagens_basic[0]  
    elif rand < 0.45 + 0.45 + 0.0167 + 0.0167:
        return imagens_basic[3] 
    elif rand < 0.45 + 0.45 + 0.0167 + 0.0167 + 0.0167: 
        return imagens_basic[4]  
    elif rand < 0.45 + 0.45 + 0.0167 + 0.0167 + 0.0167 + 0.0167:  
        return imagens_basic[5] 
    elif rand < 0.45 + 0.45 + 0.0167 + 0.0167 + 0.0167 + 0.0167 + 0.0167: 
        return imagens_basic[6]
    else: 
        return imagens_basic[7] 

class AnimatedElement:
    def __init__(self, texture, window: arcade.Window):
        self.window = window
        self.texture = texture
        self.sprite = arcade.Sprite()
        self.sprite.texture = texture
        self.t = 0.0
        self.t_raw = 0.0 
        self.active = True
        self.size = 0.0
        self.x = 0
        self.y = 0
        
        from points import get_speed
        self.speed_t = 0.001 * get_speed(ACCURACY)
    
    def ease_out(self, t):
        SLOW_PHASE = 1 
        SLOW_PROGRESS = 0.5  
        
        if t < SLOW_PHASE:
    
            return (t / SLOW_PHASE) * SLOW_PROGRESS
        else:
            
            remaining = (t - SLOW_PHASE) / (1.0 - SLOW_PHASE)
            return SLOW_PROGRESS + remaining * (1.0 - SLOW_PROGRESS)

    @property
    def width(self):
        return self.sprite.texture.width * max(self.size, 0.0001)

    @property
    def height(self):
        return self.sprite.texture.height * max(self.size, 0.0001)

    def update(self, delta_time: float):
        raise NotImplementedError

    def draw(self):
        if not self.active or self.size <= 0.001:
            return
        self.sprite.center_x = self.x
        self.sprite.center_y = self.y
        self.sprite.scale = self.size
        
        alpha = int(min(self.t / 0.0015, 1.0) * 255)
        self.sprite.alpha = alpha
        
        arcade.draw_sprite(self.sprite)


class ElementoFixo(AnimatedElement):
    def __init__(self, window: arcade.Window):
        super().__init__(imagem_torre, window)
        self.max_size_reached = False
        self.pos_inicial_x = 0.5
        self.pos_inicial_y = 0.425
        self.pos_final_x = 0.5
        self.pos_final_y = 0.525
        self.scale_inicial = 0.05
        self.scale_final = 0.25 
        self.size = self.scale_inicial
        from points import get_speed
        self.speed_t = 0.00025 * get_speed(ACCURACY)

    def update(self, delta_time: float):
        if self.max_size_reached:
            return

        self.t += self.speed_t * 1000 * delta_time

        start_x = self.window.width * self.pos_inicial_x
        start_y = self.window.height * self.pos_inicial_y
        end_x = self.window.width * self.pos_final_x
        end_y = self.window.height * self.pos_final_y

        self.x = start_x + (end_x - start_x) * self.t
        self.y = start_y + (end_y - start_y) * self.t
        self.size = self.scale_inicial + (self.scale_final - self.scale_inicial) * self.t

        if self.size >= self.scale_final:
            self.size = self.scale_final
            self.max_size_reached = True
        self.size = self.scale_inicial + (self.scale_final - self.scale_inicial) * self.t
        if self.size >= self.scale_final:
            self.size = self.scale_final
            self.max_size_reached = True


class BasicElement(AnimatedElement):
    def __init__(self, is_left_side: bool, window: arcade.Window):
        texture = get_basic_texture()
        super().__init__(texture, window)
        self.is_left = is_left_side
        
      
        if is_left_side:
           
            self.pos_inicial_x = 0.495
            self.pos_inicial_y = 0.40
            self.pos_final_x = -5
            self.pos_final_y = 0.475 * -1.5
        else:
        
            self.pos_inicial_x = 0.505
            self.pos_inicial_y = 0.40
            self.pos_final_x = 5.5
            self.pos_final_y = 0.475 * -1.5
        
        self.scale_inicial = 0.01
        self.scale_final = 8.275
        self.size = self.scale_inicial
        
        self.x_spread = 0
        
        self.x = window.width * self.pos_inicial_x
        self.y = window.height * self.pos_inicial_y

    def update(self, delta_time: float):
        if not self.active:
            return

        self.t_raw += self.speed_t * 500 * delta_time
        self.t = self.ease_out(min(self.t_raw, 1.0))

        start_x = self.window.width * self.pos_inicial_x
        start_y = self.window.height * self.pos_inicial_y
        end_x = self.window.width * self.pos_final_x
        end_y = self.window.height * self.pos_final_y


        self.x = start_x + (end_x - start_x) * self.t
        self.y = start_y + (end_y - start_y) * self.t
        
        self.x += self.window.width * self.x_spread * self.t
        
        self.size = self.scale_inicial + (self.scale_final - self.scale_inicial) * self.t

        if self.t_raw > 1.5 or self.x < -self.window.width or self.x > self.window.width * 2:
            self.active = False


class ElementoEsquerda(AnimatedElement):
    def __init__(self, window: arcade.Window):
        todas = imagens_esquerda
        texture = random.choice(todas)
        super().__init__(texture, window)
        self.pos_inicial_x = 0.495  
        self.pos_inicial_y = 0.40
        self.pos_final_x = -1.4 * 40 
        self.pos_final_y = 0.475 * -2 
        self.scale_inicial = 0.01
        self.scale_final = 30 
        self.size = self.scale_inicial
       
        self.x_spread = random.uniform(-0.08, 0.08)
        
        self.x = window.width * self.pos_inicial_x
        self.y = window.height * self.pos_inicial_y

    def update(self, delta_time: float):
        if not self.active:
            return

        self.t_raw += self.speed_t * 150 * delta_time
        
        t_linear = min(self.t_raw, 1.0)
       
        self.t = t_linear * (0.1 + 1.2 * t_linear)  

        start_x = self.window.width * self.pos_inicial_x
        start_y = self.window.height * self.pos_inicial_y
        end_x = self.window.width * self.pos_final_x
        end_y = self.window.height * self.pos_final_y

        self.x = start_x + (end_x - start_x) * self.t
        self.y = start_y + (end_y - start_y) * self.t
        
        self.x += self.window.width * self.x_spread * self.t
        
        self.size = self.scale_inicial + (self.scale_final - self.scale_inicial) * self.t

        if t_linear >= 1.0 or self.x < -self.window.width or self.y > self.window.height + 200:
            self.active = False


class ElementoDireita(AnimatedElement):
    def __init__(self, window: arcade.Window):
        texture = random.choice(imagens_direita)
        super().__init__(texture, window)
        self.pos_inicial_x = 0.505
        self.pos_inicial_y = 0.40
        self.pos_final_x = 1.4 * 35
        self.pos_final_y = 0.475 * -2
        self.scale_inicial = 0.01
        self.scale_final = 30
        self.size = self.scale_inicial
        
        self.x_spread = random.uniform(-0.08, 0.08)

    def update(self, delta_time: float):
        if not self.active:
            return

        self.t_raw += self.speed_t * 150 * delta_time
        
        t_linear = min(self.t_raw, 1.0)
       
        self.t = t_linear * (0.1 + 1.2 * t_linear)  
        start_x = self.window.width * self.pos_inicial_x
        start_y = self.window.height * self.pos_inicial_y
        end_x = self.window.width * self.pos_final_x
        end_y = self.window.height * self.pos_final_y

        self.x = start_x + (end_x - start_x) * self.t
        self.y = start_y + (end_y - start_y) * self.t
        
        self.x += self.window.width * self.x_spread * self.t
        
        self.size = self.scale_inicial + (self.scale_final - self.scale_inicial) * self.t

        if t_linear >= 1.0 or self.x > self.window.width + 300 or self.y > self.window.height + 200:
            self.active = False


class BirdAnimation:
    def __init__(self, window: arcade.Window):
        self.window = window
        self.textures = imagens_birds
        self.sprite = arcade.Sprite()
        
        self.current_frame = 0
        self.frame_time = 0
        self.frame_duration = 0.1
        
        self.active = True
        self.direction = random.choice(['left_to_right', 'right_to_left'])
        
        if self.direction == 'left_to_right':
            self.x = -100  
            self.speed = random.uniform(150, 250) 
        else:
            self.x = window.width + 100 
            self.speed = random.uniform(-250, -150)  
        
        self.y = random.uniform(window.height * 0.5, window.height * 0.9)
        
        self.scale = random.uniform(0.15, 0.3)
        
        self.wave_offset = random.uniform(0, math.pi * 2)
        self.wave_amplitude = random.uniform(10, 30)
        self.wave_frequency = random.uniform(2, 4)
        
        self.time_alive = 0
    
    def update(self, delta_time: float):
        if not self.active:
            return
        
        self.time_alive += delta_time
        
        self.frame_time += delta_time
        if self.frame_time >= self.frame_duration:
            self.frame_time = 0
            self.current_frame = (self.current_frame + 1) % len(self.textures)
        
        self.x += self.speed * delta_time
        
        wave = math.sin(self.time_alive * self.wave_frequency + self.wave_offset) * self.wave_amplitude
        self.y += wave * delta_time
        

        if self.direction == 'left_to_right':
            if self.x > self.window.width + 100:
                self.active = False
        else:
            if self.x < -100:
                self.active = False
    
    def draw(self):
        if not self.active:
            return
        
        self.sprite.texture = self.textures[self.current_frame]
        self.sprite.center_x = self.x
        self.sprite.center_y = self.y
        self.sprite.scale = self.scale
        
        if self.direction == 'right_to_left':
            self.sprite.angle = 0
        
            arcade.draw_sprite(self.sprite, pixelated=False)
        else:
            arcade.draw_sprite(self.sprite)


class CarAnimation:
    def __init__(self, window: arcade.Window):
        self.window = window
        self.direction = random.choice(['left_to_right', 'right_to_left'])
        if self.direction == 'left_to_right':
            self.texture = imagem_car_right
        else:
            self.texture = imagem_car_left
        self.sprite = arcade.Sprite()
        self.sprite.texture = self.texture

        self.active = True

        self.y = window.height * 0.42

        self.start_x = window.width * 0.5 
        self.end_x = window.width * 0.55 

        if self.direction == 'left_to_right':
            self.x = self.start_x - 100
            self.speed = random.uniform(200, 300)
        else:
            self.x = self.end_x + 100
            self.speed = random.uniform(-300, -200)

        self.scale = random.uniform(0.08, 0.12)
    
    def update(self, delta_time: float):
        if not self.active:
            return
        
        self.x += self.speed * delta_time
        
        if self.direction == 'left_to_right':
            if self.x > self.end_x + 100:
                self.active = False
        else:
            if self.x < self.start_x - 100:
                self.active = False
    
    def draw(self):
        if not self.active:
            return
        self.sprite.center_x = self.x
        self.sprite.center_y = self.y
        self.sprite.scale = self.scale
        self.sprite.angle = 0
        self.sprite.texture = self.texture
        self.sprite.flip_horizontal = False
        arcade.draw_sprite(self.sprite)


class CloudAnimation:
    """Animação de nuvens que se movem lentamente pelo céu."""
    def __init__(self, window: arcade.Window, accuracy: float):
        self.window = window
        
        self.texture = random.choice(imagens_clouds)
        self.sprite = arcade.Sprite()
        self.sprite.texture = self.texture
        
        self.active = True
        self.direction = random.choice(['left_to_right', 'right_to_left'])
        
        if self.direction == 'left_to_right':
            self.x = -200
            
            base_speed = random.uniform(15, 30)
            self.speed = base_speed * (1 + accuracy * 0.3) 
            self.x = window.width + 200
            base_speed = random.uniform(-30, -15)
            self.speed = base_speed * (1 + accuracy * 0.3)
        

        self.y = random.uniform(window.height * 0.5, window.height * 0.95)
        self.scale = random.uniform(0.3, 0.6)
        self.alpha = random.randint(80, 150) 
    
    def update(self, delta_time: float):
        if not self.active:
            return
        
        self.x += self.speed * delta_time
        
        if self.direction == 'left_to_right':
            if self.x > self.window.width + 200:
                self.active = False
        else:
            if self.x < -200:
                self.active = False
    
    def draw(self):
        if not self.active:
            return
        
        self.sprite.center_x = self.x
        self.sprite.center_y = self.y
        self.sprite.scale = self.scale
        self.sprite.alpha = self.alpha
        arcade.draw_sprite(self.sprite)


GRID_ROWS = 1
GRID_COLS = 5
MAX_PEOPLE = 5

def get_grid_boxes(grid_x0, grid_y0, grid_width, grid_height):
    box_width = grid_width / GRID_COLS
    box_height = grid_height / GRID_ROWS

    boxes = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x1 = grid_x0 + c * box_width
            y1 = grid_y0 + r * box_height
            x2 = x1 + box_width
            y2 = y1 + box_height
            boxes.append((x1, y1, x2, y2))
    return boxes

def normalize_points_to_box(points, box):
    if not points:
        return []
    
    x1, y1, x2, y2 = box
    box_w = x2 - x1
    box_h = y2 - y1
    
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    body_w = max_x - min_x
    body_h = max_y - min_y
    
    if body_w < 0.01:
        body_w = 0.01
    if body_h < 0.01:
        body_h = 0.01
    
    scale_x = (box_w * 0.9) / body_w
    scale_y = (box_h * 0.9) / body_h
    scale = min(scale_x, scale_y)
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    box_center_x = x1 + box_w / 2
    box_center_y = y1 + box_h / 2
    
    fixed_points = []
    for (x, y) in points:
        rel_x = (x - center_x) * scale
        rel_y = (y - center_y) * scale
        
        nx = box_center_x + rel_x
        ny = box_center_y - rel_y
        
        fixed_points.append((nx, ny))
    return fixed_points

def apply_points_to_scene(self, score):
    if not score:
        return

    px, py = score[0]
    dx = (px - 0.5) * 50  
    dy = (py - 0.5) * 50  

    
    for elemento in self.elementos:
        elemento.x += dx
        elemento.y += dy

   
    self.elemento_fixo.x += dx
    self.elemento_fixo.y += dy

def on_update(self, delta_time: float):
    
    with self.pose.lock:
        people = list(self.pose.people)

    if people:
        first_person_points = people[0]
        self.apply_points_to_scene(first_person_points)

    for elemento in self.elementos:
        elemento.update(delta_time)
    self.elemento_fixo.update(delta_time)    

WAVE_FRAMES = [arcade.load_texture(os.path.join(IMG_DIR, 'gestures', f'wave ({i}).png')) for i in range(1, 20)]
WAVE_ANIMATION_DURATION = 7.0 
WAVE_FRAME_TIME = 0.06


WALK_FRAMES = [arcade.load_texture(os.path.join(IMG_DIR, 'gestures', f'walk ({i}).png')) for i in range(1, 10)]

class PerspectivaWindow(arcade.Window):
    def __init__(self, width, height, title="Perspectiva Python com Pose"):
        super().__init__(width, height, title, resizable=True)
        arcade.set_background_color(arcade.color.BLACK)

        self.elementos = []
        self.elemento_fixo = ElementoFixo(self)
        
        self.birds = []
        self.last_bird_milestone = 0  
        self.bird_milestone_interval = 10000  
        
        
        self.cars = []
        self.last_car_milestone = 0
        self.car_milestone_interval = 5000  
        
        self.clouds = []
        self.last_cloud_spawn = 0
        self.next_cloud_interval = random.uniform(8000, 15000)  

        self.count_left = 0
        self.count_right = 0
        self.count_basic = 0

        self.MAX_ARVORES_POR_EIXO = 40
        self.MAX_BASIC_ELEMENTS = 15

        self.last_spawn_left = 0
        self.last_spawn_right = 0
    
        self.last_spawn_basic_left = 0
        self.last_spawn_basic_right = 0

        self.base_speed = 150 
        
        self.interval_left = int(self.base_speed * 30)  
        self.interval_right = int(self.base_speed * 30)
        
        self.interval_basic_base = int(self.base_speed * 35)  
        self.interval_basic_left = self.interval_basic_base + random.randint(200, 400)
        self.interval_basic_right = self.interval_basic_base + random.randint(200, 400)

        self.bg_texture = bg_original
        self.bg_sprite = arcade.Sprite()
        self.bg_sprite.texture = self.bg_texture
        self.update_background_sprite()

        self.pose = PoseTracker(max_people=MAX_PEOPLE)
        self.pose.start()

    
        self.accuracy = ACCURACY
        self.total_score = 0

        
        self.recent_score = 0
        
        
        self.game_start_time = time.time()
        
        self.last_message_milestone = 0
        self.message_milestone_interval = 20000
        self.motivational_message = ""
        self.message_display_time = 0
        self.message_duration = 4.0 
        
        
        self.motivational_messages = [
            "Estás a ir bem! Parabéns!",
            "Ótimo esforço!",
            "É isso, sempre a mexer!",
            "Continua assim!",
            "Excelente trabalho!",
            "Fantástico! Não pares!",
            "Que ritmo incrível!",
            "Imparável! Continua!",
            "Tu consegues!",
        ]
        
        self.time_without_score = 0
        self.show_gesture_tips = False
       
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0

        self.person_assignments = {} 
        self.next_person_id = 0
        
        self.exit_gesture_time = 0.0 
        self.exit_gesture_active = False  
       
        self.show_wave_intro = True
        self.wave_intro_time = 0.0
        self.wave_intro_frame = 0
       
        self.inactive_tip_variant = 0  
        self.inactive_tip_frame = 0
        self.inactive_tip_time = 0.0

    def update_background_sprite(self):
        self.bg_texture = bg_original
        self.bg_sprite = arcade.Sprite()
        self.bg_sprite.texture = self.bg_texture
        scale_x = self.width / self.bg_texture.width
        scale_y = self.height / self.bg_texture.height
        self.bg_sprite.scale = max(scale_x, scale_y)

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.update_background_sprite()
        for elemento in self.elementos:
            if elemento.active:
                start_x = self.width * elemento.pos_inicial_x
                start_y = self.height * elemento.pos_inicial_y
                end_x = self.width * elemento.pos_final_x
                end_y = self.height * elemento.pos_final_y
                elemento.x = start_x + (end_x - start_x) * elemento.t
                elemento.y = start_y + (end_y - start_y) * elemento.t
        start_x = self.width * self.elemento_fixo.pos_inicial_x
        start_y = self.height * self.elemento_fixo.pos_inicial_y
        end_x = self.width * self.elemento_fixo.pos_final_x
        end_y = self.height * self.elemento_fixo.pos_final_y
        self.elemento_fixo.x = start_x + (end_x - start_x) * self.elemento_fixo.t
        self.elemento_fixo.y = start_y + (end_y - start_y) * self.elemento_fixo.t

    def apply_points_to_scene(self, points, gestures):
        pass

    def on_draw(self):
        self.clear()
        
        rect = arcade.LBWH(0, 0, self.width, self.height)
        arcade.draw_texture_rect(self.bg_texture, rect)
        
        if self.show_wave_intro:
            frame = WAVE_FRAMES[self.wave_intro_frame % len(WAVE_FRAMES)]
            sprite = arcade.Sprite()
            sprite.texture = frame
            
            sprite.center_x = int(self.width * 0.22)
            sprite.center_y = int(self.height * 0.28)
            sprite.scale = 0.60
            arcade.draw_sprite(sprite)
            
            msg_lines = [
                "Olá!",
                "Experimente mover-se,",
                "sem sair do lugar,",
                "para avançar e descobrir mais!"
            ]
            font_size = 38
            
            x = self.width * 0.38
            y = self.height * 0.50
            for i, line in enumerate(msg_lines):
                arcade.draw_text(
                    line,
                    x, y - i * (font_size + 8),
                    arcade.color.BLACK,
                    font_size,
                    anchor_x="left",
                    anchor_y="center",
                    bold=True
                )
            return  

        self.birds = [b for b in self.birds if b.active]
        for bird in self.birds:
            bird.draw()

        
        self.elementos = [e for e in self.elementos if e.active]
        self.elementos.sort(key=lambda e: e.size)
        for elemento in self.elementos:
            elemento.draw()

    
        with self.pose.lock:
            people = list(self.pose.people)

        grid_width  = self.width * 0.9
        grid_height = self.height * 0.4
        grid_x0 = (self.width - grid_width) / 2
        grid_y0 = 10  

        boxes = get_grid_boxes(grid_x0, grid_y0, grid_width, grid_height)

        for box in boxes:
            x1, y1, x2, y2 = box
            arcade.draw_lrbt_rectangle_outline(left=x1, right=x2, bottom=y1, top=y2,
                                            color=arcade.color.RED, border_width=2)

       
        with self.pose.lock:
            people = list(self.pose.people)
            gestures = list(self.pose.gestures)

        
        assigned_boxes = self.assign_people_to_boxes(people, boxes)

        for person_idx, box_idx in assigned_boxes.items():
            if person_idx >= len(people) or box_idx >= len(boxes):
                continue
            person = people[person_idx]
            box = boxes[box_idx]
            adjusted = normalize_points_to_box(person, box)
            gesture, score = gestures[person_idx] if person_idx < len(gestures) else (None, 0)
            color = arcade.color.GREEN if gesture else arcade.color.RED
            self.draw_skeleton(adjusted, color=color)
            
            
            if gesture:
                x1, y1, x2, y2 = box
                text_x = (x1 + x2) / 2
                text_y = y2 + 15
                arcade.draw_text(gesture, text_x, text_y, arcade.color.BLACK, 24, 
                               anchor_x="center", bold=True)
        
      
        elapsed_time = time.time() - self.game_start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        
        panel_x = 20
        panel_y = self.height - 30
        line_height = 35
        
        
        top = max(panel_y + 25, panel_y - 5)
        bottom = min(panel_y + 25, panel_y - 5)
        arcade.draw_lrbt_rectangle_filled(panel_x - 5, panel_x + 200, bottom, top, (0, 0, 0, 180))
        
        arcade.draw_text(f"Tempo: {minutes:02d}:{seconds:02d}", 
                        panel_x, panel_y, arcade.color.WHITE, 22, bold=True)
        
        
        display_score = self.total_score // 30
        top2 = max(panel_y - line_height + 25, panel_y - line_height - 5)
        bottom2 = min(panel_y - line_height + 25, panel_y - line_height - 5)
        arcade.draw_lrbt_rectangle_filled(panel_x - 5, panel_x + 200, bottom2, top2, (0, 0, 0, 180))
        
        arcade.draw_text(f"Pontos: {display_score}", 
                        panel_x, panel_y - line_height, arcade.color.WHITE, 22, bold=True)
        
        
        if self.message_display_time > 0:
            
            msg_x = self.width / 2
            msg_y = self.height - 180  
            arcade.draw_text(
                self.motivational_message,
                msg_x,
                msg_y,
                arcade.color.BLACK,
                40,  
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
        
        
        if self.show_gesture_tips:
           
            if self.inactive_tip_variant % 2 == 0:
                # Wave
                tip_frames = WAVE_FRAMES
                tip_msg = "Tente mover os braços!"
            else:
                # Walk
                tip_frames = WALK_FRAMES
                tip_msg = "Tente marchar no lugar!"
            frame = tip_frames[self.inactive_tip_frame % len(tip_frames)]
            sprite = arcade.Sprite()
            sprite.texture = frame
            sprite.center_x = int(self.width * 0.22)
            sprite.center_y = int(self.height * 0.28)
            sprite.scale = 0.60
            arcade.draw_sprite(sprite)
            font_size = 34
            x = self.width * 0.38
            y = self.height * 0.40
            arcade.draw_text(
                tip_msg,
                x, y,
                arcade.color.BLACK,
                font_size,
                anchor_x="left",
                anchor_y="center",
                bold=True
            )
            return  
        
        
        if self.exit_gesture_active and self.exit_gesture_time > 0:
            countdown = int(5.0 - self.exit_gesture_time)
            countdown_text = f"Gesto de saída reconhecido, terminar em {countdown}s"
            
            
            arcade.draw_lrbt_rectangle_filled(
                0, self.width, 
                self.height - 120, self.height,
                (200, 0, 0, 200)
            )
            
            
            arcade.draw_text(
                countdown_text,
                self.width / 2,
                self.height - 60,
                arcade.color.WHITE,
                25,  
                anchor_x="center",
                anchor_y="center",
                bold=True
            )

    def assign_people_to_boxes(self, people, boxes):
        if not people:
            return {}
        
        
        person_centers = []
        for person in people:
            if len(person) > 0:
                avg_x = sum(p[0] for p in person) / len(person)
                avg_y = sum(p[1] for p in person) / len(person)
                person_centers.append((avg_x, avg_y))
            else:
                person_centers.append((0.5, 0.5))
        
        
        box_centers = []
        for box in boxes:
            x1, y1, x2, y2 = box
            center_x = (x1 + x2) / (2 * self.width)
            center_y = (y1 + y2) / (2 * self.height)
            box_centers.append((center_x, center_y))
        
       
        distances = {}
        for p_idx, p_center in enumerate(person_centers):
            for b_idx, b_center in enumerate(box_centers):
                dx = p_center[0] - b_center[0]
                dy = p_center[1] - b_center[1]
                dist = (dx * dx + dy * dy) ** 0.5
                distances[(p_idx, b_idx)] = dist
        
        
        assigned_boxes = {}
        used_boxes = set()
        
       
        for person_id, prev_box_idx in list(self.person_assignments.items()):
            if person_id < len(people) and prev_box_idx < len(boxes):
                if prev_box_idx not in used_boxes:
                   
                    if (person_id, prev_box_idx) in distances and distances[(person_id, prev_box_idx)] < 0.3:
                        assigned_boxes[person_id] = prev_box_idx
                        used_boxes.add(prev_box_idx)
        
        
        for p_idx in range(len(people)):
            if p_idx not in assigned_boxes:
                best_box = None
                best_dist = float('inf')
                for b_idx in range(len(boxes)):
                    if b_idx not in used_boxes:
                        dist = distances.get((p_idx, b_idx), float('inf'))
                        if dist < best_dist:
                            best_dist = dist
                            best_box = b_idx
                if best_box is not None:
                    assigned_boxes[p_idx] = best_box
                    used_boxes.add(best_box)
        
      
        self.person_assignments = assigned_boxes.copy()
        
        return assigned_boxes

    def draw_skeleton(self, person, color=arcade.color.RED):
        connections = mp.solutions.pose.POSE_CONNECTIONS
        
        for a, b in connections:
            try:
                p1 = person[a]
                p2 = person[b]
            except Exception:
                continue
            x1, y1 = p1
            x2, y2 = p2
            arcade.draw_line(x1, y1, x2, y2, color, 2)

        
        for x, y in person:
            arcade.draw_circle_filled(x, y, 4, arcade.color.BLACK)
            arcade.draw_circle_outline(x, y, 4, color, 1)

    def on_update(self, delta_time: float):
        
        if self.show_wave_intro:
            self.wave_intro_time += delta_time
            if self.wave_intro_time >= WAVE_ANIMATION_DURATION:
                self.show_wave_intro = False
            else:
                self.wave_intro_frame = int(self.wave_intro_time / WAVE_FRAME_TIME) % len(WAVE_FRAMES)
            return  

        
        with self.pose.lock:
            people = list(self.pose.people)
            gestures = list(self.pose.gestures)

        
        self.recent_score = 0
        for gesture, score in gestures:
            if gesture:
                self.total_score += score
                self.accuracy = min(1.0, self.accuracy + score * 0.01)
                self.recent_score += score  

        
        elevate_right = False
        elevate_left = False
        for gesture, score in gestures:
            if gesture == "ELEVATE_RIGHT" and score >= 17:
                elevate_right = True
            if gesture == "ELEVATE_LEFT" and score >= 17:
                elevate_left = True
        
       
        if elevate_right and elevate_left:
            self.exit_gesture_active = True
            self.exit_gesture_time += delta_time
            
           
            if self.exit_gesture_time >= 5.0:
                print("Gesto de saída confirmado: fechando sistema...")
                self.pose.stop()
                arcade.close_window()
        else:
            
            self.exit_gesture_active = False
            self.exit_gesture_time = 0.0
        
       
        current_message_milestone = (self.total_score // self.message_milestone_interval) * self.message_milestone_interval
        if current_message_milestone > self.last_message_milestone and current_message_milestone > 0:
            self.motivational_message = random.choice(self.motivational_messages)
            self.message_display_time = self.message_duration
            self.last_message_milestone = current_message_milestone
        
        
        if self.message_display_time > 0:
            self.message_display_time -= delta_time
        
        
        if self.recent_score > 0:
            self.time_without_score = 0
            self.show_gesture_tips = False
            self.inactive_tip_time = 0.0
            self.inactive_tip_frame = 0
        else:
            self.time_without_score += delta_time
            if self.time_without_score > 5.0:
                if not self.show_gesture_tips:
                    self.inactive_tip_variant += 1  
                    self.inactive_tip_time = 0.0
                    self.inactive_tip_frame = 0
                self.show_gesture_tips = True
                
                self.inactive_tip_time += delta_time
                frame_duration = 0.08
                if self.inactive_tip_time >= frame_duration:
                    self.inactive_tip_frame += 1
                    self.inactive_tip_time = 0.0
            else:
                self.show_gesture_tips = False

        
        for bird in self.birds:
            bird.update(delta_time)
        
        
        dt_ms = delta_time * 1000
        for cloud in self.clouds:
            cloud.update(delta_time)
        
        
        self.last_cloud_spawn += dt_ms
        if self.last_cloud_spawn >= self.next_cloud_interval:
            
            self.clouds.append(CloudAnimation(window=self, accuracy=self.accuracy))
            self.last_cloud_spawn = 0
            self.next_cloud_interval = random.uniform(8000, 15000)  
        
        current_bird_milestone = (self.total_score // self.bird_milestone_interval) * self.bird_milestone_interval
        if current_bird_milestone > self.last_bird_milestone and current_bird_milestone > 0:
            
            num_birds = random.randint(2, 4)
            for _ in range(num_birds):
                self.birds.append(BirdAnimation(window=self))
            self.last_bird_milestone = current_bird_milestone
            
        
        for car in self.cars:
            car.update(delta_time)
        
        current_car_milestone = (self.total_score // self.car_milestone_interval) * self.car_milestone_interval
        if current_car_milestone > self.last_car_milestone and current_car_milestone > 0:
            
            self.cars.append(CarAnimation(window=self))
            self.last_car_milestone = current_car_milestone
            
        
        if self.recent_score > 0:
            dt_ms = delta_time * 1000
            
            
            self.last_spawn_basic_left += dt_ms
            if self.last_spawn_basic_left >= self.interval_basic_left:
                self.elementos.append(BasicElement(is_left_side=True, window=self))
                self.last_spawn_basic_left = 0
                
                self.interval_basic_left = self.interval_basic_base + random.randint(200, 400)

            
            self.last_spawn_basic_right += dt_ms
            if self.last_spawn_basic_right >= self.interval_basic_right:
                self.elementos.append(BasicElement(is_left_side=False, window=self))
                self.last_spawn_basic_right = 0
               
                self.interval_basic_right = self.interval_basic_base + random.randint(200, 400)

            
            self.last_spawn_left += dt_ms
            if self.last_spawn_left >= self.interval_left:
                self.elementos.append(ElementoEsquerda(window=self))
                self.last_spawn_left = 0

            
            self.last_spawn_right += dt_ms
            if self.last_spawn_right >= self.interval_right:
                self.elementos.append(ElementoDireita(window=self))
                self.last_spawn_right = 0

           
            for elemento in self.elementos:
                elemento.update(delta_time)
            self.elemento_fixo.update(delta_time)
        
        

        
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        if elapsed >= 1.0:
            self.fps = int(self.frame_count / elapsed)
            self.frame_count = 0
            self.start_time = time.time()

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            
            self.pose.stop()
            arcade.close_window()

    def on_close(self):
       
        try:
            self.pose.stop()
        except Exception:
            pass
        super().on_close()


def main():
    window = PerspectivaWindow(WIDTH, HEIGHT)
    arcade.run()


if __name__ == '__main__':
    main()