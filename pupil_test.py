# pip install mediapipe opencv-python
import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
draw_utils = mp.solutions.drawing_utils

# indices for iris landmarks (MediaPipe canonical mapping: 468..477 are iris points)
LEFT_IRIS  = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

cap = cv2.VideoCapture(0)
with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,   # important: enables iris landmarks
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as fm:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img.flags.writeable = False
        results = fm.process(img)
        img.flags.writeable = True
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            h, w, _ = img.shape
            # collect iris landmark pixel coords
            left_pts = []
            right_pts = []
            for i, lm in enumerate(face_landmarks.landmark):
                if i in LEFT_IRIS:
                    left_pts.append((int(lm.x * w), int(lm.y * h)))
                if i in RIGHT_IRIS:
                    right_pts.append((int(lm.x * w), int(lm.y * h)))

            if left_pts:
                Lc = np.mean(left_pts, axis=0).astype(int)
                cv2.circle(img, tuple(Lc), 3, (0,255,0), -1)  # left pupil center
            if right_pts:
                Rc = np.mean(right_pts, axis=0).astype(int)
                cv2.circle(img, tuple(Rc), 3, (0,255,0), -1)  # right pupil center

        cv2.imshow('Pupil tracking (MediaPipe)', img)
        if cv2.waitKey(1) & 0xFF == 27:
            break
cap.release()
cv2.destroyAllWindows()
