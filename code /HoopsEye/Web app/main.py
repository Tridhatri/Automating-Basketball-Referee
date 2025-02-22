from fastapi import FastAPI, Response , File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.responses import HTMLResponse
import cv2
from ultralytics import YOLO
import numpy as np
from gtts import gTTS
from playsound import playsound
import tempfile
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import os

app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Welcome to the home page!"}

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

@app.post("/upload")
async def upload_video(request: Request, video_file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as temp_video:
        temp_video.write(video_file.file.read())
        video_path = temp_video.name

    return templates.TemplateResponse("index.html", {"request": request, "video_path": video_path})


@app.get("/video_feed")
async def video_feed(video_path: str = None):
    if video_path:
        cap = cv2.VideoCapture(video_path)
    else:
        cap = cv2.VideoCapture(0)
    # Open the webcam or video file
    #cap = cv2.VideoCapture('v2.mp4')
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

    # Load the YOLO model
    model = YOLO("yolov8s-pose.pt")

    def generate_frames():
        while cap.isOpened():
            success, frame = cap.read()

            if success:
                # Your object detection and processing logic here
                results = model(frame, verbose=False, conf=0.5)
                annotated_frame = results[0].plot()
                #cv2.imshow("YOLOv8 Inference", annotated_frame)
                # Convert frame to JPEG format for streaming
                rounded_results = np.round(results[0].keypoints.data.numpy())
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
                                print(f"Step taken: {step_count}")
                                wait_frames = min_wait_frames

                        prev_left_ankle_y = left_ankle[1]
                        prev_right_ankle_y = right_ankle[1]

                        if wait_frames > 0:
                            wait_frames -= 1

                except:
                    print("No human detected.")
                
               
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            
                ret, jpeg = cv2.imencode('.jpg', annotated_frame)
                frame_bytes = jpeg.tobytes()
                step_info = f"Steps taken: {step_count}".encode()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
                       b'Content-Type: text/plain\r\n\r\n' + step_info + b'\r\n')

                
            else:
                break
    

    #return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
@app.get("/video_feed_stream")
async def video_feed_stream():
    cap = cv2.VideoCapture(0)
    async def generate_frames():
        while cap.isOpened():
            success, frame = cap.read()
            if success:
                ret, jpeg = cv2.imencode('.jpg', frame)
                frame_bytes = jpeg.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                break

    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


