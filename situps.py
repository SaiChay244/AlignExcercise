import cv2
import mediapipe as mp
import math

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot_product = ba[0] * bc[0] + ba[1] * bc[1]
    magnitude_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    magnitude_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)
    cosine_angle = dot_product / (magnitude_ba * magnitude_bc)
    cosine_angle = max(-1, min(1, cosine_angle))
    angle = math.degrees(math.acos(cosine_angle))
    return angle

cap = cv2.VideoCapture(0)

counter = 0
stage = "down"

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, image = cap.read()
        if not ret:
            break

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        try:
            landmarks = results.pose_landmarks.landmark
            shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x,
                        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
            hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x,
                   landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y]
            knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
            angle = calculate_angle(shoulder, hip, knee)

            if angle <= 100 and stage == "down":
                stage = "up"
            elif angle >= 160 and stage == "up":
                stage = "down"
                counter += 1

            cv2.putText(image, f'Sit-up Angle: {int(angle)}', (10, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(image, f'Stage: {stage.upper()}', (10, 110), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
        except:
            pass

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.putText(image, f'Sit-ups: {counter}', (10, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Sit-up Counter', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
