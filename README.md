# Smart-Attendance-App-v1.0
An AI-powered, face recognition–based desktop attendance system built with Python, Flask, OpenCV, and face_recognition. Provides a clean GUI for managing datasets and tracking attendance.

**Features**

Desktop application for attendance tracking using face recognition.
Add, update, or delete user datasets via GUI.
Live camera view to track and mark attendance automatically.
Export attendance reports as PDF.
Lightweight, easy-to-run, and fully Python-based.


**Technologies Used**

Python 3.13.7
Flask (Web interface inside desktop window)
OpenCV (Webcam capture & image handling)
face_recognition (AI-powered face recognition)
FPDF (PDF report generation)
Flask-Session (Manage session data)


**Folder Structure**

Smart Attendance App/
│
├── launcher.py                  # Entry point: runs the app in a desktop window
├── attendance_app.py            # Main Flask app code
├── face_recognition_backend.py  # Handles face recognition & dataset encodings
├── static/                      # JS, CSS, other static files
├── templates/                   # HTML templates for GUI
├── runtime_data/                # Generated automatically (images, encodings, logs, session)
└── requirements.txt             # Python dependencies



**Setup Instructions**

*Clone the repository:*
git clone https://github.com/TridipB02/Smart-Attendance-App-v1.0.git
cd "Smart Attendance App"

*Install dependencies:*
pip install -r requirements.txt

*Run the application:*
python launcher.py

*App usage:*
Add users/images via Set Dataset page
Click Start Attendance to mark attendance live
Export attendance via Export PDF


**Notes**

The app generates runtime_data/ on first run.
This folder stores:
images/ → User face datasets
encodings.pkl → Precomputed face encodings
logs/ → App logs
flask_session/ → Session data
No initial dataset is required; new users can be added via GUI.


**License**

© Tridip Baksi 2025. 
You are free to view, study, and use this code for learning or personal projects. 
You **must give proper credit** if you use any part of this code. 
Commercial use or claiming this work as your own is strictly prohibited.

**Future Versions**
v2.0: Packaged desktop executable, improved UI/UX, performance enhancements
