import cv2
from ultralytics import YOLO
import numpy as np
from gtts import gTTS
from playsound import playsound
import tempfile

# Load the YOLO model
model = YOLO("yolov8s-pose.pt")

# Open the webcam
#cap = cv2.VideoCapture(0)
cap = cv2.imread('input_videos/i1.png')
# Define the body part indices
body_index = {"left_knee": 13, "right_knee": 14, "left_ankle": 15, "right_ankle": 16}

# Initialize step count, previouqs positions, and thresholds
step_count = 0
prev_left_ankle_y = None
prev_right_ankle_y = None
step_threshold = 12
min_wait_frames = 8
wait_frames = 0

# Generate the 'Step' audio file
tts = gTTS(text="Step", lang="en")
temp_file = tempfile.NamedTemporaryFile(delete=False)
tts.save(temp_file.name)


results = model(cap, verbose=False, conf=0.5)
annotated_frame = results[0].plot()



            # Round the results to the nearest decimal
            #rounded_results = np.round(results[0].keypoints.numpy(), 1)
rounded_results = np.round(results[0].keypoints.data.numpy())

            # Get the keypoints for the body parts
left_knee = rounded_results[0][body_index["left_knee"]]
right_knee = rounded_results[0][body_index["right_knee"]]
left_ankle = rounded_results[0][body_index["left_ankle"]]
right_ankle = rounded_results[0][body_index["right_ankle"]]
some_point = rounded_results[0][0]



left_knee_x, left_knee_y = int(left_knee[0]), int(left_knee[1])
right_knee_x,right_knee_y = int(right_knee[0]), int(right_knee[1])
some_x,some_y = int(some_point[0]), int(some_point[1])
# Define the color to paint the left knee (in BGR format)
left_knee_color = (0, 255, 0)  # Green color, you can change this to any BGR value
right_knee_color = (255,0,0)
some_color = (0,0,255)

# Draw a circle at the location of the left knee
radius = 5  # Adjust the radius as needed
radius2 = 15
cv2.circle(annotated_frame, (left_knee_x, left_knee_y), radius, left_knee_color, -1)
cv2.circle(annotated_frame, (right_knee_x, right_knee_y), radius, right_knee_color, -1)
cv2.circle(annotated_frame, (some_x,some_y),radius2,some_color,-1)
cv2.imwrite('output_files/annotated_frame2.png', annotated_frame)

print("the fuck is  " ,left_knee)

print("the dfj is ", cap)
print(cap.get(3))