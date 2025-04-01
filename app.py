# Copyright (c) 2025 Shiva Hanumanthaiah
# All rights reserved.

from flask import Flask, Response, render_template, request, jsonify
import cv2
import os
import threading
import base64
import time
from flask_socketio import SocketIO, emit
import eventlet
import eventlet.wsgi
from flask_cors import CORS
import queue
import numpy as np

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5000", "http://localhost:5000"])

socketio = SocketIO(app, cors_allowed_origins=["http://127.0.0.1:5000", "http://localhost:5000"], async_mode='eventlet')

class VideoStreamProcessor:
    def __init__(self, video_source, frame_width, frame_height, default_fps, cache_duration=30, video_folder="./video_source_files/", channel_color="blue"):
        self.video_source = video_source
        self.video_folder = video_folder
        self.channel_color = channel_color
        self.current_video_source = video_source
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.default_fps = default_fps
        self.cache_duration = cache_duration

       # setting frame_cache_maxlen to value 900 assuming 30 FPS for 30 seconds duration cache
        self.frame_cache_maxlen = self.default_fps * self.cache_duration
        self.frame_cache = queue.Queue(maxsize=self.frame_cache_maxlen)
        self.frame_count = 0
        self.live_video_dict = {}
        self.original_fps = 0
        self.gray_intensity = 128
        self.caching_enabled = False

        self.thread = threading.Thread(target=self.generate_frames)
        self.thread.start()

    def generate_frames(self):
        try:
            while True:
                self.current_video_source = self.video_source
                video_source_path = self.video_folder + self.video_source
                cap = cv2.VideoCapture(video_source_path)
                self.original_fps = int(cap.get(cv2.CAP_PROP_FPS))
                cap.set(cv2.CAP_PROP_FPS, self.default_fps)
                if not cap.isOpened():
                    print(f"Error: Could not open video file {self.video_source}")
                    break

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    if self.current_video_source != self.video_source:
                        break

                    frame = cv2.resize(frame, (self.frame_width, self.frame_height))

                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray_frame = cv2.addWeighted(gray_frame, self.gray_intensity / 128.0, np.zeros_like(gray_frame), 0, 0)
                    _, gray_encoded = cv2.imencode('.jpg', gray_frame)
                    gray_base64 = base64.b64encode(gray_encoded).decode('utf-8')

                    channel_frame = self.apply_channel_filter(frame)
                    _, channel_encoded = cv2.imencode('.jpg', channel_frame)
                    channel_base64 = base64.b64encode(channel_encoded).decode('utf-8')

                    _, bgr_encoded = cv2.imencode('.jpg', frame)
                    bgr_base64 = base64.b64encode(bgr_encoded).decode('utf-8')

                    if self.caching_enabled and self.frame_count < self.frame_cache_maxlen:
                        self.frame_cache.put({"timestamp": time.time(), "gray": gray_base64, self.channel_color: channel_base64, "bgr": bgr_base64})
                        self.frame_count += 1

                    self.live_video_dict = {"timestamp": time.time(), "gray": gray_base64, self.channel_color: channel_base64, "bgr": bgr_base64}

        except Exception as e:
            print(f"Error generating frames: {e}")
        finally:
            cap.release()

    def apply_channel_filter(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        if self.channel_color == "green":
            hsv[:, :, 0] = 60
        elif self.channel_color == "red":
            hsv[:, :, 0] = 180
        else:
            hsv[:, :, 0] = 120
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def get_video_stream(self):
        def generate():
            if self.caching_enabled and not self.frame_cache.empty():
                while self.frame_count < self.frame_cache_maxlen and not self.frame_cache.empty():
                    oldest = self.frame_cache.get()
                    yield f'data:{{ "gray": "{oldest["gray"]}", "channel_color": "{self.live_video_dict[self.channel_color]}", "bgr": "{oldest["bgr"]}", "cache_status": "Showing Cached Data" }}\n\n'
                    self.frame_count += 1
                self.caching_enabled = False
            else:
                while "gray" not in self.live_video_dict:
                    time.sleep(1)
                yield f'data:{{ "gray": "{self.live_video_dict["gray"]}", "channel_color": "{self.live_video_dict[self.channel_color]}", "bgr": "{self.live_video_dict["bgr"]}", "cache_status": "Showing Live Streamed Data", "fps": {self.original_fps} }}\n\n'

        return Response(generate(), mimetype='text/event-stream')

# Create the processor instance
# Assuming this is your global VideoStreamProcessor instance
video_processor = VideoStreamProcessor(video_source="big_buck_bunny.mp4", frame_width=640, frame_height=480, default_fps=60)

@app.route('/apply_changes', methods=['POST'])
def apply_changes():
    selected_video = request.form.get('video_source')
    video_processor.video_source = selected_video

    new_frame_width = int(request.form.get('frame_width'))
    new_frame_height = int(request.form.get('frame_height'))

    if new_frame_width:
        video_processor.frame_width = new_frame_width
    if new_frame_height:
        video_processor.frame_height = new_frame_height

    return jsonify({"status": "success"})

@app.route('/start_caching', methods=['POST'])
def handle_start_caching():

    video_processor.caching_enabled = True
    video_processor.frame_count = 0
    return jsonify({"status": "success"})


@app.route("/video_feed")
def video_feed():
    return video_processor.get_video_stream()

@app.route('/', methods=['GET', 'POST'])
def index():
    video_files = [f for f in os.listdir(video_processor.video_folder) if f.endswith(('.mp4', '.avi', '.mov'))]

    try:
        video_source_path = video_processor.video_folder + video_processor.current_video_source
        cap = cv2.VideoCapture(video_source_path)
        original_fps = int(cap.get(cv2.CAP_PROP_FPS))
    except Exception as e:
        print (f"Error {e}: Inside index(): could not open video_source file :{video_source_path}", flush=True)
    finally:
        cap.release()


    return render_template(
        'index.html',
        video_files=video_files,
        fps=video_processor.original_fps,
        frame_width=video_processor.frame_width,
        frame_height=video_processor.frame_height,   
        selected_video=os.path.basename(video_processor.video_source)
    )

@app.route('/set_grayscale_intensity', methods=['POST'])
def change_gray_intensity():
    data = request.get_json()
    intensity = int(data.get('gray_intensity'))
    if intensity >= 0 and intensity <= 255:
        video_processor.gray_intensity = intensity

    return jsonify({"status": "success"})

@app.route('/set_channel_color', methods=['POST'])
def change_channel_color():
    data = request.get_json()
    video_processor.channel_color = data.get('channel_color')

    return jsonify({"status": "success"})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

