import cv2
import os
import pandas as pd
import numpy as np
from collections import Counter
import face_recognition
import dlib
from math import hypot
# from ml2 import ml_model
from landmark_models import *
from face_spoofing import *
from headpose_estimation import *
from face_detection import get_face_detector, find_faces
from object_detection import yoloV3Detect

# Function to perform proctoring analysis on an image
def perform_proctoring_analysis(image_path,face_model,predictor,h_model):
    # Read the image
    frame = cv2.imread(image_path)

    # Initialize variables
    results = {}

    # Resize frame of image to 1/4 size for faster face recognition processing
    if frame is not None:
     small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    else:
     print("Error: The frame is empty or not loaded correctly.")

    # Perform proctoring analysis
    try:
        ##### Object Detection #####
        try:
            fboxes, fclasses = yoloV3Detect(small_frame)
            
            to_detect = ['person', 'laptop', 'cell phone', 'book', 'tv']

            temp1, temp2 = [], []

            for i in range(len(fclasses)):
                if fclasses[i] in to_detect:
                    temp1.append(fboxes[i])
                    temp2.append(fclasses[i])

            # Counter
            count_items = Counter(temp2)
        except Exception as e:
            count_items = {}
            count_items['person'] = 0
            count_items['laptop'] = 0
            count_items['cell phone'] = 0
            count_items['book'] = 0
            count_items['tv'] = 0
            print(e)

        results["Number of People"] = count_items['person']
        results["Banned Objects"] = count_items['laptop'] + count_items['cell phone'] + count_items['book'] + count_items['tv']

        if count_items['person'] == 1:
            #### face detection using caffe model of OpenCV's DNN module ####
            faces = find_faces(small_frame, face_model)
            if len(faces) > 0:
                face = faces[0]
            else:
                results["Number of Faces Detected"] = 0
                return results

            results["Number of Faces Detected"] = 1

            # Convert BGR image to RGB image
            rgb_small_frame = small_frame[:, :, ::-1]

            # Get CNN feature vector
            face_encodings = face_recognition.face_encodings(rgb_small_frame, [face])
            

            #### mouth movement ####
            left, top, right, bottom = [coord * 4 for coord in face]
            face_dlib = dlib.rectangle(left, top, right, bottom)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            facial_landmarks = predictor(gray, face_dlib)
            mouth_ratio = get_mouth_ratio([60, 62, 64, 66], frame, facial_landmarks)
            results["Mouth Open"] = mouth_ratio > 0.1

            #### head pose ####
            oAnglesNp, oBboxExpanded = headpose_inference(h_model, frame, face)
            condition1 = (round(oAnglesNp[0], 1) not in [0.0, -1.0, -1.1, -1.2, -1.3, -1.4, -1.5, -1.6, -1.7] and
                          round(oAnglesNp[1], 0) not in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
            results["Head Pose"] = "Looking away from screen" if condition1 else "Looking at screen"

            ##### eye tracker #####
            gaze_ratio1_left_eye, gaze_ratio2_left_eye = get_gaze_ratio([36, 37, 38, 39, 40, 41], frame, facial_landmarks)
            gaze_ratio1_right_eye, gaze_ratio2_right_eye = get_gaze_ratio([42, 43, 44, 45, 46, 47], frame, facial_landmarks)
            gaze_ratio1 = (gaze_ratio1_right_eye + gaze_ratio1_left_eye) / 2
            results["Eye Tracking"] = "Looking away from screen" if gaze_ratio1 <= 0.35 or gaze_ratio1 >= 4 or condition1 else "Looking at screen"

            #### face spoofing ####
            measures = face_spoof(frame, face)
            results["Spoof Face Detected"] = np.mean(measures) < 0.7
        else:
            results["Face Recognized"] = "N/A"
            results["Mouth Open"] = "N/A"
            results["Head Pose"] = "N/A"
            results["Eye Tracking"] = "N/A"
            results["Spoof Face Detected"] = "N/A"

    except Exception as e:
        print(e)
        results = {}
    return results

# Setup
# Load known face encodings and names
def first_function(usn):
    
    # Load headpose model
    h_model = load_hp_model('models/Headpose_customARC_ZoomShiftNoise.hdf5')

    # Load face detection model
    face_model = get_face_detector()

    # Load face landmark model
    predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")

    # Define the path to the folder containing images
    image_folder_path = "images/"+usn

    # Initialize an empty DataFrame to store the results
    results_df = pd.DataFrame(columns=["Image Name", "Number of People", "Banned Objects", "Number of Faces Detected",
                                    "Face Recognized", "Mouth Open", "Head Pose", "Eye Tracking", "Spoof Face Detected"])

    # Loop through the images in the folder
    for image_name in os.listdir(image_folder_path):
        image_path = os.path.join(image_folder_path, image_name)

        # Perform proctoring analysis on the image
        results = perform_proctoring_analysis(image_path,face_model,predictor,h_model)

        # Append the results for this image to the DataFrame
        results_df = results_df.append({
            "Image Name": image_name,
            "Number of People": results.get("Number of People", np.nan),
            "Banned Objects": results.get("Banned Objects", np.nan),
            "Number of Faces Detected": results.get("Number of Faces Detected", np.nan),
            "Face Recognized": results.get("Face Recognized", np.nan),
            "Mouth Open": results.get("Mouth Open", np.nan),
            "Head Pose": results.get("Head Pose", np.nan),
            "Eye Tracking": results.get("Eye Tracking", np.nan),
            "Spoof Face Detected": results.get("Spoof Face Detected", np.nan)
        }, ignore_index=True)

    # Define the CSV folder path
    csv_folder_path = os.path.join("csv", usn)

    # Create the folder if it doesn't exist
    if not os.path.exists(csv_folder_path):
        os.makedirs(csv_folder_path)

    # Define the CSV file path
    csv_file_path = os.path.join(csv_folder_path, "proctoring_results.csv")

    # Save the results to a CSV file
    results_df.to_csv(csv_file_path, index=False)

    # Replace backslashes with forward slashes in the printed path
    print("Results saved to:", csv_file_path.replace("\\", "/"))
    csv_file_path=csv_file_path.replace("\\", "/")

    # Call the ML model and get the score
    score = ml_model(csv_file_path)
    score = str(score)
    print("score: " + score)
    return score