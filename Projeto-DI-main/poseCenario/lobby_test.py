import arcade
import subprocess
import time
import math
import sys
import os

from colega import PoseTracker

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Lobby - Pose Detection"
MAX_PEOPLE = 5
SMOOTHING_FRAMES = 5

SKELETON_COLORS = [
    (255, 50, 50),
    (50, 150, 255),
    (50, 255, 50),
    (255, 200, 50),
    (200, 50, 255),
]

LOBBY_SLOTS = [
    (0.12, 0.8),
    (0.30, 0.95),
    (0.50, 1.25),
    (0.70, 0.95),
    (0.88, 0.8),
]


class LobbyWindow(arcade.Window):

    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title=SCREEN_TITLE):
        super().__init__(width, height, title, fullscreen=True)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        self.pose_tracker = PoseTracker(max_people=MAX_PEOPLE)
        self.pose_tracker.start()

        self.slot_assignments = {}
        self.last_seen = {}
        self.slot_timeout = 2.0

        self._mouse_down_x = None
        self._mouse_down_y = None
        self.swipe_threshold = 120

        self.gesture_start_time = 0
        self.gesture_hold_duration = 2.0
        self.is_launching = False

        import colega as pv
        self.pose_connections = list(pv.mp.solutions.pose.POSE_CONNECTIONS)

    def draw_skeleton(self, landmarks, position_index, box_x, box_y, box_width, box_height):
        """Desenha esqueleto estilizado dentro de uma caixa."""
        if not landmarks:
            return

        color = SKELETON_COLORS[position_index % len(SKELETON_COLORS)]

        norm_points = []
        for lm in landmarks:
            nx = 1.0 - lm['x']
            ny = 1.0 - lm['y']
            norm_points.append((nx, ny, lm.get('visibility', 1.0)))

        xs = [p[0] for p in norm_points]
        ys = [p[1] for p in norm_points]
        if not xs or not ys:
            return
        min_x = min(xs); max_x = max(xs)
        min_y = min(ys); max_y = max(ys)

        width_norm = max(max_x - min_x, 1e-3)
        height_norm = max(max_y - min_y, 1e-3)

        pad_px = 0.05 * box_width
        pad_py = 0.05 * box_height

        target_left = box_x + pad_px
        target_bottom = box_y + pad_py
        target_width = box_width - 2 * pad_px
        target_height = box_height - 2 * pad_py

        scale = min(target_width / width_norm, target_height / height_norm)

        scaled_w = width_norm * scale
        scaled_h = height_norm * scale

        offset_left = target_left + (target_width - scaled_w) / 2.0
        offset_bottom = target_bottom + (target_height - scaled_h) / 2.0

        points = []
        for nx, ny, vis in norm_points:
            px = offset_left + (nx - min_x) * scale
            py = offset_bottom + (ny - min_y) * scale
            points.append((px, py, vis))

        for idx1, idx2 in self.pose_connections:
            if idx1 < len(points) and idx2 < len(points):
                p1 = points[idx1]; p2 = points[idx2]
                if p1[2] > 0.5 and p2[2] > 0.5:
                    arcade.draw_line(p1[0], p1[1], p2[0], p2[1], color, 4)

        for i, (px, py, vis) in enumerate(points):
            if vis > 0.5:
                if i in [11,12,13,14,15,16,23,24,25,26]:
                    arcade.draw_circle_filled(px, py, 8, color)
                    arcade.draw_circle_outline(px, py, 8, arcade.color.WHITE, 2)
                else:
                    arcade.draw_circle_filled(px, py, 5, color)
                    arcade.draw_circle_outline(px, py, 5, arcade.color.WHITE, 1)
    def on_draw(self):
        self.clear()
        arcade.draw_text("LOBBY - Aguardando Jogadores", self.width/2, self.height-50,
                         arcade.color.WHITE, 32, anchor_x="center", bold=True)
        poses = self.pose_tracker.get_smoothed_poses()

        slots_info = []
        base_y = 0.55
        y_depth_factor = 0.18
        base_box_w = 200
        base_box_h = 400

        centroids = []
        for landmarks in poses:
            vs = [(lm['x'], lm['y'], lm.get('visibility', 1.0)) for lm in landmarks if lm.get('visibility', 1.0) > 0.25]
            if not vs:
                centroids.append(None)
                continue
            avg_x = sum(v[0] for v in vs) / len(vs)
            avg_y = sum(v[1] for v in vs) / len(vs)
            sx = (1.0 - avg_x) * SCREEN_WIDTH
            sy = (1.0 - avg_y) * SCREEN_HEIGHT
            centroids.append((sx, sy))

        for idx, (x_frac, depth_scale) in enumerate(LOBBY_SLOTS):
            pos_x = x_frac * self.width
            pos_y = self.height * (base_y - (depth_scale - 1.0) * y_depth_factor)
            box_width = base_box_w * depth_scale
            box_height = base_box_h * depth_scale
            box_x = pos_x - box_width / 2
            box_y = pos_y - box_height / 2

            assigned_pose = None
            has_player = False
            slots_info.append({
                'idx': idx, 'pos_x': pos_x, 'pos_y': pos_y,
                'box_x': box_x, 'box_y': box_y, 'box_w': box_width, 'box_h': box_height,
                'depth': depth_scale, 'has_player': has_player, 'assigned_pose': assigned_pose
            })

        slot_centers = {s['idx']: (s['pos_x'], s['pos_y']) for s in slots_info}
        taken_slots = set()
        pose_to_slot = {}
        if len(centroids) > 0 and centroids[0] is not None:
            pose_to_slot[0] = 2
            taken_slots.add(2)

        for p_idx in range(1, len(centroids)):
            c = centroids[p_idx]
            if c is None:
                continue
            best = None; best_dist = None
            for s in slots_info:
                sidx = s['idx']
                if sidx in taken_slots:
                    continue
                cx, cy = slot_centers[sidx]
                d = math.hypot(c[0] - cx, c[1] - cy)
                if best is None or d < best_dist:
                    best = sidx; best_dist = d
            if best is not None:
                pose_to_slot[p_idx] = best
                taken_slots.add(best)

        for slot in slots_info:
            assigned = None
            for p_idx, s_idx in pose_to_slot.items():
                if s_idx == slot['idx']:
                    assigned = p_idx; break
            slot['assigned_pose'] = assigned
            slot['has_player'] = assigned is not None

        for slot in sorted(slots_info, key=lambda s: s['depth']):
            if slot['has_player']:
                p_idx = slot['assigned_pose']
                if p_idx is not None and p_idx < len(poses):
                    self.draw_skeleton(poses[p_idx], p_idx, slot['box_x'], slot['box_y'], slot['box_w'], slot['box_h'])

        order = [2, 1, 3, 0, 4]
        slot_label_map = {s_idx: i+1 for i, s_idx in enumerate(order)}

        for slot in slots_info:
            label_num = slot_label_map.get(slot['idx'], None)
            if label_num is not None:
                arcade.draw_text(f"P{label_num}", slot['pos_x'], slot['box_y'] + slot['box_h'] + 10,
                                 arcade.color.WHITE, 18, anchor_x='center', bold=True)
                status_text = "PRONTO" if slot['has_player'] else "AGUARDANDO"
                status_color = arcade.color.GREEN if slot['has_player'] else arcade.color.GRAY
                arcade.draw_text(status_text, slot['pos_x'], slot['box_y'] - 30, status_color, 14, anchor_x='center', bold=True)

        arcade.draw_text(f"Jogadores Detectados: {len(poses)}/{MAX_PEOPLE}", self.width/2, 50, arcade.color.WHITE, 20, anchor_x='center', bold=True)

        swipe_detected, swipe_dir = self.pose_tracker.get_swipe()
        if swipe_detected and not self.is_launching:
            print(f"✋ Swipe detectado: {swipe_dir}")
            self.launch_perspectiva()
            return

        gestures = self.pose_tracker.get_gestures()
        start_gesture_detected = False
        
        for gesture_name, score in gestures:
            if gesture_name in ["ELEVATE_RIGHT", "ELEVATE_LEFT"]:
                start_gesture_detected = True
                break
        
        if start_gesture_detected and not self.is_launching:
            if self.gesture_start_time == 0:
                self.gesture_start_time = time.time()
            
            elapsed = time.time() - self.gesture_start_time
            remaining = max(0, self.gesture_hold_duration - elapsed)
            
            bar_width = 400
            bar_height = 30
            cx = self.width / 2
            cy = self.height / 2
            
            l = cx - bar_width / 2
            r = cx + bar_width / 2
            t = cy + bar_height / 2
            b = cy - bar_height / 2
            arcade.draw_lrbt_rectangle_filled(l, r, b, t, arcade.color.GRAY)
            
            progress = min(1.0, elapsed / self.gesture_hold_duration)
            fill_width = bar_width * progress
            arcade.draw_lrbt_rectangle_filled(l, l + fill_width, b, t, arcade.color.GREEN)
            
            arcade.draw_text(f"A INICIAR EM {remaining:.1f}s...", cx, cy + 40, arcade.color.WHITE, 24, anchor_x='center', bold=True)
            arcade.draw_text("(Mantenha a mão levantada ou faça swipe)", cx, cy - 40, arcade.color.WHITE, 16, anchor_x='center')
            
            if elapsed >= self.gesture_hold_duration:
                self.is_launching = True
                self.launch_perspectiva()
        else:
            self.gesture_start_time = 0

    def on_mouse_press(self, x, y, button, modifiers):
        self._mouse_down_x = x
        self._mouse_down_y = y

    def on_mouse_release(self, x, y, button, modifiers):
        if self._mouse_down_x is None:
            return
        dx = x - self._mouse_down_x
        if abs(dx) > self.swipe_threshold:
            # Treat any horizontal swipe as "launch"
            self.launch_perspectiva()
        self._mouse_down_x = None
        self._mouse_down_y = None

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            self.launch_perspectiva()

    def launch_perspectiva(self):
        poses = self.pose_tracker.get_smoothed_poses()
        player_count = min(len(poses), MAX_PEOPLE)

        print(f"[Lobby] Parando pose tracker, lançando perspectiva com {player_count} jogador(es)")
        
        # Lançar o cenário como processo separado
        script_path = os.path.join(os.path.dirname(__file__), 'colega.py')
        subprocess.Popen(['python', script_path, str(player_count)])
        
        try:
            self.pose_tracker.stop()
        except Exception:
            pass

        # Fechar janela agendando para o próximo frame
        arcade.schedule(lambda dt: arcade.exit(), 0.1)


def main():
    window = LobbyWindow()
    arcade.run()


if __name__ == '__main__':
    main()
