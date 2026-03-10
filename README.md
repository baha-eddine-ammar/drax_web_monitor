# LAN PC Monitor

Windows-first local monitoring server for a single PC.

The app always monitors the machine on which it is running. Nothing is hardcoded to your own PC. If your boss runs it on another computer, it automatically shows that computer's hostname, IP address, CPU, RAM, disks, network usage, uptime, and current live state.

## Chosen deployment strategy

This project is packaged as a standalone Windows executable with PyInstaller.

Why this is the recommended delivery method:

- The boss does not need to install Python
- The boss does not need to install `pip`, Node.js, Git, or VS Code
- The release can be sent as one folder or one ZIP file
- `setup.bat` can prepare the machine and start the app
- `run_app.bat` can start the app later with one double-click
- `stop_app.bat` can stop the app with one double-click

## What to send to your boss

After you run `build.bat`, send one of these:

1. Best option: `dist\LAN-PC-Monitor.zip`
2. Or send the full folder: `release\LAN-PC-Monitor`

Do not send the source code folder to your boss. Send only the packaged release.

## Recommended release folder structure

```text
LAN-PC-Monitor/
  PCMonitorServer.exe
  config.json
  setup.bat
  run_app.bat
  stop_app.bat
  README.md
```

## Exact build steps for you

Use these steps on your own machine to create the release package:

1. Open this project folder
2. Double-click `build.bat`
3. Wait for the PyInstaller build to finish
4. When it finishes, open `release\LAN-PC-Monitor`
5. Optional: if created, send `dist\LAN-PC-Monitor.zip`
6. Otherwise send the full folder `release\LAN-PC-Monitor`

`build.bat` does all of this automatically:

1. Creates `.venv` if needed
2. Installs build dependencies
3. Builds `PCMonitorServer.exe`
4. Creates the release folder
5. Copies `setup.bat`, `run_app.bat`, `stop_app.bat`, `config.json`, and `README.md`
6. Tries to create a ZIP package

## Exact install and run steps for your boss

Your boss should do only this:

1. Download the ZIP file or receive the release folder
2. Extract it if it is a ZIP file
3. Open the `LAN-PC-Monitor` folder
4. Double-click `setup.bat`
5. If Windows asks about firewall access, click `Allow access` for Private networks
6. The app will start and show a message like this:

```text
PC Monitor Server is running
Hostname       : IT-PC-01
Local IP       : 192.168.1.80
Port           : 5000
Bind Address   : 0.0.0.0
Dashboard URL  : http://192.168.1.80:5000
```

After that:

- The boss can use `run_app.bat` to start it later
- The boss can use `stop_app.bat` to stop it later

## What the app does on each machine

This app is machine-independent.

Wherever it is installed and run:

- it detects that computer's hostname
- it detects that computer's best LAN IPv4 address
- it monitors that computer's CPU
- it monitors that computer's memory
- it monitors that computer's disks
- it monitors that computer's network state and usage
- it monitors that computer's uptime

Examples:

- Install on PC A: dashboard shows PC A
- Install on PC B: dashboard shows PC B
- Install on PC C: dashboard shows PC C

## LAN access behavior

The server is configured for LAN use:

- it binds to `0.0.0.0`
- it uses the configured port from `config.json`
- it prints the detected LAN IPv4 address
- it shows the dashboard URL clearly in the console
- other PCs on the same network can open the dashboard in a browser

Example LAN link:

```text
http://192.168.1.80:5000
```

## Config file

You can change the listening port and refresh interval in `config.json`.

Example:

```json
{
  "port": 5000,
  "refresh_seconds": 2
}
```

Notes:

- The default port is `5000`
- The app still binds to `0.0.0.0`
- If you change the port, the printed dashboard URL changes automatically

## Windows firewall setup

`setup.bat` tries to add a Windows Firewall rule for the configured TCP port on Private networks.

Important notes:

- Adding a firewall rule may require administrator rights
- If `setup.bat` is not run as administrator, it will continue and explain that the rule could not be added automatically
- On first launch, Windows may show a security popup

If the popup appears:

1. Click `Allow access`
2. Make sure `Private networks` is allowed
3. Click `OK`

If no popup appears and another PC still cannot connect:

1. Open `Windows Defender Firewall`
2. Click `Advanced settings`
3. Open `Inbound Rules`
4. Click `New Rule...`
5. Choose `Port`
6. Choose `TCP`
7. Enter the port from `config.json` such as `5000`
8. Choose `Allow the connection`
9. Apply it to `Private` networks
10. Save the rule

## How another PC opens the dashboard

1. Make sure both PCs are on the same company network
2. Start the app on the monitored PC
3. Read the dashboard URL shown in the console
4. On another PC, open that exact address in a browser

Example:

```text
http://192.168.1.80:5000
```

## How to stop and restart

To stop:

1. Double-click `stop_app.bat`
2. Or press `Ctrl+C` in the server window

To restart:

1. Stop it first
2. Double-click `run_app.bat`

## Troubleshooting if another PC cannot access the dashboard

Check these in order:

1. Make sure the app window is still open on the monitored PC
2. Make sure the printed IP address is a LAN IP such as `192.168.x.x`, `10.x.x.x`, or `172.16.x.x`
3. Make sure both computers are connected to the same local network
4. Make sure the browser is opening the full address including the port
5. Make sure Windows Firewall allowed the app or the configured port
6. Make sure no other program is already using the same port

If the printed IP address is `127.0.0.1`:

- the machine does not currently have a usable LAN IPv4 address
- check Ethernet or Wi-Fi connection
- check whether the network adapter is enabled
- then restart the app

If the server says the port is already in use:

1. Run `stop_app.bat`
2. Start the app again with `run_app.bat`

If another PC still cannot connect:

1. Open the dashboard locally on the monitored PC with `http://127.0.0.1:5000`
2. If that works locally but not from another PC, the problem is usually firewall or network isolation
3. If it does not work locally either, restart the app

## Source project files

These files are used to create the packaged release:

```text
pc_monitor/
  __init__.py
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
requirements.txt
run.py
run_app.bat
setup.bat
start.bat
stop_app.bat
stop.bat
```

## Developer note

The packaged executable is the recommended delivery format for a non-technical Windows user. The source-mode `start.bat` script is still available for development, but it is not the preferred way to deliver the app to your boss.
