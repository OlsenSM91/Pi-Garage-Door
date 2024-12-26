# Raspberry Pi Garage Door Controller
This guide will walk you through setting up a Python-based FastAPI web application for controlling a garage door using a Raspberry Pi. The application features secure authentication, magnetic door state sensing, and Discord notifications.

### Web Interface
![Screenshot_20241225-154737](https://github.com/user-attachments/assets/cb148c9d-74b3-48d4-b380-c0a7f9beb5ed)

## Features
- Web-based control interface
- Real-time door state monitoring
- Discord notifications for extended door-open states
- Secure authentication
- Mobile-responsive design

## Prerequisites
- Raspberry Pi (tested on Raspberry Pi 3B v1.2 or newer)
- Fresh Raspberry Pi OS image installed and updated
- Relay module
- Magnetic door sensor (N.O. configuration)
- Discord webhook URL (for notifications)
- Internet connection

### Magnetic Switch
![PXL_20241225_222001517](https://github.com/user-attachments/assets/ac9f2f03-4f29-413d-8947-4549086ffc75)
Amazon (Magentic Switch): https://a.co/d/gcJET4m

### RasPi GPIO
![raspiGPIO](https://github.com/user-attachments/assets/107e742a-1dbc-4f3c-867a-7b0221bf64e2)
Amazon (RasPi 3b V1.2): https://a.co/d/5volc3C

### RasPi to Relay
![PXL_20241226_002035419](https://github.com/user-attachments/assets/5a891e68-31e6-45d1-9f2b-f2a89aa163c5)
Amazon (Relay Module): https://a.co/d/3oeR67d

## Hardware Setup

![GPIO-Pinout-Diagram-2](https://github.com/user-attachments/assets/53726df5-c269-41d4-a0fc-1eb06af6135b)

### Relay Connection
1. Connect the relay module to the Raspberry Pi:
   - **VCC** → 5V power (Pin 2)
   - **GND** → Ground (Pin 6)
   - **IN1** → GPIO17 (Pin 11)

### Magnetic Door Sensor Connection
1. Mount the magnetic sensor components:
   - Install contact switch on the door track
   - Install magnet on the door
   - Maintain ≤3" (76mm) gap between contact and magnet when closed
2. Connect the magnetic sensor:
   - Wire 1 → GPIO27 (Pin 13)
   - Wire 2 → Ground (Pin 14)

## Software Setup

### Step 1: System Preparation
Update your Raspberry Pi OS:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-pip python3-venv python3-full
```

### Step 2: Create Project Directory and Virtual Environment
```bash
# Create project directory
cd ~
git clone https://github.com/yourusername/garage-door-controller.git
cd garage-door-controller

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Python Packages
While in the virtual environment:
```bash
pip3 install fastapi uvicorn python-dotenv aiohttp RPi.GPIO
```

### Step 4: Environment Configuration
1. Create your environment file:
```bash
cp .envtemplate .env
chmod 600 .env
```

2. Edit the .env file:
```bash
nano .env
```

Add your configuration:
```ini
DISCORD_WEBHOOK_URL="your_discord_webhook_url_here"
SECRET_KEY="your_random_secret_key_here"
USERNAME="your_chosen_username"
PASSWORD="your_chosen_password"
```

### Step 5: Service Configuration
1. Create the service file:
```bash
sudo nano /etc/systemd/system/garage_door_app.service
```

2. Add the service configuration:
```ini
[Unit]
Description=Garage Door Opener Web App
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/garage-door-controller
Environment="PATH=/home/pi/garage-door-controller/venv/bin"
ExecStart=/home/pi/garage-door-controller/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl enable garage_door_app
sudo systemctl start garage_door_app
```

### Step 6: Access the Web Interface
Open a web browser and navigate to:
```
http://<your-raspberry-pi-ip>:3070
```

Log in with the credentials you set in the .env file.

## Configuration Options

You can adjust the following settings in `main.py`:
```python
DOOR_OPEN_ALERT_MINUTES = 15      # Time before sending alert
NOTIFICATION_COOLDOWN_MINUTES = 15 # Time between notifications
CHECK_INTERVAL_SECONDS = 60        # Door state check frequency
```

## Maintenance

### Viewing Logs
View application logs:
```bash
tail -f ~/garage-door-controller/garage.log
```

View service logs:
```bash
sudo journalctl -u garage_door_app -f
```

### Service Control
```bash
# Stop the service
sudo systemctl stop garage_door_app

# Start the service
sudo systemctl start garage_door_app

# Restart the service
sudo systemctl restart garage_door_app

# Check status
sudo systemctl status garage_door_app
```

## Troubleshooting

### Hardware Issues
1. **Relay Not Triggering**
   - Verify 5V power connection
   - Check GPIO17 connection
   - Confirm ground connection

2. **Door Sensor Issues**
   - Verify magnet alignment
   - Check GPIO27 connection
   - Confirm ground connection

### Software Issues
1. **Service Won't Start**
   - Check logs: `sudo journalctl -u garage_door_app -f`
   - Verify file permissions
   - Confirm Python package installation
   - Ensure virtual environment is properly configured

2. **Discord Notifications Not Working**
   - Verify webhook URL in .env
   - Check internet connectivity
   - Review application logs

3. **Web Interface Not Accessible**
   - Confirm service is running
   - Check firewall settings
   - Verify network connectivity

## Security Recommendations
1. Change default credentials immediately
2. Use a strong SECRET_KEY
3. Keep system and packages updated
4. Consider setting up HTTPS with a reverse proxy
5. Regularly monitor logs for unauthorized access attempts

## Support
For issues and feature requests, please create an issue in the GitHub repository.
