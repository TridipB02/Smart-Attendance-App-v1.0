# attendance_app.py
import os
import datetime
import threading
import cv2
import logging
import shutil
from flask import (
    Flask, render_template, Response, redirect, url_for,
    send_file, jsonify, flash, request
)
from flask_session import Session
from face_recognition_backend import recognize_faces_in_frame, update_encodings
from fpdf import FPDF
from io import BytesIO

# -------------------- Logging Setup --------------------
logging.basicConfig(level=logging.INFO)

# -------------------- Flask Setup --------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SECRET_KEY'] = 'supersecret'

# ---------------- Persistent Base Directory --------------------
BASE_DIR = os.path.join(os.getcwd(), "runtime_data")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
ENCODINGS_FILE = os.path.join(BASE_DIR, "encodings.pkl")
LOG_DIR = os.path.join(BASE_DIR, "logs")
SESSION_DIR = os.path.join(BASE_DIR, "flask_session")

# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

# Flask-Session Setup
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = SESSION_DIR
Session(app)

# Ensure encodings file exists (generate if absent)
try:
    if not os.path.exists(ENCODINGS_FILE):
        logging.info("Encodings file not found — generating initial encodings.")
        update_encodings(IMAGES_DIR, ENCODINGS_FILE)
except Exception as e:
    logging.error(f"Error while ensuring encodings file: {e}")

# -------------------- Global Variables --------------------
attendance_list = []
recently_marked = []
camera_active = False
latest_frame = None
lock = threading.Lock()
camera_thread = None
cap = None

# -------------------- Routes --------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dataset', methods=['GET', 'POST'])
def dataset_page():
    try:
        if request.method == 'POST':
            name = request.form.get("name", "").strip()
            image_file = request.files.get("image")

            logging.info(f"Dataset POST: name={name}, image_file={getattr(image_file, 'filename', None)}")

            if not name or not image_file:
                flash("Name and Image are required!", "danger")
                return redirect(url_for('dataset_page'))

            # Save image with timestamp
            filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(image_file.filename)}"
            user_dir = os.path.join(IMAGES_DIR, name)
            os.makedirs(user_dir, exist_ok=True)
            img_path = os.path.join(user_dir, filename)
            image_file.save(img_path)
            logging.info(f"Saved image to {img_path}")

            # Update encodings
            try:
                update_encodings(IMAGES_DIR, ENCODINGS_FILE)
                flash(f"Added/updated dataset for {name}", "success")
            except Exception as e:
                logging.error(f"Failed to update encodings: {e}")
                flash(f"Uploaded image but failed to update encodings: {e}", "warning")

            return redirect(url_for('index'))

        # GET: show existing dataset
        users_dict = {}
        for user in sorted(os.listdir(IMAGES_DIR)):
            user_dir = os.path.join(IMAGES_DIR, user)
            if os.path.isdir(user_dir):
                images_list = [f for f in os.listdir(user_dir) if os.path.isfile(os.path.join(user_dir, f))]
                users_dict[user] = images_list

        return render_template('dataset.html', users=users_dict, os=os)

    except Exception as e:
        logging.exception("Error in dataset_page")
        flash(f"Error uploading dataset: {e}", "danger")
        return redirect(url_for('dataset_page'))


@app.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):
    try:
        safe_username = os.path.basename(username)
        user_dir = os.path.join(IMAGES_DIR, safe_username)
        if os.path.exists(user_dir) and os.path.isdir(user_dir):
            shutil.rmtree(user_dir)
            logging.info(f"Deleted dataset folder: {user_dir}")

            try:
                update_encodings(IMAGES_DIR, ENCODINGS_FILE)
            except Exception as e:
                logging.error(f"Failed to update encodings after delete: {e}")
                flash(f"Deleted user but failed to update encodings: {e}", "warning")

            flash(f"Deleted dataset for {safe_username}", "success")
        else:
            flash(f"User {safe_username} not found", "warning")
    except Exception as e:
        logging.exception(f"Error deleting user {username}")
        flash(f"Error deleting user: {e}", "danger")

    return redirect(url_for('dataset_page'))


@app.route('/start_attendance')
def start_attendance():
    global camera_active, camera_thread, cap, attendance_list, recently_marked
    attendance_list = []
    recently_marked = []
    camera_active = True

    if camera_thread is None or not camera_thread.is_alive():
        cap = cv2.VideoCapture(0)

        def camera_loop():
            global latest_frame, attendance_list, recently_marked
            while camera_active and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    continue

                recognized_names = recognize_faces_in_frame(frame, encodings_file=ENCODINGS_FILE)
                new_marks = []
                for name in recognized_names:
                    if name not in [x['name'] for x in attendance_list]:
                        attendance_list.append({
                            'name': name,
                            'time': datetime.datetime.now().strftime('%H:%M:%S'),
                            'status': 'Present'
                        })
                        new_marks.append(name)

                if new_marks:
                    recently_marked = new_marks

                _, buffer = cv2.imencode('.jpg', frame)
                with lock:
                    latest_frame = buffer.tobytes()

        camera_thread = threading.Thread(target=camera_loop, daemon=True)
        camera_thread.start()

    return render_template('camera.html')


@app.route('/video_feed')
def video_feed():
    def gen_frames():
        global latest_frame
        while camera_active:
            if latest_frame is not None:
                with lock:
                    frame = latest_frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/stop_camera')
def stop_camera():
    global camera_active, cap
    camera_active = False
    if cap:
        cap.release()
    return '', 204


@app.route('/attendance_live')
def attendance_live():
    global recently_marked
    return jsonify(recently_marked)


@app.route('/attendance')
def attendance_page():
    return render_template('attendance.html', attendance_data=attendance_list)


@app.route('/export_pdf')
def export_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "Attendance Report", ln=True, align='C')
    pdf.ln(10)

    for item in attendance_list:
        line = f"{item['name']} - {item['time']} - {item['status']}"
        pdf.cell(0, 10, line, ln=True)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_buffer = BytesIO(pdf_bytes)
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, as_attachment=True, download_name="attendance.pdf", mimetype='application/pdf')


# -------------------- Run App --------------------
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
