import cv2
import numpy as np
import os
from collections import deque
import time
from ultralytics import YOLO




import numpy as np
from gtts import gTTS
from playsound import playsound
import tempfile

from .models import Stats  # Import the Stats model from your models file
from . import db  # Import the database object

# from .models import Stats  # Import the Stats model from your models file
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import create_engine

# # Define the database connection
# engine = create_engine('sqlite:///path_to_your_database.db')
# Session = sessionmaker(bind=engine)

def detect_travel(video_source):
    saving = False  # Initialize saving variable
    # Initialize counters and positions
    dribble_count = 0
    step_count = 0
    prev_x_center = None
    prev_y_center = None
    prev_left_ankle_y = None
    prev_right_ankle_y = None
    prev_delta_y = None
    ball_not_detected_frames = 0
    max_ball_not_detected_frames = 20  # Adjust based on your requirement
    dribble_threshold = 18  # Adjust based on observations
    step_threshold = 5
    min_wait_frames = 7
    wait_frames = 0
    
    travel_timestamp = None
    travel_detected = False
    total_dribble_count=0
    total_step_count=0
    # Define the body part indices
    body_index = {"left_knee": 13, "right_knee": 14, "left_ankle": 15, "right_ankle": 16}
    
    # Define the frame dimensions and fps
    

