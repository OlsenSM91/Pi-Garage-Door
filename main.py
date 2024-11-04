from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import RPi.GPIO as GPIO
import time

# Set up FastAPI app
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="Secret_key_here")

# Set up GPIO
GPIO.setmode(GPIO.BCM)
RELAY_PIN = 17  # Choose your GPIO pin
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)  # Set initial state to 'off'

# Simple user authentication (demo purposes only)
USERS = {"user": "password"}

# Dependency for authentication
def get_current_user(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return request.session.get("user")

# Login page route
@app.get("/login", response_class=HTMLResponse)
async def show_login_page(request: Request):
    return HTMLResponse(get_login_page_html())

# Login route
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if USERS.get(username) == password:
        request.session["user"] = username
        return RedirectResponse(url="/", status_code=303)
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Logout route
@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/login", status_code=303)

# Main control page
@app.get("/", response_class=HTMLResponse)
async def get_control_page(request: Request):
    try:
        user = get_current_user(request)
        return HTMLResponse(get_control_page_html())
    except HTTPException:
        return HTMLResponse(get_login_page_html())

# Trigger relay route
@app.post("/trigger")
async def trigger_relay(request: Request):
    user = get_current_user(request)
    try:
        # Momentarily activate the relay (LOW is typically "on" for most relays)
        GPIO.output(RELAY_PIN, GPIO.LOW)
        time.sleep(0.5)  # Hold for 500ms
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Ensure relay turns off
        time.sleep(0.1)  # Small delay to ensure the relay has time to switch
    except Exception as e:
        print(f"Error: {e}")
        # Make sure relay is off even if there's an error
        GPIO.output(RELAY_PIN, GPIO.HIGH)
    return RedirectResponse(url="/", status_code=303)

# Ensure cleanup on exit
import atexit

def cleanup_gpio():
    try:
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Make sure relay is off
        GPIO.cleanup()
    except:
        pass  # Ignore errors during cleanup

atexit.register(cleanup_gpio)

# HTML Template for the login page
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

# HTML Template for the control page
def get_control_page_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Garage Door Control</title>
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
        .logout {
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Garage Door Clicker</h1>
        <form action="/trigger" method="post">
            <button type="submit">Open/Close</button>
        </form>
        <form action="/logout" method="get" class="logout">
            <button type="submit">Log Out</button>
        </form>
    </div>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3070)
