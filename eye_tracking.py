import cv2 
import numpy as np 
import dlib 
from math import hypot
 

cap = cv2.VideoCapture(0) 
detector = dlib.get_frontal_face_detector() 
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

def midpoint(p1, p2): 
    return int((p1.x + p2.x)/2), int((p1.y + p2.y)/2)

# leftx, lefty, rightx, righty 
#def find_points(x, y, x1, x2): 
    #return () 


while True: 
    _, frame = cap.read()
    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #greyscale 
    #change frame = grey if want to use greyscale 
    #frame = grey 

    faces = detector(grey) 
    for face in faces: 
        #print(face) 

        landmarks = predictor(grey, face)

        #right eye -- convert to function so no redundancies -- also can find left eye then 
        left_point = (landmarks.part(36).x, landmarks.part(36).y)
        right_point = (landmarks.part(39).x, landmarks.part(39).y)
        horizontal_line = cv2.line(frame, left_point, right_point, (0, 255, 0), 2)

        center_top = midpoint(landmarks.part(37), landmarks.part(38))
        center_bottom = midpoint(landmarks.part(41), landmarks.part(40))
        vertical_line = cv2.line(frame, center_top, center_bottom, (0, 255, 0), 2)

        #length of lines
        vertical_line_length = hypot((center_top[0] - center_bottom[0]), (center_top[1] - center_bottom[1]))
        horizontal_line_length = hypot((left_point[0] - right_point[0]), (left_point[1] - right_point[1]))
        ratio = horizontal_line_length / vertical_line_length
        # ratio = 5.7 -- detects almost all blinks 

        if ratio > 5.75: 
            cv2.putText(frame, "BLINKING", (100, 150), cv2.FONT_HERSHEY_PLAIN, 6, (0, 255, 0))
        

    cv2.imshow("Frame", frame) 
    key = cv2.waitKey(1)
    if key == 27: 
        break 

cap.release()
cv2.destroyAllWindows() 


