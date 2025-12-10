# Babar_DorBar – AI-Powered Microwave Cooking Assistant

Babar_DorBar is an intelligent cooking assistant that detects food using a webcam, generates microwave cooking instructions via **LLaMA-3.1**, and communicates with an **Arduino-controlled microwave system** to automatically set temperature and cooking time. The system also provides real-time feedback on an **LCD display**.

---

## Features

- Real-time **food detection** using YOLOv8.
- AI-generated **cooking instructions** (temperature & time) from Groq’s LLaMA-3.1 model.
- Automatic communication with an **Arduino** to control a microwave or heating system.
- **PID-controlled heating** with temperature feedback from a DS18B20 sensor.
- Live **LCD display** showing temperature, setpoint, cooking time, and errors.
- Cross-platform support (Windows, macOS, Linux) for the Python interface.

---

## Repository Structure

```
Babar_DorBar/
│
├─ python_app/
│  ├─ main.py              # Python code for webcam detection, AI interaction, and serial communication
│  └─ requirements.txt     # Python dependencies
│
├─ arduino_firmware/
│  └─ microwave.ino        # Arduino code for PID temperature control and LCD display
│
├─ README.md               # This file
└─ assets/                 # Optional: screenshots or demo videos
```

---

## Requirements

### Python

- Python 3.10+
- Packages (can be installed via `pip install -r requirements.txt`):
  - `opencv-python`
  - `cvzone`
  - `ultralytics`
  - `gradio`
  - `numpy`
  - `groq`
  - `pyserial`

### Hardware

- Arduino board (Uno, Mega, etc.)
- DS18B20 temperature sensor
- SSR (Solid State Relay) for controlling microwave/heater
- LCD I2C display (16x2)
- Breadboard, wires, and basic electronic components

---

## Installation

1. **Clone the repository**:

```bash
git clone https://github.com/<your-username>/Babar_DorBar.git
cd Babar_DorBar/python_app
```

2. **Install Python dependencies**:

```bash
pip install -r requirements.txt
```

3. **Upload Arduino firmware**:

- Open `arduino_firmware/microwave.ino` in the Arduino IDE.
- Select your board and port.
- Upload to the Arduino.

---

## Usage

1. **Connect Arduino** with the temperature sensor, SSR, and LCD setup.
2. **Run Python app**:

```bash
python main.py
```

3. **Web Interface**:

- A Gradio web interface will launch automatically.
- Select `webcam` or `upload` an image to detect food.
- The system detects food, sends the label to LLaMA-3.1, generates cooking instructions, and sends commands to the Arduino.
- Arduino executes PID-controlled heating and updates the LCD in real-time.

---

## How It Works

1. **Food Detection**  
   - YOLOv8 detects food objects in the image frame.
   - The object with the largest bounding box is considered the main food item.

2. **AI Cooking Instructions**  
   - Detected food label is sent to **Groq LLaMA-3.1** model.
   - Returns `Temperature` and `Time` in a strict format.

3. **Arduino Control**  
   - Python sends commands via **serial**:  
     - `TEMP:<value>` → sets the target temperature  
     - `TIME:<value>` → starts cooking for the specified duration  
   - Arduino uses **PID control** to maintain the temperature.
   - LCD shows current temperature, setpoint, remaining cooking time, and error percentage.

---

## Example Output

- **Python Console**:

```
Food detected: Hot Dog
AI Instructions:
Temperature: 75°C
Time: 1.5 minutes
Sending to Arduino...
```

- **LCD Display**:

```
T: 65.2°C Set: 75°C
Left: 1.2m Err: -13.1%
```

---

## Notes

- Ensure **Arduino is connected** before running the Python app.
- The `force_release_port` function attempts to close other processes using the serial port if it’s busy.
- PID parameters (`Kp`, `Ki`, `Kd`) in the Arduino code may need tuning depending on your heating system.
- LLaMA-3.1 API key is required for Groq integration (`client = Groq(api_key="YOUR_KEY")`).

---

## Future Improvements

- Add **support for multiple food items** detection in one frame.
- GUI controls for manual override of temperature and time.
- Save cooking history and AI recommendations for analysis.
- Integrate with **smart kitchen appliances**.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

