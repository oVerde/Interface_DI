import cv2
import mediapipe as mp
import time

class GestureEngine:
    def __init__(self):
        self.holistic = mp.solutions.holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        self.shoulder_threshold = 0.05
        self.last_trigger_time = 0
        self.cooldown_duration = 0.8
        
    def process_frame(self, image):
        image.flags.writeable = False
        results = self.holistic.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        image.flags.writeable = True
        return results

    def detect_gesture(self, results):
        current_time = time.time()
        if (current_time - self.last_trigger_time) < self.cooldown_duration:
            return None
        if not results.pose_landmarks:
            return None

        landmarks = results.pose_landmarks.landmark
        l_shoulder, r_shoulder = landmarks[11], landmarks[12]
        l_wrist, r_wrist = landmarks[15], landmarks[16]

        if l_wrist.visibility < 0.5 or r_wrist.visibility < 0.5:
            return None

        l_up = l_wrist.y < (l_shoulder.y - self.shoulder_threshold)
        r_up = r_wrist.y < (r_shoulder.y - self.shoulder_threshold)

        if l_up and r_up:
            event = 'SELECT'
        elif l_up:
            event = 'NEXT'
        elif r_up:
            event = 'PREV'
        else:
            return None

        self.last_trigger_time = current_time
        print(f"Gesture: {event}")
        return event