import pika
import json
import numpy as np
import requests
from updated_cv import perform_proctoring_analysis

import cv2
import os
import pandas as pd
import numpy as np
from collections import Counter
import face_recognition
import dlib
from math import hypot
# from exam_app.ml.ml2 import ml_model
from landmark_models import *
from face_spoofing import *
from headpose_estimation import *
from face_detection import get_face_detector, find_faces
from object_detection import yoloV3Detect

cheating_counter = {}
consecutive_frame_counter = {}
checks = ["Mouth Open", "Head Pose", "Eye Tracking"]
convert_to_bool = {
    "Looking away from screen": True,
    "Looking at screen": False,
}

def process_image(usn, image_path):
    """Process image and analyze cheating"""
    global cheating_counter
        # Load headpose model
    h_model = load_hp_model('models/Headpose_customARC_ZoomShiftNoise.hdf5')

    # Load face detection model
    face_model = get_face_detector()

    # Load face landmark model
    predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")


    results = perform_proctoring_analysis(image_path,face_model,predictor,h_model)
    
    print("result isss:  ", results)
     
#put your conditions here
    # cheating_detected = results.get("Banned Objects") or results.get("Spoof Face Detected") or results.get("Mouth Open")
    # if(results.get("Banned Objects")>0):
    #     banned_object_detect= True
    no_of_people=False
    
    if (results.get("Number of People")!=1 or results.get('Number of Faces Detected')!=1):
        no_of_people=True
    cheating_detected = results.get("Banned Objects") or no_of_people

    if usn not in consecutive_frame_counter:
        user_face = {}
        # checks = ["Mouth Open", "Head Pose", "Eye Tracking"] #error
        for check in checks:
            if check not in user_face:
                if results.get(check) == "N/A":
                    user_face[check] = 0
                else:
                    result_check = results.get(check) if check == "Mouth Open" else convert_to_bool[results.get(check)]
                    if result_check == False:
                        user_face[check] = 0
                    else:
                        user_face[check] = 1
        consecutive_frame_counter[usn] = user_face
    else:
        user_face = consecutive_frame_counter[usn]
        for check in checks:
            if results.get(check) == "N/A":
                user_face[check] = 0
            else:
                result_check = results.get(check) if check == "Mouth Open" else convert_to_bool[results.get(check)]
                if result_check == False:
                    user_face[check] = 0
                else:
                    user_face[check] += 1
        consecutive_frame_counter[usn] = user_face
    user_face = consecutive_frame_counter[usn]
    if user_face["Mouth Open"] >= 2:
        send_warning_to_frontend(usn, stop=True,warning="Mouth Open")
    if user_face["Head Pose"] >= 2:
        send_warning_to_frontend(usn, stop=True,warning="Head Pose Looking Away from screen")
    if user_face["Eye Tracking"] >= 2:
        send_warning_to_frontend(usn, stop=True,warning="Eye Tracking Looking Away from screen")
    
    if user_face["Mouth Open"] == 1:
        send_warning_to_frontend(usn, stop=False,warning="Mouth Open")
    if user_face["Head Pose"] == 1:
        send_warning_to_frontend(usn, stop=False,warning="Head Pose Looking Away from screen")
    if user_face["Eye Tracking"] == 1:
        send_warning_to_frontend(usn, stop=False,warning="Eye Tracking  Looking Away from screen")

    if usn not in cheating_counter:
        cheating_counter[usn] = 0


    if cheating_detected:
        print(image_path,"   ","cheated")
        cheating_counter[usn] += 1
        if cheating_counter[usn] >= 2:
            send_warning_to_frontend(usn, stop=True)
        else:
            send_warning_to_frontend(usn, stop=False)
    else:
        cheating_counter[usn] = 0  # Reset if no cheating detected

def send_warning_to_frontend(usn, stop=False,warning="Cheating detected"):
    """Send warning to frontend"""
    payload = {'usn': usn, 'warning': warning, 'stop_capture': stop}
    requests.post("http://localhost:8000/send_warning/", json=payload)

def callback(ch, method, properties, body):
    """Consume message from queue and process image"""
    data = json.loads(body)
    usn = data['usn']
    image_path = data['image_path']
    process_image(usn, image_path)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='proctoring_queue')

channel.basic_consume(queue='proctoring_queue', on_message_callback=callback, auto_ack=True)
print("Waiting for messages...")
channel.start_consuming()