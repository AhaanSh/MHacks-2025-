# pip install mediapipe opencv-python pyautogui
import cv2
import mediapipe as mp
import numpy as np
import pyautogui

mp_face_mesh = mp.solutions.face_mesh

LEFT_IRIS  = [468]  # use only left iris

screen_w, screen_h = pyautogui.size()
cap = cv2.VideoCapture(0)

# Calibration data
calib_cam_x, calib_cam_y = [], []
calib_scr_x, calib_scr_y = [], []

# 5 calibration points (screen)
calib_points = [
    (100, 100, "top-left"),
    (screen_w-100, 100, "top-right"),
    (screen_w-100, screen_h-100, "bottom-right"),
    (100, screen_h-100, "bottom-left"),
    (screen_w//2, screen_h//2, "center")
]

step = 0
frames_collected = 0
frames_per_point = 60
calibrated = False

def get_pupil_center(face_landmarks, w, h):
    L = face_landmarks.landmark[LEFT_IRIS[0]]
    Lc = np.array([L.x * w, L.y * h])
    return Lc.astype(int)

with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True) as fm:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = fm.process(rgb)

        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]
            pupil = get_pupil_center(face, w, h)
            cv2.circle(frame, tuple(pupil), 4, (0,255,0), -1)  # pupil dot

            if not calibrated:
                target_x, target_y, desc = calib_points[step]
                # Move OS cursor to target as guide
                pyautogui.moveTo(target_x, target_y)
                # Show instructions on webcam feed
                cv2.putText(frame,
                            f"Look at {desc} of screen ({step+1}/{len(calib_points)})",
                            (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

                frames_collected += 1
                if frames_collected >= frames_per_point:
                    calib_cam_x.append(pupil[0])
                    calib_cam_y.append(pupil[1])
                    calib_scr_x.append(target_x)
                    calib_scr_y.append(target_y)
                    step += 1
                    frames_collected = 0
                    print(f"Calibration point {step}/{len(calib_points)} collected")

                if step >= len(calib_points):
                    # linear mapping: x and y separately
                    coef_x = np.polyfit(calib_cam_x, calib_scr_x, 1)
                    coef_y = np.polyfit(calib_cam_y, calib_scr_y, 1)
                    calibrated = True
                    print("Calibration done!")

            else:
                # map pupil to screen
                mx = int(np.polyval(coef_x, pupil[0]))
                my = int(np.polyval(coef_y, pupil[1]))
                # constrain to screen bounds
                mx = max(0, min(screen_w-1, mx))
                my = max(0, min(screen_h-1, my))
                pyautogui.moveTo(mx, my)

        cv2.imshow("Pupil Tracking + Calibration", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
