import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import numpy as np

class PoseDetector:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        
        import os
        import urllib.request
        
        model_path = 'pose_landmarker_full.task'
        if not os.path.exists(model_path):
            print("Baixando modelo full (suporta múltiplas pessoas)...")
            url = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task'
            urllib.request.urlretrieve(url, model_path)
            print("✓ Modelo baixado")
        
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=6,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)
        
        print("✓ MediaPipe PoseLandmarker carregado (modelo FULL - múltiplas pessoas)")
        
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0
        self.people_count = 0
        
    def draw_info_panel(self, frame, status="Ativo"):
        height, width = frame.shape[:2]
        
        info_width = 250
        info_height = 150
        overlay = frame.copy()
        cv2.rectangle(overlay, (width - info_width - 10, 10), 
                     (width - 10, info_height), (255, 255, 255), -1)
        cv2.rectangle(overlay, (width - info_width - 10, 10), 
                     (width - 10, info_height), (0, 0, 0), 2)
        
        alpha = 0.9
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        color = (0, 0, 0)
        x_pos = width - info_width + 5
        
        cv2.putText(frame, f"Status: {status}", (x_pos, 40), 
                   font, font_scale, color, thickness)
        cv2.putText(frame, f"FPS: {self.fps}", (x_pos, 70), 
                   font, font_scale, color, thickness)
        cv2.putText(frame, f"Pessoas: {self.people_count}", (x_pos, 100), 
                   font, font_scale, color, thickness)
        cv2.putText(frame, f"Resolucao: {width}x{height}", (x_pos, 130), 
                   font, font_scale, color, thickness)
        
        return frame
    
    def process_frame(self, frame, timestamp_ms):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        results = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        self.people_count = len(results.pose_landmarks) if results.pose_landmarks else 0
        
        if results.pose_landmarks:
            for person_landmarks in results.pose_landmarks:
                h, w = frame.shape[:2]
                
                connections = self.mp_pose.POSE_CONNECTIONS
                
                for connection in connections:
                    start_idx, end_idx = connection
                    start_point = person_landmarks[start_idx]
                    end_point = person_landmarks[end_idx]
                    
                    start_x = int(start_point.x * w)
                    start_y = int(start_point.y * h)
                    end_x = int(end_point.x * w)
                    end_y = int(end_point.y * h)
                    
                    cv2.line(frame, (start_x, start_y), (end_x, end_y), (0, 0, 0), 2)
                
                for landmark in person_landmarks:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame, (x, y), 4, (0, 0, 0), -1)
        
        return frame
    
    def calculate_fps(self):
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        
        if elapsed_time >= 1.0:
            self.fps = int(self.frame_count / elapsed_time)
            self.frame_count = 0
            self.start_time = time.time()
    
    def run(self):
        print("=" * 50)
        print("Detecao de Pessoas - Webcam")
        print("=" * 50)
        print("\nInicializando webcam...")
        
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            print("ERRO: Não foi possível abrir a webcam!")
            return
        
        time.sleep(0.5)
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        for _ in range(5):
            cap.read()
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Webcam inicializada: {width}x{height}")
        print(f"✓ MediaPipe carregado")
        print("\nPressione 'q' ou 'ESC' para sair")
        print("-" * 50)
        
        try:
            frame_timestamp_ms = 0
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    print("ERRO: Não foi possível ler frame da webcam")
                    break
                
                frame = self.process_frame(frame, frame_timestamp_ms)
                frame_timestamp_ms += 33
                
                self.calculate_fps()
                
                frame = self.draw_info_panel(frame)
                
                cv2.putText(frame, "Detecao de Pessoas - Webcam", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                
                cv2.imshow('Detecao de Pessoas - Webcam', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    print("\nEncerrando...")
                    break
                    
        except KeyboardInterrupt:
            print("\n\nInterrompido pelo utilizador")
        except Exception as e:
            print(f"\nERRO: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.detector.close()
            print("✓ Recursos libertados")
            print("=" * 50)

def main():
    detector = PoseDetector()
    detector.run()

if __name__ == "__main__":
    main()
