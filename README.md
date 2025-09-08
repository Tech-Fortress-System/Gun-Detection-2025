# Gun Detection Security System 🔫🚨

A real-time dual-camera security system using YOLOv8 to detect firearms from a thermal camera feed, send alerts via WhatsApp and email, log incidents to a local SQLite database, and display a live dashboard using Flask.

---

## 📌 Features

- 🔍 Real-time gun detection using **YOLOv8**
- 🎥 Dual-camera input: HD + Thermal
- 📩 Sends alert with snapshots via **Email** and **WhatsApp**
- 🗃 Logs alerts to **SQLite**
- 🌐 Live web dashboard with Flask (view history, stream video)

---

## 💻 Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/Tech-Fortress-Systems/yolov5.git
cd yolov5

2. Set Up Python Environment
Use Python 3.8 or newer:

python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

3. Install Dependencies
bash

pip install -r requirements.txt

🔐 Environment Variables
Create a .env file in the root folder and fill in the following:


# YOLOv8 model weights
MODEL_WEIGHTS=yolov8m.pt

# Confidence and cooldown settings
MIN_CONFIDENCE=0.6
CONFIRM_FRAMES=3
COOLDOWN_SECONDS=30

# Email settings (Gmail recommended)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_email_password
EMAIL_RECEIVER=receiver_email@example.com

# Twilio WhatsApp settings
TWILIO_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
WHATSAPP_FROM=whatsapp:+14155238886   # Twilio sandbox number
WHATSAPP_TO=whatsapp:+27xxxxxxxxx     # Your WhatsApp number

📷 Camera Setup
HD Camera should be available at index 0

Thermal Camera should be available at index 1

You can adjust these inside the script:

python

hd_cam = cv2.VideoCapture(0)
thermal_cam = cv2.VideoCapture(1)
# Gun-Detection-2025
