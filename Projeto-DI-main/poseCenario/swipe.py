import cv2
import mediapipe as mp
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

start_x = None
swipe_text = ""
text_timer = 0
THRESHOLD = 0.2


while cap.isOpened():
    success, img = cap.read()

    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            index_tip_x = hand_landmarks.landmark[8].x

            if start_x is None:
                start_x = index_tip_x

            diff = index_tip_x - start_x

            if diff > THRESHOLD:
                swipe_text = "SWIPE DIREITA >>"
                text_timer = time.time()
                start_x = index_tip_x
            elif diff < -THRESHOLD:
                swipe_text = "<< SWIPE ESQUERDA"
                text_timer = time.time()
                start_x = index_tip_x

    else:
        start_x = None

    if time.time() - text_timer < 1:
        cv2.putText(img, swipe_text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    cv2.imshow("Detetor de Swipes Simples", img)

cap.release()
cv2.destroyAllWindows()