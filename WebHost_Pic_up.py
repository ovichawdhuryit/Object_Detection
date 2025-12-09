import cv2
import cvzone
from ultralytics import YOLO
import gradio as gr
import numpy as np


objectModel = YOLO("yolov8n.pt")

def detect_objects(image):
    img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    results = objectModel(img_bgr)

 
    for object in results:
        boxes = object.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].numpy().astype("int")
            cv2.rectangle(img_bgr, (x1, y1), (x2, y2), (50, 50, 255), 3)

            classNum = int(box.cls[0])
            className = objectModel.names[classNum]

            confidence = float(box.conf[0]) * 100
            cvzone.putTextRect(img_bgr, f"{className} | {confidence:.2f}%", [x1 + 8, y1 - 12], scale=2)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return img_rgb


iface = gr.Interface(
    fn=detect_objects,
    inputs=gr.Image(sources=["upload", "webcam"], type="numpy"),
    outputs="image",
    live=True,
    title="YOLOv8 Object Detection"
)


iface.launch(share= True)
