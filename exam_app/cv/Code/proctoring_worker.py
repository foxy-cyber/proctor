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
    cheating_detected = results.get("Mouth Open") or results.get("Banned Objects") or no_of_people

    if usn not in cheating_counter:
        cheating_counter[usn] = 0

    if cheating_detected:
        print(image_path,"   ","cheated")
        cheating_counter[usn] += 1
        if cheating_counter[usn] >= 5:
            send_warning_to_frontend(usn, stop=True)
        else:
            send_warning_to_frontend(usn, stop=False)
    else:
        cheating_counter[usn] = 0  # Reset if no cheating detected

def send_warning_to_frontend(usn, stop=False):
    """Send warning to frontend"""
    payload = {'usn': usn, 'warning': 'Cheating detected', 'stop_capture': stop}
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