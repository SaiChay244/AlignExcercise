
import cv2
import mediapipe as mp
import math
import time
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


def calculate_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])


    dot_product = ba[0] * bc[0] + ba[1] * bc[1]

    magnitude_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    magnitude_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)

    cosine_angle = dot_product / (magnitude_ba * magnitude_bc)

    angle_radians = math.acos(cosine_angle)
    angle_degrees = math.degrees(angle_radians)

    return angle_degrees

def count_pushups_demo(videoSource):
    counter = 0
    stage = "down"
    reference_wrist = None
    start_time = time.time()
    if isinstance(videoSource, int):
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ret, image = cap.read()
            cv2.imshow('Push-up Counter', image)
            if isinstance(videoSource, int) and time.time() - start_time > 10:
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
    cap = cv2.VideoCapture(videoSource)
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

                shoulder_left = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
                elbow_left = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y]
                wrist_left = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]
                wrist_landmark_left = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
                shoulder_right = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y]
                elbow_right = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x, landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y]
                wrist_right = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y]
                wrist_landmark_right = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]

                if wrist_landmark_left.visibility > 0.5 or wrist_landmark_right.visibility > 0.5: 
                    if wrist_landmark_right.visibility > wrist_landmark_left.visibility:
                        angle = calculate_angle(shoulder_right, elbow_right, wrist_right)
                        if reference_wrist is None:
                            if angle <= 90 and stage == "down":  
                                stage = "up"
                                last_shoulder_y = shoulder_right[1] 
                            elif angle >= 150 and stage == "up" and shoulder_right[1] < last_shoulder_y:  
                                stage = "down"
                                counter += 1 
                                reference_wrist = {'x': abs(wrist_right[0] - wrist_left[0]), 'y': abs(wrist_right[1] - wrist_left[1])}
                        else:
                            if angle <= 90 and stage == "down" and shoulder_right[1] > last_shoulder_y:  
                                stage = "up"
                                last_shoulder_y = shoulder_right[1] 
                            elif angle >= 150 and stage == "up":
                                stage = "down"
                                counter += 1 
                    else:
                        angle = calculate_angle(shoulder_left, elbow_left, wrist_left)
                        if reference_wrist is None:
                            if angle <= 90 and stage == "down":
                                stage = "up"
                                last_shoulder_y = shoulder_left[1]  
                            elif angle >= 150 and stage == "up" and shoulder_left[1] < last_shoulder_y: 
                                stage = "down" 
                                counter += 1 
                                reference_wrist = {'x': abs(wrist_right[0] - wrist_left[0]), 'y': abs(wrist_right[1] - wrist_left[1])}
                        else:
                            if angle <= 90 and stage == "down" and shoulder_left[1] > last_shoulder_y:  
                                stage = "up"
                                last_shoulder_y = shoulder_left[1] 
                            elif angle >= 150 and stage == "up":
                                stage = "down"
                                counter += 1 
                else:
                    print("wrists not visible")


            except:
                pass

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.putText(image, f'Reps: {counter}', (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
            cv2.imshow('Push-up Counter', image)

            if cv2.waitKey(1) & 0xFF == ord('q'):  
                break

    cap.release()
    cv2.destroyAllWindows()
    return counter
