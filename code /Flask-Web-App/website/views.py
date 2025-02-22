from flask import Blueprint, render_template, request, flash, jsonify,redirect, session, url_for, Response
from flask_login import login_required, current_user
from .models import Note, User
from .utils import detect_travel
from . import db
import json

import cv2
from ultralytics import YOLO
import numpy as np
import tempfile
from collections import deque
import os
import time

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        option = request.form.get('option')
        print("Option selected:", option)
        if option == 'referee_game':
            # Redirect to the video_feed page for referee game
            return redirect(url_for('views.choose_file_upload'))
        elif option == 'train_player':
            # Redirect to the video_feed page for player training
            return redirect(url_for('views.choose_file_upload'))
        else:
            print("Invalid option:", option)

    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

# @views.route('/video-feed')
# @login_required
# def video_feed():
#     return render_template("video_feed.html", user=current_user)

# @views.route('/video-processing', methods=['GET'])
# @login_required
# def video_processing():
#     video_source = request.args.get('video_source')
#     return render_template("video_processing.html", user=current_user, video_source=video_source)



# @views.route('/video-feed', methods=['GET'])
# @login_required
# def video_feed():
#     # Render the video_feed.html template
#     return render_template("video_feed.html", user=current_user)

# # Route for processing the selected video source
# @views.route('/process-video', methods=['POST'])
# @login_required
# def process_video():
#     # Get the chosen video source from the request data
#     video_source = request.json.get('videoSource')

#     # Start processing the video using the chosen video source
#     result = detect_travel(video_source)
#     print(type(result))
#     response = Response(generate_frames(result), mimetype='multipart/x-mixed-replace; boundary=frame')
#      # Debugging: Print the content of the blob
#     #print(response.get_data())  # This will print the content of the blob to the console

#     # Return a response with the processed video frames
#     return Response(generate_frames(result), mimetype='multipart/x-mixed-replace; boundary=frame')

# def generate_frames(result):
#     # Generator function to convert each frame to bytes and yield them
#     for frame in result:
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@views.route('/video-feed', methods=['GET'])
@login_required
def video_feed():
    return render_template("video_feed.html", user=current_user)

# @views.route('/output_video')
# def output_video():
#     def generate_frames():
#         video_source =  request.json.get('videoSource') # Or provide your video source here
#         for frame in detect_travel(video_source):
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')




@views.route('/upload-video', methods=['POST'])
@login_required
def upload_video():
    if 'video_file' not in request.files:
        return redirect(request.url)
    file = request.files['video_file']
    if file.filename == '':
        return redirect(request.url)
    # Save the uploaded file to a temporary location
    temp_file_path = os.path.join(tempfile.gettempdir(), file.filename)
    file.save(temp_file_path)
    # Redirect to the video feed route with the uploaded file as the source
    return redirect(url_for('views.video_feed', video_source=temp_file_path))


# @views.route('/process-video', methods=['POST'])
# @login_required
# def process_video():
#     # Get the chosen video source from the request data
#     video_source = request.json.get('videoSource')

#     # Start processing the video using the chosen video source
#     result = detect_travel(video_source)

#     # Return a response with the processed video frames
#     return Response(result, mimetype='multipart/x-mixed-replace; boundary=frame')

@views.route('/process-video', methods=['POST'])
@login_required
def process_video():
    video_source = request.json.get('videoSource')
    def generate_frames():
        video_source = request.json.get('videoSource') # Or provide your video source here
        for frame in detect_travel(video_source):
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    #result = detect_travel(video_source)
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Define a route handler for /insights.html
@views.route('/insights.html')
@login_required
def insights():
    # Render the insights.html template
    return render_template("insights.html",user=current_user)




# # HTML Form to choose between file upload and camera usage
# @views.route('/choose-file-upload')
# def index():
#     return '''
#     <form action="/upload" method="post" enctype="multipart/form-data">
#         <input type="file" name="video_file">
#         <input type="submit" value="Upload Video">
#     </form>
#     <form action="/camera" method="get">
#         <button type="submit">Use device's camera</button>
#     </form>
#     '''

# Route to render the choose_file_upload.html template
@views.route('/choose-file-upload')
@login_required
def choose_file_upload():
    
    return render_template('choose_file_upload.html', user = current_user)

# Create 'uploads' directory if it doesn't exist
# UPLOADS_DIR = 'uploads'
# if not os.path.exists(UPLOADS_DIR):
#     os.makedirs(UPLOADS_DIR)

