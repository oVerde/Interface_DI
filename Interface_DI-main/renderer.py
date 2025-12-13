import cv2
import mediapipe as mp
import time
import numpy as np
import os
from font_manager import FontManager

class Renderer:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_DUPLEX
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Roboto-VariableFont_wdth,wght.ttf')
        self.font_path = font_path if os.path.exists(font_path) else None
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.transition_progress = 0.0
        self.transition_animating = False
        self.transition_start_time = 0
        self.transition_duration = 0.5
        self.last_index = 0
        self.previous_index = 0
        self.arrow_direction = 0
        self.arrow_animation_progress = 0.0
        self.arrow_animation_active = False
        self.arrow_animation_start_time = 0
        self.arrow_animation_duration = 0.6
        self.bg_images = {}
        self.loading_time = time.time()
        self.multiplayer_lobby_state = "WAITING"
        self.multiplayer_players_ready = 0
        self.multiplayer_countdown_start = 0
        self.lobby_state = "WAITING"
        self.lobby_countdown_start = 0
    
    def _put_text_ttf(self, img, text, position, font_size, color, outline=False):
        if self.font_path:
            try:
                x, y = position
                if outline:
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx != 0 or dy != 0:
                                FontManager.put_text(img, text, (x + dx, y + dy), font_size, (0, 0, 0), self.font_path)
                FontManager.put_text(img, text, position, font_size, color, self.font_path)
            except:
                cv2.putText(img, text, position, self.font, 1.0, color, 2)
        else:
            cv2.putText(img, text, position, self.font, 1.0, color, 2)
        return img
    
    def set_backgrounds(self, bg_loader, maps):
        self.bg_loader = bg_loader
        for i in range(len(maps)):
            self.bg_images[i] = bg_loader.get_background(i)
    
    def update_transition(self, current_index, force_reset=False, num_maps=4):
        current_time = time.time()
        if current_index != self.last_index or force_reset:
            self.previous_index = self.last_index
            self.transition_animating = True
            self.transition_start_time = current_time
            forward_distance = (current_index - self.last_index) % num_maps
            backward_distance = (self.last_index - current_index) % num_maps
            self.arrow_direction = 1 if forward_distance <= backward_distance else -1
            self.arrow_animation_active = True
            self.arrow_animation_start_time = current_time
            self.last_index = current_index
        
        if self.transition_animating:
            elapsed = current_time - self.transition_start_time
            progress = min(elapsed / self.transition_duration, 1.0)
            self.transition_progress = 4 * progress ** 3 if progress < 0.5 else 1 - (-2 * progress + 2) ** 3 / 2
            if progress >= 1.0:
                self.transition_animating = False
                self.transition_progress = 1.0
        
        if self.arrow_animation_active:
            elapsed = current_time - self.arrow_animation_start_time
            progress = min(elapsed / self.arrow_animation_duration, 1.0)
            self.arrow_animation_progress = progress
            if progress >= 1.0:
                self.arrow_animation_active = False
                self.arrow_animation_progress = 0.0
    
    def render(self, image, state, maps, current_index, lobby_state=None, lobby_countdown=None, mp_lobby_data=None, pose_landmarks=None, is_locked=False, lobby_obj=None):
        h, w = image.shape[:2]
        if pose_landmarks:
            self._draw_skeleton(image, pose_landmarks, w, h)
        
        if state == "SELECTOR":
            return self._render_selector(image, maps, current_index, w, h, is_locked)
        elif state == "MULTIPLAYER_LOBBY":
            return self._render_multiplayer_lobby(image, maps, current_index, w, h, mp_lobby_data)
        elif state == "LOBBY":
            return self._render_lobby(image, maps, current_index, w, h)
        return image
    
    def _draw_skeleton(self, image, landmarks, w, h):
        connections = [(0, 1), (0, 4), (1, 2), (2, 3), (4, 5), (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
                       (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 25), (24, 26), (23, 24)]
        for start_idx, end_idx in connections:
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start, end = landmarks[start_idx], landmarks[end_idx]
                if start.visibility > 0.3 and end.visibility > 0.3:
                    cv2.line(image, (int(start.x * w), int(start.y * h)), (int(end.x * w), int(end.y * h)), (0, 255, 0), 2)
        for landmark in landmarks:
            if landmark.visibility > 0.3:
                cv2.circle(image, (int(landmark.x * w), int(landmark.y * h)), 4, (255, 0, 0), -1)
    
    def _draw_instructions(self, image, w, h):
        if self.arrow_animation_active and self.arrow_direction == -1:
            pulse = 1.0 + 0.3 * (1 - abs(self.arrow_animation_progress - 0.5) * 2)
            thickness, alpha = max(1, int(3 * pulse)), max(100, int(255 * (1 - self.arrow_animation_progress)))
            overlay = image.copy()
            cv2.arrowedLine(overlay, (70, 35), (30, 35), (255, 255, 0), thickness, tipLength=0.4)
            cv2.addWeighted(overlay, alpha / 255.0, image, 1 - alpha / 255.0, 0, image)
        else:
            cv2.arrowedLine(image, (70, 35), (30, 35), (255, 255, 0), 3, tipLength=0.4)
        
        self._put_text_ttf(image, "Suba o braco esquerdo", (100, 30), 20, (15, 15, 15))
        self._put_text_ttf(image, "para recuar", (100, 48), 20, (15, 15, 15))
        
        if self.arrow_animation_active and self.arrow_direction == 1:
            pulse = 1.0 + 0.3 * (1 - abs(self.arrow_animation_progress - 0.5) * 2)
            thickness, alpha = max(1, int(3 * pulse)), max(100, int(255 * (1 - self.arrow_animation_progress)))
            overlay = image.copy()
            cv2.arrowedLine(overlay, (w - 70, 35), (w - 30, 35), (255, 255, 0), thickness, tipLength=0.4)
            cv2.addWeighted(overlay, alpha / 255.0, image, 1 - alpha / 255.0, 0, image)
        else:
            cv2.arrowedLine(image, (w - 70, 35), (w - 30, 35), (255, 255, 0), 3, tipLength=0.4)
        
        right_x = w - 90 - int(len("Suba o braco direito") * 8) - 20
        self._put_text_ttf(image, "Suba o braco direito", (right_x, 30), 20, (15, 15, 15))
        right_x2 = w - 90 - int(len("para avancar") * 8) - 20
        self._put_text_ttf(image, "para avancar", (right_x2, 48), 20, (15, 15, 15))
    
    def _draw_loading_dots(self, img, x, y, font_size=24):
        elapsed = (time.time() - self.loading_time) * 2.5
        dots = (int(elapsed) % 3) + 1
        text = "." * dots
        self._put_text_ttf(img, text, (x, y), font_size, (255, 255, 0))
    
    def _render_selector(self, img, maps, current_index, w, h, is_locked=False):
        self.update_transition(current_index, num_maps=len(maps))
        current_bg = self.bg_loader.get_background(current_index) if hasattr(self, 'bg_loader') else None
        previous_bg = self.bg_loader.get_background(self.previous_index) if hasattr(self, 'bg_loader') else None
        
        if self.transition_animating and previous_bg is not None and current_bg is not None:
            alpha = self.transition_progress
            carousel_img = cv2.addWeighted(previous_bg, 1 - alpha, current_bg, alpha, 0)
        elif current_bg is not None:
            carousel_img = current_bg.copy()
        else:
            carousel_img = img.copy()
        
        img = carousel_img
        overlay = img.copy()
        overlay[:] = (20, 20, 25)
        img = cv2.addWeighted(overlay, 0.2, img, 0.8, 0)
        
        self._put_text_ttf(img, maps[current_index], (100, h - 170), 100, (255, 255, 255), outline=True)
        cv2.rectangle(img, (0, 0), (w, h), (255, 255, 0), 3)
        
        if is_locked:
            lock_overlay = np.zeros((h, w, 3), dtype=np.uint8)
            lock_overlay[:] = (0, 0, 0)
            img = cv2.addWeighted(img, 0.3, lock_overlay, 0.7, 0)
            locked_text = "BLOQUEADO"
            text_width = len(locked_text) * int(56 * 0.65)
            self._put_text_ttf(img, locked_text, ((w - text_width) // 2, h // 2), 56, (0, 0, 255), outline=True)
        
        self._draw_instructions(img, w, h)
        return img
    
    def _render_multiplayer_lobby(self, img, maps, current_index, w, h, mp_lobby_data):
        overlay = img.copy()
        overlay[:] = (180, 100, 50)
        img = cv2.addWeighted(overlay, 0.4, img, 0.6, 0)
        
        elapsed = (time.time() - self.loading_time) * 2.5
        dots = (int(elapsed) % 3) + 1
        waiting_text = "AGUARDANDO JOGADORES" + "." * dots
        self._put_text_ttf(img, waiting_text, (w//2 - 265, 100), 40, (255, 255, 0), outline=True)
        self._put_text_ttf(img, maps[current_index], (20, h - 30), 30, (255, 255, 255))
        
        confirmed = mp_lobby_data.get('confirmed_players', 0) if mp_lobby_data else 0
        required = 5
        slot_y, slot_size, slot_spacing = 280, 40, 70
        start_x = (w - ((required * slot_spacing - slot_spacing // 2) - 45)) // 2
        
        for i in range(required):
            slot_x = start_x + i * slot_spacing
            cv2.circle(img, (slot_x, slot_y), slot_size // 2, (255, 255, 0) if i < confirmed else (100, 100, 100), -1 if i < confirmed else 2)
        
        player_text = f"{confirmed}/{required} Jogadores"
        text_size = cv2.getTextSize(player_text, self.font, 1.0, 2)[0]
        self._put_text_ttf(img, player_text, (((w - text_size[0]) // 2) + 47, slot_y + 80), 24, (15, 15, 15))
        
        if confirmed < required:
            pass
        else:
            countdown = mp_lobby_data.get('countdown') if mp_lobby_data else None
            status = f"Jogo começa em: {int(countdown) + 1}" if countdown is not None else "Todos prontos!"
            color = (255, 255, 0)
            self._put_text_ttf(img, status, ((w - int(len(status) * 12)) // 2, h // 2 + 150), 24, color)
        
        self._put_text_ttf(img, "Press Backspace to Cancel", (50, h-50), 20, (150, 150, 150))
        self._draw_instructions(img, w, h)
        return img
    
    def _render_lobby(self, img, maps, current_index, w, h):
        overlay = img.copy()
        overlay[:] = (180, 100, 50)
        img = cv2.addWeighted(overlay, 0.4, img, 0.6, 0)
        
        elapsed = time.time() - self.lobby_countdown_start
        countdown = max(0, 3 - int(elapsed))
        
        self._put_text_ttf(img, f"JOGO COMEÇA EM: {countdown}", (w//2 - 300, 100), 48, (255, 255, 0), outline=True)
        self._put_text_ttf(img, maps[current_index], (20, h - 30), 30, (255, 255, 255))
        
        slot_y, slot_size, slot_spacing = 280, 50, 100
        start_x = (w - (5 * slot_spacing - slot_spacing // 2)) // 2
        
        for i in range(5):
            slot_x = start_x + i * slot_spacing
            cv2.circle(img, (slot_x, slot_y), slot_size // 2, (255, 255, 0), -1)
            self._put_text_ttf(img, str(i+1), (slot_x - 10, slot_y + 15), 32, (0, 0, 0))
        
        return img
    
    def render_game(self, image, game_data):
        h, w = image.shape[:2]
        self._put_text_ttf(image, "GAME RUNNING", (w//2 - 150, h//2), 36, (255, 255, 255))
        return image
    
    def init_multiplayer_lobby(self):
        self.multiplayer_lobby_state = "WAITING"
        self.multiplayer_players_ready = 0
        self.multiplayer_countdown_start = 0
    
    def update_multiplayer_lobby(self, event):
        if event == 'SELECT':
            self.multiplayer_players_ready = min(5, self.multiplayer_players_ready + 1)
            if self.multiplayer_players_ready >= 5:
                self.multiplayer_lobby_state = "COUNTDOWN"
                self.multiplayer_countdown_start = time.time()
    
    def set_player_ready(self):
        self.multiplayer_players_ready = min(5, self.multiplayer_players_ready + 1)
        if self.multiplayer_players_ready >= 5:
            self.multiplayer_lobby_state = "COUNTDOWN"
            self.multiplayer_countdown_start = time.time()
    
    def multiplayer_lobby_finished(self):
        if self.multiplayer_lobby_state == "COUNTDOWN":
            elapsed = time.time() - self.multiplayer_countdown_start
            return elapsed >= 3
        return False
    
    def init_lobby(self, map_index):
        self.lobby_state = "COUNTDOWN"
        self.lobby_countdown_start = time.time()
    
    def update_lobby(self):
        if self.lobby_state == "COUNTDOWN":
            elapsed = time.time() - self.lobby_countdown_start
            if elapsed >= 3:
                self.lobby_state = "FINISHED"
    
    def lobby_finished(self):
        return self.lobby_state == "FINISHED"
