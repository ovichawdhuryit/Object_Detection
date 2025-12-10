import cv2
import cvzone
from ultralytics import YOLO
import gradio as gr
import numpy as np
from groq import Groq
import serial
import serial.tools.list_ports
import time
import re
import os

def force_release_port(port):
    try:
        import subprocess
        result = subprocess.check_output(["lsof", port]).decode()
        for line in result.splitlines()[1:]:
            pid = int(line.split()[1])
            os.system(f"kill -9 {pid}")
            print(f"Force-killed process {pid} using {port}")
    except:
        pass

def get_arduino_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        dn = p.device.lower()
        if "usbmodem" in dn or "usbserial" in dn or "tty.usb" in dn:
            return p.device
    return None

def open_serial_port():
    port = get_arduino_port()
    if not port:
        print("Arduino not detected.")
        return None
    force_release_port(port)
    try:
        ser = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)
        print("Arduino connected on:", port)
        return ser
    except Exception as e:
        print("Failed to open serial port:", e)
        return None

arduino = open_serial_port()


def send_to_arduino(text, expect_ack=True):
    if arduino is None:
        print("No Arduino connected → skip send:", text)
        return False
    line = (text.strip() + "\n").encode()
    try:
        arduino.write(line)
        arduino.flush()
    except Exception as e:
        print("Serial write error:", e)
        return False
    if not expect_ack:
        return True
    timeout = time.time() + 2.5
    while time.time() < timeout:
        try:
            if arduino.in_waiting:
                resp = arduino.readline().decode("utf-8", errors="ignore").strip()
                if resp.startswith("ACK"):
                    return True
        except:
            break
        time.sleep(0.05)
    print("⚠ No ACK received for:", text)
    return False


objectModel = YOLO("yolov8n.pt")


client = Groq(api_key="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")

prompt_template = (
    "You are a microwave cooking assistant.\n"
    "Provide instructions in this EXACT format and DO NOT mention watts.\n\n"
    "Example:\n"
    "Food: Hot Dog\n"
    "Temperature: 75°C\n"
    "Time: 1.5 minutes\n\n"
    "Food: {food}\n"
)

def llama_generate(food_label):
    prompt = prompt_template.format(food=food_label)
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.15
        )
        instructions = response.choices[0].message.content.strip()
        return instructions
    except Exception as e:
        print("Groq error:", e)
        return "AI error."


def parse_instructions(text):
    temp = None
    t = None
    m1 = re.search(r"[Tt]emperature.*?(\d+\.?\d*)", text)
    m2 = re.search(r"[Tt]ime.*?(\d+\.?\d*)", text)
    if m1: temp = float(m1.group(1))
    if m2: t = float(m2.group(1))
    return temp, t

def detect_and_predict(image):
    img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    results = objectModel(img_bgr)
    label = None
    best_area = 0

    for r in results:
        boxes = getattr(r, "boxes", None)
        if boxes is None:
            continue
        xyxy = boxes.xyxy.cpu().numpy()
        conf = boxes.conf.cpu().numpy()
        clss = boxes.cls.cpu().numpy()
        for i, box in enumerate(xyxy):
            x1, y1, x2, y2 = map(int, box)
            area = (x2 - x1) * (y2 - y1)
            name = objectModel.names[int(clss[i])]
            if area > best_area:
                best_area = area
                label = name
            cv2.rectangle(img_bgr, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cvzone.putTextRect(img_bgr, f"{name} {conf[i]:.2f}", (x1, y1 - 12), scale=1)

    if not label:
        instructions = "No food detected."
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), instructions

    instructions = llama_generate(label)
    temp, tm = parse_instructions(instructions)

    print("\n----- AI Output -----")
    print(instructions)
    print("---------------------\n")

    if temp is not None:
        send_to_arduino(f"TEMP:{temp}")
    if tm is not None:
        send_to_arduino(f"TIME:{tm}")

    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), instructions


iface = gr.Interface(
    fn=detect_and_predict,
    inputs=gr.Image(type="numpy", sources=["webcam", "upload"]),
    outputs=[gr.Image(type="numpy"), gr.Textbox(label="AI Instructions")],
    live=True,
    title="Babar_DorBar",
    description="Detect food, compute temperature/time using LLaMA-3.1, and send to Arduino."
)

if __name__ == "__main__":
    iface.launch(share=False)
