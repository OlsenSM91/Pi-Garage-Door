# Raspberry Pi Relay Control Web App

This guide will walk you through setting up a Python-based FastAPI web application on a fresh Raspberry Pi OS image. The application allows authenticated users to control a relay connected to the GPIO pins through a web interface.

## Prerequisites
- Raspberry Pi (tested on Raspberry Pi 3b v1.2 or newer)
- Fresh Raspberry Pi OS image installed and updated
- Python 3 installed
- Relay module with leads (GND, IN1, IN2, VCC)
- Internet connection

## Hardware Setup
1. **Connect the relay module to the Raspberry Pi:**
   - **VCC** to a 3.3V or 5V pin on the Raspberry Pi (e.g., Pin 1 or 2).
   - **GND** to a ground pin (e.g., Pin 6).
   - **IN1** to GPIO17 (Pin 11) or any available GPIO pin.
2. **Ensure that the relay is securely connected and powered.**

## Software Setup
### Step 1: Update the Raspberry Pi OS
Run the following commands to update your system:
```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Python and Pip
Ensure Python 3 and pip are installed:
```bash
sudo apt install python3 python3-pip -y
```

### Step 3: Install Required Python Packages
Create a `requirements.txt` file with the following content:
```plaintext
fastapi
uvicorn
starlette
itsdangerous
RPi.GPIO
```

Install the dependencies:
```bash
pip3 install -r requirements.txt
```

### Step 4: Create the FastAPI Application
Copy the provided `main.py` code into a new file:
```bash
nano main.py
```
Paste the code and save it (`Ctrl + X`, then `Y` and `Enter`).

### Step 5: Run the Application
Start the FastAPI application using Uvicorn:
```bash
python3 main.py
```

### Step 6: Access the Web App
Open a web browser and navigate to:
```
http://<your-raspberry-pi-ip>:3070
```
Log in with the default credentials provided in the `main.py` file.

## Notes
- Ensure your Raspberry Pi is on the same network as your computer.
- Modify the GPIO pin in the `main.py` if connecting to a different pin.

## Troubleshooting
- **ModuleNotFoundError**: If you encounter missing module errors, ensure they are installed via `pip3 install <module-name>`.
- **Permission issues**: Run the app with `sudo` if GPIO access is restricted:
  ```bash
  sudo python3 main.py
  ```

## Safety Precautions
- Double-check all wiring before powering on the Raspberry Pi.
- Do not exceed the voltage and current ratings of the relay.

Enjoy controlling your relay through the web application!
