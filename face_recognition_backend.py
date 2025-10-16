import face_recognition
import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import logging

# ---------------- Persistent Base Directory ----------------
# Use project-relative runtime_data folder
BASE_DIR = os.path.join(os.getcwd(), "runtime_data")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
ENCODINGS_FILE = os.path.join(BASE_DIR, "encodings.pkl")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# -------------------- Logging Setup --------------------
log_file = os.path.join(LOG_DIR, "face_recognition.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(log_file, encoding='utf-8')]
)

# -------------------- Update Encodings --------------------
def update_encodings(images_dir=IMAGES_DIR, encodings_file=ENCODINGS_FILE):
    try:
        known_encodings = []
        names = []

        for user in os.listdir(images_dir):
            user_dir = os.path.join(images_dir, user)
            if not os.path.isdir(user_dir):
                continue
            for file_name in os.listdir(user_dir):
                img_path = os.path.join(user_dir, file_name)
                img = cv2.imread(img_path)
                if img is None:
                    logging.warning(f"Cannot read image: {img_path}")
                    continue
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                encodes = face_recognition.face_encodings(img_rgb)
                if encodes:
                    known_encodings.append(encodes[0])
                    names.append(user)
                else:
                    logging.warning(f"No face found in image: {img_path}")

        with open(encodings_file, 'wb') as f:
            pickle.dump({"names": names, "encodings": known_encodings}, f)
        logging.info(f"Encodings updated: {len(names)} faces encoded.")

    except Exception as e:
        logging.error(f"Failed to update encodings: {e}")
        raise e

# -------------------- Recognize Faces in Single Frame --------------------
def recognize_faces_in_frame(frame, encodings_file=ENCODINGS_FILE, threshold=0.5):
    """Return list of recognized names in a single frame"""
    if not os.path.exists(encodings_file):
        logging.warning("Encodings file missing. Generating new encodings...")
        update_encodings()

    try:
        with open(encodings_file, 'rb') as f:
            data = pickle.load(f)
    except (EOFError, pickle.UnpicklingError):
        logging.warning("Encodings file corrupted. Regenerating...")
        update_encodings()
        with open(encodings_file, 'rb') as f:
            data = pickle.load(f)

    known_encodings = data.get("encodings", [])
    names = data.get("names", [])

    if not known_encodings:
        return []

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    face_encodings = face_recognition.face_encodings(rgb_small, face_recognition.face_locations(rgb_small))

    recognized_names = []
    for encode_face in face_encodings:
        matches = face_recognition.face_distance(known_encodings, encode_face)
        name = "Unknown"
        if len(matches) > 0:
            best_match_index = np.argmin(matches)
            if matches[best_match_index] < threshold:
                name = names[best_match_index]

        if name != "Unknown":
            recognized_names.append(name)

    return recognized_names

# -------------------- Full Webcam Recognition (Optional) --------------------
def run_face_recognition(callback=None, threshold=0.5, encodings_file=ENCODINGS_FILE):
    if not os.path.exists(encodings_file):
        logging.warning("Encodings file not found, generating new encodings...")
        update_encodings()

    try:
        with open(encodings_file, 'rb') as f:
            data = pickle.load(f)
        known_encodings = data.get("encodings", [])
        names = data.get("names", [])
    except (EOFError, pickle.UnpicklingError):
        logging.warning("Encodings file corrupted. Regenerating...")
        update_encodings()
        with open(encodings_file, 'rb') as f:
            data = pickle.load(f)
        known_encodings = data.get("encodings", [])
        names = data.get("names", [])

    if not known_encodings:
        logging.warning("No known faces found in dataset. Exiting recognition.")
        return []

    attendance_list = []

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Cannot access webcam")
        return attendance_list

    logging.info("Webcam started for face recognition.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_encodings = face_recognition.face_encodings(rgb_small, face_recognition.face_locations(rgb_small))

        for encode_face in face_encodings:
            matches = face_recognition.face_distance(known_encodings, encode_face)
            name = "Unknown"
            if len(matches) > 0:
                best_match_index = np.argmin(matches)
                if matches[best_match_index] < threshold:
                    name = names[best_match_index]

            if name != "Unknown" and name not in [x['name'] for x in attendance_list]:
                now = datetime.now().strftime('%H:%M:%S')
                attendance_list.append({'name': name, 'time': now})
                logging.info(f"Marked {name} at {now}")
                if callback:
                    try:
                        callback(name, now)
                    except Exception as e:
                        logging.warning(f"Callback error: {e}")

    cap.release()
    logging.info("Webcam closed.")
    return attendance_list
