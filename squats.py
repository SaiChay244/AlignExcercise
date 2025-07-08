
import cv2
import mediapipe as mp
import math

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

counter = 0
stage = "down"
reference_hip = None

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

video_file = 0

cap = cv2.VideoCapture(video_file)

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

            hip_left = [landmarks[mp_pose.PoseLandmark.LEFT_HIP].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP].y]
            knee_left = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE].y]
            ankle_left = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y]
            hip_landmark_left = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            hip_right = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y]
            knee_right = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE].y]
            ankle_right = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y] 
            hip_landmark_right = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
 
            squat_position = False

            if hip_landmark_left.visibility > 0.5 or hip_landmark_right.visibility > 0.5:
                if hip_landmark_right.visibility > hip_landmark_left.visibility:
                    angle = calculate_angle(hip_right, knee_right, ankle_right)
                    if reference_hip is None:
                        if angle <= 90 and stage == "down":
                            stage = "up"
                        elif angle >= 150 and stage == "up":
                            stage = "down"
                            counter += 1
                            reference_hip = abs(hip_right[1] - hip_left[1])
                            squat_position = True
                    else:
                        if angle <= 90 and stage == "down" and abs(abs(hip_left[1] - hip_right[1]) - reference_hip) <= 0.05:
                            stage = "up"  
                        elif angle >= 150 and stage == "up":
                            stage = "down"
                            counter += 1
                            squat_position = True
                else:
                    angle = calculate_angle(hip_left, knee_left, ankle_left)
                    if reference_hip is None:
                        if angle <= 90 and stage == "down":
                            stage = "up"
                        elif angle >= 150 and stage == "up":
                            stage = "down"
                            counter += 1
                            reference_hip = abs(hip_right[1] - hip_left[1])
                            squat_position = True
                    else:
                        if angle <= 90 and stage == "down" and abs(abs(hip_left[1] - hip_right[1]) - reference_hip) <= 0.05:
                            stage = "up"
                        elif angle >= 150 and stage == "up":
                            stage = "down"
                            counter += 1
                            squat_position = True
            else:
                print("Hips not visible")

            # Display squat position indicator
            if squat_position:
                cv2.putText(image, "Squat Position: Yes", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(image, "Squat Position: No", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        except:
            pass

        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.putText(image, f'Reps: {counter}', (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
        cv2.imshow('Squat Counter', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
