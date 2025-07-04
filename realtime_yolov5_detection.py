import cv2
import torch
import smtplib
from email.message import EmailMessage
import ssl
import os
from flask import Flask, render_template
from datetime import datetime
import threading
from twilio.rest import Client
from dotenv import load_dotenv
import traceback

# Load environment variables from .env file
load_dotenv()

# Configuration
CAMERA_LOCATION = "Waterfront mall entrance 2"
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM")
WHATSAPP_TO = os.getenv("WHATSAPP_TO")

EMAIL_SENDER = "Balfourmhlangovuyo98@gmail.com"
EMAIL_PASSWORD = "dmxencmxlcyezdrr"
EMAIL_RECEIVER = "Ziziphontusi@gmail.com"

# Load YOLOv5 model (replace 'yolov5s' with your custom gun detection model if applicable)
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', trust_repo=True)

app = Flask(__name__)
last_alert_time = None
alert_sent = False

def alert_security(image_path):
    global last_alert_time
    last_alert_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[ALERT] Gun detected at {last_alert_time}. Sending alerts...")

    # Email Alert
    msg = EmailMessage()
    msg.set_content(f"""🚨 ALERT: A gun has been detected on the webcam feed.

Camera Location: {CAMERA_LOCATION}
Time: {last_alert_time}

See attached image for details.""")

    msg['Subject'] = "Security Alert - Gun Detected"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with open(image_path, 'rb') as img_file:
        msg.add_attachment(img_file.read(), maintype='image', subtype='jpeg', filename="detection.jpg")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ssl.create_default_context()) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("✅ Email alert sent.")
    except Exception as e:
        print(f"❌ Email error: {e}")

    # WhatsApp Alert
    try:
        print(f"📲 Sending WhatsApp using SID: {TWILIO_SID}, From: {WHATSAPP_FROM}, To: {WHATSAPP_TO}")
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"🚨 ALERT: Gun detected at {CAMERA_LOCATION} on {last_alert_time}. Check admin dashboard or email for details.",
            from_=WHATSAPP_FROM,
            to=WHATSAPP_TO
        )
        print(f"✅ WhatsApp alert sent. SID: {message.sid}")
    except Exception as e:
        print(f"❌ WhatsApp error: {e}")
        traceback.print_exc()

def detection_loop():
    global alert_sent

    cap = cv2.VideoCapture(0)
    print("🔍 Starting webcam detection... Press 'q' to exit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        detections = results.xyxy[0]
        labels = results.names

        for *xyxy, conf, cls in detections:
            label = labels[int(cls)]
            if label == 'gun' and not alert_sent:
                save_path = "static/gun_detection.jpg"
                cv2.imwrite(save_path, frame)
                alert_security(save_path)
                alert_sent = True

        annotated_frame = results.render()[0]
        cv2.imshow("YOLO Gun Detection Webcam Feed", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

@app.route('/')
def admin_dashboard():
    return render_template(
        'dashboard.html',
        camera_location=CAMERA_LOCATION,
        last_alert=last_alert_time or "No alerts yet",
        image_exists=os.path.exists("static/gun_detection.jpg")
    )

if __name__ == '__main__':
    detection_thread = threading.Thread(target=detection_loop, daemon=True)
    detection_thread.start()
    app.run(debug=True)
