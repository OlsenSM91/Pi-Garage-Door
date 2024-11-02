from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import RPi.GPIO as GPIO

# Set up FastAPI app
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Set up GPIO
GPIO.setmode(GPIO.BCM)
RELAY_PIN = 17  # Choose your GPIO pin
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)

# Simple user authentication (demo purposes only)
USERS = {"user": "password"}

# Dependency for authentication
def get_current_user(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return request.session.get("user")

# Login route
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if USERS.get(username) == password:
        request.session["user"] = username
        return HTMLResponse(get_control_page_html())
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Logout route
@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return HTMLResponse("<p>Logged out successfully.</p>")

# Main control page
@app.get("/", response_class=HTMLResponse)
async def get_control_page(request: Request):
    user = get_current_user(request)
    return HTMLResponse(get_control_page_html())

# Trigger relay route
@app.post("/trigger")
async def trigger_relay(request: Request):
    user = get_current_user(request)
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    # Optional: Add a small delay to control pulse timing
    GPIO.output(RELAY_PIN, GPIO.LOW)
    return {"status": "Relay triggered"}

# Ensure cleanup on exit
import atexit

def cleanup_gpio():
    GPIO.cleanup()

atexit.register(cleanup_gpio)

# HTML Template embedded in Python
def get_control_page_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relay Control</title>
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
            text-align: center;
            background: #fff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        button {
            padding: 10px 20px;
            font-size: 18px;
            margin-top: 20px;
            cursor: pointer;
            border: none;
            border-radius: 5px;
            background-color: #007BFF;
            color: white;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Control Relay</h1>
        <form action="/trigger" method="post">
            <button type="submit">Trigger Relay</button>
        </form>
    </div>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3070)