# Import necessary libraries
import cv2
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.lang import Builder
from ultralytics import YOLO

# Load the YOLO model
model = YOLO("yolov8s-pose.pt")

# Define the body part indices
body_index = {"left_knee": 13, "right_knee": 14, "left_ankle": 15, "right_ankle": 16}

# Initialize step count, previous positions, and thresholds
step_count = 0
prev_left_ankle_y = None
prev_right_ankle_y = None
step_threshold = 12
min_wait_frames = 8
wait_frames = 0


class CameraApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.image = Image()
        self.layout.add_widget(self.image)

        # Open the webcam
        self.cap = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update, 1.0 / 30.0)
        return self.layout

    def update(self, dt):
        success, frame = self.cap.read()

        if success:
            results = model(frame, verbose=False, conf=0.5)
            annotated_frame = results[0].plot()
            frame_texture = self.convert_frame_to_texture(annotated_frame)
            self.image.texture = frame_texture

            # Round the results to the nearest decimal
            rounded_results = np.round(results[0].keypoints.data.numpy())

            # Get the keypoints for the body parts
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
                            Logger.info(f"Step taken: {step_count}")
                            wait_frames = min_wait_frames

                    prev_left_ankle_y = left_ankle[1]
                    prev_right_ankle_y = right_ankle[1]

                    if wait_frames > 0:
                        wait_frames -= 1

            except:
                Logger.info("No human detected.")

        else:
            Logger.error("Failed to read frame")

    def convert_frame_to_texture(self, frame):
        buffer = cv2.flip(frame, 0).tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
        return texture

    def on_stop(self):
        self.cap.release()


if __name__ == '__main__':
    CameraApp().run()
