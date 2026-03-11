# LAN PC Monitor

LAN PC Monitor is a simple self-hosted monitoring dashboard for Windows.

When it runs on a PC, it monitors that same PC and shares a live dashboard on the local network. Other PCs on the same LAN can open the shown link in a browser and view the current machine state.

## Technologies Used

- Python
- FastAPI
- Uvicorn
- psutil
- Jinja2
- HTML
- CSS
- JavaScript
- WebSocket
- PyInstaller

## Project Structure

```text
pc_monitor/
  app.py
  config.py
  monitor.py
  network_utils.py
  templates/
    index.html
  static/
    app.js
    style.css
build.bat
config.json
pc_monitor.spec
README.md
run.py
run_app.bat
setup.bat
stop_app.bat
```

## Data Flow

1. The app starts on the current Windows PC.
2. `monitor.py` collects live local system data from that same machine.
3. `network_utils.py` detects the best LAN IPv4 address.
4. `app.py` starts the FastAPI server on `0.0.0.0`.
5. The dashboard page is served to browsers on the local network.
6. Live metrics are pushed to the browser through WebSocket updates.
7. Any PC on the same LAN can open the shown URL and view the current machine state.

## Release Package

Send this packaged folder or ZIP to the user:

```text
LAN-PC-Monitor/
  PCMonitorServer.exe
  config.json
  setup.bat
  run_app.bat
  stop_app.bat
  README.md
```

## How To Download And Run

1. Download `LAN-PC-Monitor.zip`.
2. Extract the ZIP.
3. Open the extracted `LAN-PC-Monitor` folder.
4. Double-click `setup.bat`.
5. If Windows asks for firewall access, click `Allow access`.
6. Wait for the app window to show the dashboard link.
7. Open that link in a browser.

Example:

```text
http://192.168.1.80:5000
```

## Run Later

- To start the app again, double-click `run_app.bat`
- To stop the app, double-click `stop_app.bat`