@views.route('/upload', methods=['POST'])
def upload_file():
    if 'video_file' not in request.files:
        return redirect(request.url)
    file = request.files['video_file']
    print("file vachindi")
    if file.filename == '':
        return redirect(request.url)
    # Save the uploaded file to a temporary location
    temp_file_path = os.path.join(tempfile.gettempdir(), file.filename)
    file.save(temp_file_path)
    # Redirect to the video feed route with the uploaded file as the source
    return redirect(url_for('views.output_video', video_source=temp_file_path))
    
    # if request.method == 'POST':
    #     file = request.files['file']
    #     if file:
    #         filename = 'uploaded_video.mp4'
    #         file.save(os.path.join(UPLOADS_DIR, filename))
    #         session['video_source'] = filename
    #         # Redirect to the output_video route
    #         return redirect(url_for('views.output_video'))  # Use 'views.output_video' as the endpoint
    #     return render_template('upload.html')  # Render upload.html template if no file is provided
    # return render_template('upload.html')  # Render upload.html template for GET request


# Route to handle camera usage
@views.route('/camera')
def camera():
    return detect_and_render_video(0)  # Pass 0 to use the device's camera


# 1)This is working 
###################
# Route to render the output video
@views.route('/output_video')
def output_video():
     # Check if the 'video_source' query parameter is present
    # video_source = session.get('video_source')
    # video_source = request.args.get('video_source', 0)
    video_source = request.args.get('video_source',0)
    if video_source:
        
        #return render_template('output.html', video_source=video_source)
        return Response(detect_travel(video_source), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return 'Error: No video source provided'

##############

###############
###############
# 2)this might work

# @views.route('/output_video')
# def output_video():
#     video_source = request.args.get('video_source', 0)
#     if video_source:
#         detector = detect_travel(video_source)

#         def generate():
#             for frame, dribble_count, travel_detected, total_step_count in detector:
#                 # Convert frame to JPEG
#                 ret, buffer = cv2.imencode('.jpg', frame)
#                 frame_data = buffer.tobytes()

#                 # Construct response containing frame data and variable values
#                 response_data = (
#                     b'--frame\r\n'
#                     b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n' +
#                     b'Dribble Count: ' + str(dribble_count).encode() + b'\r\n' +
#                     b'Travel Detected: ' + str(travel_detected).encode() + b'\r\n' +
#                     b'Steps Count: ' + str(total_step_count).encode() + b'\r\n'
#                 )

#                 yield response_data

#         return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
#     else:
#         return 'Error: No video source provided'
#############

###########
########
# 3. Trying to send variables
# @views.route('/output_video')
# def output_video():
#     video_source = request.args.get('video_source', 0)
#     if video_source:
#         detector = detect_travel(video_source)
#         return render_template('output.html',video_source= video_source)
#     else:
#         return 'Error: No video source provided'
    
#####
#### 4. Tryna variables

# @views.route('/variable_updates')
# def variable_updates(video_source):
#     if video_source:
#         detector = detect_travel(video_source)
#         for frame, dribble_count, travel_detected, total_step_count in detector:
#             yield f"Dribble Count: {dribble_count}\nTravel Detected: {travel_detected}\nSteps Count: {total_step_count}\n\n"
#     else:
#         yield 'Error: No video source provided'

# @views.route('/variable_updates_generator')
# def variable_updates_handler():
#     video_source = request.args.get('video_source', 0)
#     return Response(variable_updates(video_source), content_type='text/event-stream')
   

def detect_and_render_video(video_source):
    return Response(detect_travel(video_source), mimetype='multipart/x-mixed-replace; boundary=frame')
    #return render_template('output.html', video_source=video_source)

def generate_frames(video_source):
    video_source = request.json.get('videoSource') # Or provide your video source here
    for frame in detect_travel(video_source):
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# def generate_frames(video_source):
#     # Get the video source from the request data or provide your own source here
#     video_source = request.json.get('videoSource')  

#     for frame, dribble_count, travel_detected, step_count in detect_travel(video_source):
#         # Yield frame and stats
#         yield (frame, dribble_count, travel_detected, step_count)
# def generate_frames(video_source):
#     video_source = request.json.get('videoSource') # Or provide your video source here
#     for frame, dribble_count, travel_detected, step_count in detect_travel(video_source):
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n' +
#                b'Dribble Count: ' + str(dribble_count).encode() + b'\r\n' +
#                b'Travel Detected: ' + str(travel_detected).encode() + b'\r\n' +
#                b'Steps Count: ' + str(step_count).encode() + b'\r\n')
