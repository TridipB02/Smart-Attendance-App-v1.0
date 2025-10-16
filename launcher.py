import webview
import threading
import time
from attendance_app import app

# Run Flask app in a separate thread
def start_flask():
    print("[INFO] Starting Flask server...")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    print("[INFO] Flask server stopped.")

if __name__ == "__main__":
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Give Flask a moment to start
    time.sleep(2)

    print("[INFO] Launching Webview...")
    # Launch pywebview window pointing to Flask app
    webview.create_window(
        "Smart Attendance System",
        "http://127.0.0.1:5000",
        width=1024,
        height=768,
        resizable=True
    )
    webview.start()
    print("[INFO] Webview closed.")
