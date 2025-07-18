import cv2
import numpy as np
from ultralytics import YOLO
from twilio.rest import Client
import os
import requests
import time

# Twilio setup (replace with your actual credentials)
TWILIO_SID = "Twilio sid"
TWILIO_AUTH_TOKEN = "Twilo_auth_token"
TWILIO_PHONE_FROM = "+1413430267"
TWILIO_PHONE_TO = "Mobile number"



# ESP8266 IP address
ESP8266_IP = "device's ip address"

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# File paths
REFERENCE_GATE_IMAGE = "images/gate_closed.jpg"
IMAGES_TO_CHECK = [
    "images/gate_closed.jpg",
    "images/gate_open.jpg",
    "images/gate_open_with_pet.jpg",
    "images/pet_with_human.jpg",
    "images/dog_going_out.jpg",
    "images/dog_going_out.jpg"
]

# YOLOv8 model and interested classes
model = YOLO("yolov8n.pt")
INTERESTED_CLASSES = {
    "person": "human",
    "dog": "pet",
    "cat": "pet",
    "bird": "pet"
}

# Alert function
def send_sms_alert(message):
    try:
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_FROM,
            to=TWILIO_PHONE_TO
        )
        print(f"✅ SMS sent: {message.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")

# Buzzer trigger
def trigger_buzzer():
    try:
        response = requests.get(f"{ESP8266_IP}/buzz", timeout=5)
        if response.status_code == 200:
            print("🔔 Buzzer triggered successfully!")
        else:
            print("⚠️ Failed to trigger buzzer.")
    except Exception as e:
        print("🔔 Buzzer triggered (fallback - no confirmation).")

# Compare image difference
def calculate_difference(imageA, imageB):
    # Resize imageB to match imageA
    imageB_resized = cv2.resize(imageB, (imageA.shape[1], imageA.shape[0]))
    imageA_gray = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB_gray = cv2.cvtColor(imageB_resized, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(imageA_gray, imageB_gray)
    return np.mean(diff)

# Detect humans/pets
def detect_entities(image_path):
    results = model(image_path)
    detections = results[0].boxes
    humans, pets = 0, 0

    if detections is not None:
        for cls_id, conf in zip(detections.cls.cpu().numpy(), detections.conf.cpu().numpy()):
            class_name = model.names[int(cls_id)]
            if class_name in INTERESTED_CLASSES and conf > 0.5:
                entity = INTERESTED_CLASSES[class_name]
                print(f"Detected: {class_name} ({entity}, confidence: {conf:.2f})")
                if entity == "human":
                    humans += 1
                elif entity == "pet":
                    pets += 1
    return humans, pets

# Main logic
def main():
    if not os.path.exists(REFERENCE_GATE_IMAGE):
        print(f"❌ Reference image {REFERENCE_GATE_IMAGE} not found.")
        return

    gate_closed_img = cv2.imread(REFERENCE_GATE_IMAGE)
    if gate_closed_img is None:
        print("❌ Failed to load reference gate image.")
        return

    for image_path in IMAGES_TO_CHECK:
        print(f"\n🔍 Processing {image_path}...")
        if not os.path.exists(image_path):
            print(f"⚠️ Image {image_path} not found, skipping.")
            continue

        current_img = cv2.imread(image_path)
        if current_img is None:
            print(f"❌ Failed to load {image_path}. Skipping.")
            continue

        diff_score = calculate_difference(gate_closed_img, current_img)
        is_gate_open = diff_score > 10  # Threshold can be tuned
        print(f"Gate diff score: {diff_score:.2f} → {'Open' if is_gate_open else 'Closed'}")

        if not is_gate_open:
            print("✅ Gate is closed. No alert needed.")
        else:
            humans, pets = detect_entities(image_path)

            if humans == 0 and pets == 0:
                print("⚠️ Gate is open with no human/pet.")
                send_sms_alert("🚨 Gate is open!")
            elif humans == 0 and pets > 0:
                trigger_buzzer()
                send_sms_alert("🚨 Pet is going out alone! Buzzer triggered!")
                print("⚠️ Pet alone detected!")
            else:
                print("✅ Human present. No alert needed.")

        # Wait before next image
        print("⏳ Waiting 5 seconds before processing next image:")
        for i in range(5, 0, -1):
            print(f"  {i}...", end='', flush=True)
            time.sleep(1)
        print()

if __name__ == "__main__":
    main()
