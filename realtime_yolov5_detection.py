import cv2
import torch
import smtplib
from email.message import EmailMessage
import ssl
import os
from datetime import datetime
import threading
from twilio.rest import Client
from dotenv import load_dotenv
import traceback

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
IMAGE_SAVE_PATH = "gun_detection.jpg"

# ------------------- LOAD YOLOv5 FIREARM MODEL -------------------
print("🔄 Loading custom YOLOv5 firearm model...")
model_path = "best_gun_model.pt"  # Make sure this file exists in your project folder
model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, trust_repo=True)
print("✅ Custom YOLOv5 firearm model loaded.")

# ------------------- GLOBAL VARIABLES -------------------
last_alert_time = None
alert_lock = threading.Lock()
alert_sent = False
cap = cv2.VideoCapture(0)  # Use webcam 0

# Define the firearm classes your custom model recognizes
FIREARM_CLASSES = ["gun", "pistol", "rifle"]  # Adjust based on your model labels

# ------------------- ALERT FUNCTION -------------------
def alert_security(image_path):
    """Send email and WhatsApp alerts when a firearm is detected."""
    global last_alert_time, alert_sent

    with alert_lock:
        now = datetime.now()
        if last_alert_time:
            elapsed = (now - datetime.strptime(last_alert_time, '%Y-%m-%d %H:%M:%S')).total_seconds()
            if elapsed < DETECTION_COOLDOWN:
                return

        last_alert_time = now.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[ALERT] Firearm detected at {last_alert_time}.")

        # ----- Email Alert -----
        try:
            msg = EmailMessage()
            msg.set_content(f"""🚨 ALERT: Firearm detected!

Camera Location: {CAMERA_LOCATION}
Time: {last_alert_time}

See attached image.""")
            msg['Subject'] = "Security Alert - Firearm Detected"
            msg['From'] = EMAIL_SENDER
            msg['To'] = EMAIL_RECEIVER

            with open(image_path, 'rb') as img_file:
                msg.add_attachment(img_file.read(), maintype='image', subtype='jpeg', filename="detection.jpg")

            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context()) as smtp:
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
                body=f"🚨 ALERT: Firearm detected at {CAMERA_LOCATION} on {last_alert_time}.",
                from_=WHATSAPP_FROM,
                to=WHATSAPP_TO
            )
            print(f"✅ WhatsApp alert sent. SID: {message.sid}")
        except Exception as e:
            print(f"❌ WhatsApp error: {e}")
            traceback.print_exc()

        alert_sent = True

# ------------------- MAIN LOOP -------------------
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame from webcam.")
            break

        # Run YOLO detection
        results = model(frame)
        detections = results.xyxy[0]
        labels = results.names

        # Reset alert_sent if cooldown elapsed
        if last_alert_time:
            elapsed = (datetime.now() - datetime.strptime(last_alert_time, '%Y-%m-%d %H:%M:%S')).total_seconds()
            if elapsed > DETECTION_COOLDOWN:
                alert_sent = False

        # Check for firearms and trigger alert
        for *xyxy, conf, cls in detections:
            label = labels[int(cls)].lower()
            if label in FIREARM_CLASSES and not alert_sent:
                cv2.imwrite(IMAGE_SAVE_PATH, frame)
                alert_security(IMAGE_SAVE_PATH)
                break  # Stop after first firearm detected per frame

        # Render detections on the frame
        annotated_frame = results.render()[0]

        # Show the frame in a window
        cv2.imshow('YOLOv5 Firearm Detection', annotated_frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Camera and windows released successfully.")
