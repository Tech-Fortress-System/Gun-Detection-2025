import os
import smtplib
import ssl
import threading
import traceback
from datetime import datetime
from email.message import EmailMessage

import cv2
import torch
from dotenv import load_dotenv
from flask import Flask, render_template
from twilio.rest import Client

# ------------------- LOAD ENV VARIABLES -------------------
load_dotenv()

# ------------------- CONFIGURATION -------------------
CAMERA_LOCATION = "Waterfront Mall Entrance 2"

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM")
WHATSAPP_TO = os.getenv("WHATSAPP_TO")

EMAIL_SENDER = os.getenv("EMAIL_SENDER", "Balfourmhlangovuyo98@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "dmxencmxlcyezdrr")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "Ziziphontusi@gmail.com")

DETECTION_COOLDOWN = 30  # seconds between alerts
IMAGE_SAVE_PATH = "static/gun_detection.jpg"

# ------------------- LOAD YOLO MODEL -------------------
print("🔄 Loading YOLOv5 model...")
model = torch.hub.load("ultralytics/yolov5", "yolov5s", trust_repo=True)
print("✅ YOLOv5 model loaded.")

# ------------------- FLASK APP -------------------
app = Flask(__name__)

# ------------------- GLOBAL VARIABLES -------------------
last_alert_time = None
alert_lock = threading.Lock()
alert_sent = False


# ------------------- ALERT FUNCTION -------------------
def alert_security(image_path):
    """Send email and WhatsApp alerts when a gun is detected."""
    global last_alert_time, alert_sent

    with alert_lock:
        now = datetime.now()
        # Skip alert if within cooldown
        if last_alert_time:
            elapsed = (now - datetime.strptime(last_alert_time, "%Y-%m-%d %H:%M:%S")).total_seconds()
            if elapsed < DETECTION_COOLDOWN:
                return

        last_alert_time = now.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[ALERT] Gun detected at {last_alert_time}.")

        # ----- Email Alert -----
        try:
            msg = EmailMessage()
            msg.set_content(f"""🚨 ALERT: Gun detected!

Camera Location: {CAMERA_LOCATION}
Time: {last_alert_time}

See attached image.""")
            msg["Subject"] = "Security Alert - Gun Detected"
            msg["From"] = EMAIL_SENDER
            msg["To"] = EMAIL_RECEIVER

            with open(image_path, "rb") as img_file:
                msg.add_attachment(img_file.read(), maintype="image", subtype="jpeg", filename="detection.jpg")

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.send_message(msg)
            print("✅ Email alert sent.")
        except Exception as e:
            print(f"❌ Email error: {e}")
            traceback.print_exc()

        # ----- WhatsApp Alert -----
        try:
            client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f"🚨 ALERT: Gun detected at {CAMERA_LOCATION} on {last_alert_time}.",
                from_=WHATSAPP_FROM,
                to=WHATSAPP_TO,
            )
            print(f"✅ WhatsApp alert sent. SID: {message.sid}")
        except Exception as e:
            print(f"❌ WhatsApp error: {e}")
            traceback.print_exc()

        alert_sent = True


# ------------------- DETECTION LOOP -------------------
def detection_loop():
    global alert_sent
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam.")
        return

    print("🔍 Starting webcam detection. Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame.")
            break

        # Run YOLO detection
        results = model(frame)
        detections = results.xyxy[0]  # bounding boxes
        labels = results.names

        for *xyxy, conf, cls in detections:
            label = labels[int(cls)].lower()
            if label == "gun" and not alert_sent:
                cv2.imwrite(IMAGE_SAVE_PATH, frame)
                alert_security(IMAGE_SAVE_PATH)

        # Optional: show live detection with annotations
        annotated_frame = results.render()[0]
        cv2.imshow("Gun Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ------------------- FLASK DASHBOARD -------------------
@app.route("/")
def admin_dashboard():
    return render_template(
        "dashboard.html",
        camera_location=CAMERA_LOCATION,
        last_alert=last_alert_time or "No alerts yet",
        image_exists=os.path.exists(IMAGE_SAVE_PATH),
    )


# ------------------- MAIN -------------------
if __name__ == "__main__":
    detection_thread = threading.Thread(target=detection_loop, daemon=True)
    detection_thread.start()
    app.run(debug=True)
    detection_thread.join()
