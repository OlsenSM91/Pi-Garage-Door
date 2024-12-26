from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import RPi.GPIO as GPIO
import time
import aiohttp
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import logging
import sys

# Configurable Settings
DOOR_OPEN_ALERT_MINUTES = 15  # Minutes before sending door open alert
NOTIFICATION_COOLDOWN_MINUTES = 15  # Minutes between repeated notifications
CHECK_INTERVAL_SECONDS = 60  # How often to check door state

# GPIO Pin Configuration
RELAY_PIN = 17  # Physical pin 11
SENSOR_PIN = 27  # Physical pin 13

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('garage.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set up FastAPI app
app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "default_secret_key")
)

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Enable pull-up resistor
GPIO.output(RELAY_PIN, GPIO.HIGH)  # Initialize relay to OFF state

# Discord webhook configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
last_notification_time = None
door_open_time = None

# User authentication
USERS = {
    os.getenv("USERNAME", "admin"): os.getenv("PASSWORD", "admin")
}

# Background task to check door state
async def check_door_state():
    global door_open_time, last_notification_time
    logger.info("Starting door state monitoring")
    
    while True:
        try:
            current_state = GPIO.input(SENSOR_PIN)
            if current_state == 1:  # Door is open
                if door_open_time is None:
                    door_open_time = datetime.now()
                    logger.info("Door opened at %s", door_open_time)
                elif (datetime.now() - door_open_time) > timedelta(minutes=DOOR_OPEN_ALERT_MINUTES):
                    if last_notification_time is None or \
                       (datetime.now() - last_notification_time) > timedelta(minutes=NOTIFICATION_COOLDOWN_MINUTES):
                        await send_discord_notification(
                            f"⚠️ Garage door has been open for more than {DOOR_OPEN_ALERT_MINUTES} minutes!"
                        )
                        last_notification_time = datetime.now()
            else:  # Door is closed
                if door_open_time is not None:
                    logger.info("Door closed after being open since %s", door_open_time)
                door_open_time = None
        except Exception as e:
            logger.error("Error in door state monitoring: %s", e)
        
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

async def send_discord_notification(message):
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord webhook URL not configured")
        return
        
    async with aiohttp.ClientSession() as session:
        webhook_data = {"content": message}
        try:
            async with session.post(DISCORD_WEBHOOK_URL, json=webhook_data) as response:
                if response.status != 204:
                    logger.error("Failed to send Discord notification: %s", response.status)
                else:
                    logger.info("Discord notification sent successfully")
        except Exception as e:
            logger.error("Error sending Discord notification: %s", e)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting garage door control application")
    asyncio.create_task(check_door_state())

def get_current_user(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return request.session.get("user")

def get_door_state():
    try:
        state = "open" if GPIO.input(SENSOR_PIN) == 1 else "closed"
        logger.debug("Door state checked: %s", state)
        return state
    except Exception as e:
        logger.error("Error reading door state: %s", e)
        return "unknown"

@app.get("/login", response_class=HTMLResponse)
async def show_login_page(request: Request):
    return HTMLResponse(get_login_page_html())

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if USERS.get(username) == password:
        request.session["user"] = username
        logger.info("Successful login for user: %s", username)
        return RedirectResponse(url="/", status_code=303)
    else:
        logger.warning("Failed login attempt for username: %s", username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/logout")
async def logout(request: Request):
    user = request.session.get("user")
    request.session.pop("user", None)
    logger.info("User logged out: %s", user)
    return RedirectResponse(url="/login", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def get_control_page(request: Request):
    try:
        user = get_current_user(request)
        return HTMLResponse(get_control_page_html(get_door_state()))
    except HTTPException:
        return HTMLResponse(get_login_page_html())

@app.get("/door-state")
async def door_state(request: Request):
    user = get_current_user(request)
    state = get_door_state()
    return {"state": state}

@app.post("/trigger")
async def trigger_relay(request: Request):
    user = get_current_user(request)
    logger.info("Door trigger activated by user: %s", user)
    
    try:
        GPIO.output(RELAY_PIN, GPIO.LOW)  # Activate relay
        time.sleep(0.5)  # Hold for 500ms
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Deactivate relay
        time.sleep(0.1)  # Small delay to ensure relay has switched
        logger.info("Relay triggered successfully")
    except Exception as e:
        logger.error("Error triggering relay: %s", e)
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Ensure relay is off
    
    return RedirectResponse(url="/", status_code=303)

def cleanup_gpio():
    try:
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Ensure relay is off
        GPIO.cleanup()
        logger.info("GPIO cleanup completed")
    except:
        logger.error("Error during GPIO cleanup")

import atexit
atexit.register(cleanup_gpio)

def get_login_page_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
        }
        .container {
            width: 90%;
            max-width: 400px;
            margin: auto;
            text-align: center;
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        input, button {
            padding: 10px;
            margin-top: 10px;
            width: 100%;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        button {
            background-color: #007BFF;
            color: white;
            cursor: pointer;
            border: none;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Login</h1>
        <form action="/login" method="post">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Log In</button>
        </form>
    </div>
</body>
</html>"""

def get_control_page_html(door_state):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Garage Door Control</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
        }}
        .container {{
            text-align: center;
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }}
        .garage-button {{
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: linear-gradient(145deg, #e6e6e6, #ffffff);
            box-shadow: 5px 5px 10px #d9d9d9, -5px -5px 10px #ffffff;
            border: none;
            cursor: pointer;
            margin: 20px;
            position: relative;
            transition: all 0.2s;
        }}
        .garage-button:active {{
            box-shadow: inset 5px 5px 10px #d9d9d9, inset -5px -5px 10px #ffffff;
        }}
        .status-indicator {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            margin: 10px auto;
            background-color: {'#4CAF50' if door_state == 'open' else '#f44336'};
        }}
        .status-text {{
            font-size: 18px;
            margin: 10px 0;
            color: {'#4CAF50' if door_state == 'open' else '#f44336'};
        }}
        .logout {{
            margin-top: 15px;
        }}
        .logout button {{
            padding: 10px 20px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        .logout button:hover {{
            background-color: #0056b3;
        }}
    </style>
    <script>
        function updateDoorState() {{
            fetch('/door-state')
                .then(response => response.json())
                .then(data => {{
                    const indicator = document.querySelector('.status-indicator');
                    const statusText = document.querySelector('.status-text');
                    if (data.state === 'open') {{
                        indicator.style.backgroundColor = '#4CAF50';
                        statusText.style.color = '#4CAF50';
                        statusText.textContent = 'Door is Open';
                    }} else {{
                        indicator.style.backgroundColor = '#f44336';
                        statusText.style.color = '#f44336';
                        statusText.textContent = 'Door is Closed';
                    }}
                }});
        }}
        
        setInterval(updateDoorState, 5000);  // Update every 5 seconds
    </script>
</head>
<body>
    <div class="container">
        <h1>Garage Door Control</h1>
        <div class="status-indicator"></div>
        <div class="status-text">Door is {door_state.capitalize()}</div>
        <form action="/trigger" method="post">
            <button type="submit" class="garage-button"></button>
        </form>
        <form action="/logout" method="get" class="logout">
            <button type="submit">Log Out</button>
        </form>
    </div>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    try:
        logger.info("Starting server on port 3070")
        uvicorn.run(app, host="0.0.0.0", port=3070)
    except Exception as e:
        logger.error("Server failed to start: %s", e)
        cleanup_gpio()