# Define the codec using VideoWriter_fourcc and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    
    
    # Load the YOLO models
    ball_model = YOLO("website/basketballModel.pt")
    pose_model = YOLO("website/yolov8s-pose.pt")

    if isinstance(video_source, int):
        cap = cv2.VideoCapture(video_source)
    else:
        cap = cv2.VideoCapture(video_source)
    
    # Initialize frame buffer and frame saving settings
    frame_buffer = deque(maxlen=30)  # Buffer to hold frames
    save_frames = 60  # Number of frames to save after travel is detected
    frame_save_counter = 0
    saving = False
    out = None
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Initialize other variables and settings as per the provided code

    #session = Session()  # Create a session object
    
    while cap.isOpened():
        success, frame = cap.read()

        if success:
            
            
            # Process frames and detect travel as per provided code

            # Ball detection
            ball_results_list = ball_model(frame, verbose=False, conf=0.65)

            ball_detected = False

            for results in ball_results_list:
                for bbox in results.boxes.xyxy:
                    x1, y1, x2, y2 = bbox[:4]

                    x_center = (x1 + x2) / 2
                    y_center = (y1 + y2) / 2

                    if prev_y_center is not None:
                        delta_y = y_center - prev_y_center

                        if (
                            prev_delta_y is not None
                            and prev_delta_y > dribble_threshold
                            and delta_y < -dribble_threshold
                        ):
                            dribble_count += 1
                            total_dribble_count += 1

                        prev_delta_y = delta_y

                    prev_x_center = x_center
                    prev_y_center = y_center

                    ball_detected = True
                    ball_not_detected_frames = 0

                annotated_frame = results.plot()

            # Increment the ball not detected counter if ball is not detected
            if not ball_detected:
                ball_not_detected_frames += 1

            # Reset step count if ball is not detected for a prolonged period
            if ball_not_detected_frames >= max_ball_not_detected_frames:
                step_count = 0

            # Pose detection
            pose_results = pose_model(frame, verbose=False, conf=0.5)

            # Round the results to the nearest decimal
            rounded_results = np.round(pose_results[0].keypoints.data.numpy())

            try:
                left_knee = rounded_results[0][body_index["left_knee"]]
                right_knee = rounded_results[0][body_index["right_knee"]]
                left_ankle = rounded_results[0][body_index["left_ankle"]]
                right_ankle = rounded_results[0][body_index["right_ankle"]]

                if (
                    (left_knee[2] > 0.5)
                    and (right_knee[2] > 0.5)
                    and (left_ankle[2] > 0.5)
                    and (right_ankle[2] > 0.5)
                ):
                    if (
                        prev_left_ankle_y is not None
                        and prev_right_ankle_y is not None
                        and wait_frames == 0
                    ):
                        left_diff = abs(left_ankle[1] - prev_left_ankle_y)
                        right_diff = abs(right_ankle[1] - prev_right_ankle_y)

                        if max(left_diff, right_diff) > step_threshold:
                            step_count += 1
                            total_step_count += 1
                            print(f"Step taken: {step_count}")
                            wait_frames = min_wait_frames  # Update wait_frames

                    prev_left_ankle_y = left_ankle[1]
                    prev_right_ankle_y = right_ankle[1]

                    if wait_frames > 0:
                        wait_frames -= 1

            except:
                print("No human detected.")

            pose_annotated_frame = pose_results[0].plot()

            # Combining frames
            combined_frame = cv2.addWeighted(
                annotated_frame, 0.6, pose_annotated_frame, 0.4, 0
            )

            # Drawing counts on the frame
            cv2.putText(
                combined_frame,
                f"Dribble count: {total_dribble_count}",
                (50, 950),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 0),
                4,
                cv2.LINE_AA,
            )

            # Travel detection
            if ball_detected and step_count >= 2 and dribble_count == 0:
                print("Travel detected!")
                step_count = 0  # reset step count
                travel_detected = True
                travel_timestamp = time.time()
                # Start saving frames when travel is detected
                if not saving:
                    # Define the filename based on timestamp
                    
                    filename = os.path.join(
                        "travel_footage",
                        "travel_{}.mp4".format(time.strftime("%Y%m%d-%H%M%S")),
                    )

                    # Create a VideoWriter object
                    out = cv2.VideoWriter(filename, fourcc, 9, (frame_width, frame_height))

                    # Write the buffered frames into the file
                    for f in frame_buffer:
                        out.write(f)

                    saving = True

            if travel_detected and time.time() - travel_timestamp > 3:
                travel_detected = False
                total_dribble_count = 0
                total_step_count = 0

            # Change the tint of the frame and write text if travel was detected
            if travel_detected:
                print("travel detected")
                # Change the tint of the frame to blue
                # Change the tint of the frame to blue
                blue_tint = np.full_like(combined_frame, (255, 0, 0), dtype=np.uint8)
                combined_frame = cv2.addWeighted(combined_frame, 0.7, blue_tint, 0.3, 0)

                 # Write 'Travel Detected!' at the center of the screen
                cv2.putText(
                    combined_frame,
                    "Travel Detected!",
                    (50, 50),  # Adjusted position
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (255, 255, 255),
                    4,
                    cv2.LINE_AA,
                )

            # Reset counts when a dribble is detected
            if dribble_count > 0:
                step_count = 0
                dribble_count = 0
            
               
            # # Update statistical values
            # if dribble_count > 0:
            #     total_dribble_count += 1
            # if travel_detected:
            #     travel_detected_count += 1
            # total_step_count += step_count

            # # Save statistics to the database
            # stats_entry = Stats(
            #     total_dribble_count=total_dribble_count,
            #     travel_detected_count=travel_detected_count,
            #     total_step_count=total_step_count
            # )
            # session.add(stats_entry)
            # session.commit()

            #  # Create an instance of the Stats model with the calculated values
            # stats_entry = Stats(
            #     total_dribble_count=total_dribble_count,
            #     total_step_count=total_step_count,
            #     travel_detected=travel_detected
            #     # Add other relevant statistics here
            # )

            # # Add the instance to the session
            # db.session.add(stats_entry)

            # # Commit the changes to the database
            # db.session.commit()



            # Convert frame to JPEG
            ret, buffer = cv2.imencode('.jpg', combined_frame)
            frame = buffer.tobytes()

            # Convert dribble count and travel detection status to bytes
            # dribble_count_bytes = str(total_dribble_count).encode()
            # travel_detected_bytes = str(travel_detected).encode()
            
            
              # Return frame, dribble count, and travel detection status
            # yield (b'--frame\r\n'
            #        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n' +
            #        b'Dribble Count: ' + str(total_dribble_count) + b'\r\n' +
            #        b'Travel Detected: ' + str(travel_detected) + b'\r\n' +
            #        b'Steps Count: ' + str(total_step_count) + b'r\n');                        # Yield frame, dribble count, and travel detection status
            # yield (b'--frame\r\n'
            #        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n' +
            #        b'Dribble Count: ' + dribble_count_bytes + b'\r\n' +
            #        b'Travel Detected: ' + travel_detected_bytes + b'\r\n')
            
            
           

            yield (b'--frame\r\n'     b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n' )
            # Yield frame and statistical values
            #yield (frame, total_dribble_count, travel_detected, total_step_count)
            #yield (b'--frame\r\n'     b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n' + total_dribble_count,travel_detected, total_step_count )
        else:
            break

    cap.release()
    pass



# def step_counter(video_file): 
#     def get_video_fps(video_file):
#         vcap = cv2.VideoCapture(video_file)
#         fps = vcap.get(cv2.CAP_PROP_FPS)
#         return fps

# # Load the YOLO model
# model = YOLO("yolov8s-pose.pt")

# # Open the webcam
# #cap = cv2.VideoCapture(0)
# cap = cv2.VideoCapture(video_file)

# # Defining the body part indices
# body_index = {"left_knee": 13, "right_knee": 14, "left_ankle": 15, "right_ankle": 16}

# # Initialize step count, previouqs positions, and thresholds
# step_count = 0
# prev_left_ankle_y = None
# prev_right_ankle_y = None
# step_threshold = 12
# min_wait_frames = 8
# wait_frames = 0

# # Generate the 'Step' audio file
# tts = gTTS(text="Step", lang="en")
# temp_file = tempfile.NamedTemporaryFile(delete=False)
# tts.save(temp_file.name)

# while cap.isOpened():
#     success, frame = cap.read()

#     if success:
#         results = model(frame, verbose=False, conf=0.5)
#         annotated_frame = results[0].plot()
#         fps = get_video_fps(video_file)
#         cv2.putText(annotated_frame, str(int(fps)), (100, 100), cv2.FONT_ITALIC, 3, (0, 255, 255), 3)
#         cv2.imshow("YOLOv8 Inference", annotated_frame)

        
#         #rounded_results = np.round(results[0].keypoints.numpy(), 1)
#         rounded_results = np.round(results[0].keypoints.data.numpy())

#         # Get the keypoints for the body parts
#         try:
#             left_knee = rounded_results[0][body_index["left_knee"]]
#             right_knee = rounded_results[0][body_index["right_knee"]]
#             left_ankle = rounded_results[0][body_index["left_ankle"]]
#             right_ankle = rounded_results[0][body_index["right_ankle"]]

#             if (
#                 (left_knee[2] > 0.5)
#                 and (right_knee[2] > 0.5)
#                 and (left_ankle[2] > 0.5)
#                 and (right_ankle[2] > 0.5)
#             ):
#                 if (
#                     prev_left_ankle_y is not None
#                     and prev_right_ankle_y is not None
#                     and wait_frames == 0
#                 ):
#                     left_diff = abs(left_ankle[1] - prev_left_ankle_y)
#                     right_diff = abs(right_ankle[1] - prev_right_ankle_y)

#                     if max(left_diff, right_diff) > step_threshold:
#                         step_count += 1
#                         print(f"Step taken: {step_count}")
#                         wait_frames = min_wait_frames

#                 prev_left_ankle_y = left_ankle[1]
#                 prev_right_ankle_y = right_ankle[1]

#                 if wait_frames > 0:
#                     wait_frames -= 1

#         except:
#             print("No human detected.")

#         if cv2.waitKey(1) & 0xFF == ord("q"):
#             break
#     else:
#         break

# cap.release()
# cv2.destroyAllWindows


