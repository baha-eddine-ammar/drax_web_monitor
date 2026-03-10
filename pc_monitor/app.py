from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import AppConfig, get_static_dir, get_template_dir, load_config
from .monitor import SystemMonitor
from .network_utils import ServerIdentity, get_server_identity


class DashboardRuntime:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.monitor = SystemMonitor()
        self.identity = get_server_identity(config.port)
        self.latest_metrics = self.monitor.collect(self.identity.ip_address)

    def refresh(self) -> None:
        self.identity = get_server_identity(self.config.port)
        self.latest_metrics = self.monitor.collect(self.identity.ip_address)


def create_app() -> FastAPI:
    config = load_config()
    runtime = DashboardRuntime(config)
    templates = Jinja2Templates(directory=str(get_template_dir()))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _print_startup_banner(runtime.identity, runtime.config.port)
        refresh_task = asyncio.create_task(_refresh_loop(app))
        try:
            yield
        finally:
            refresh_task.cancel()
            with suppress(asyncio.CancelledError):
                await refresh_task

    app = FastAPI(
        title="LAN PC Monitor",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.runtime = runtime
    app.state.templates = templates
    app.mount("/static", StaticFiles(directory=str(get_static_dir())), name="static")

    @app.get("/")
    async def dashboard(request: Request):
        current_runtime: DashboardRuntime = request.app.state.runtime
        return request.app.state.templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "dashboard_url": current_runtime.identity.dashboard_url,
                "refresh_seconds": current_runtime.config.refresh_seconds,
            },
        )

    @app.get("/api/metrics")
    async def current_metrics(request: Request) -> JSONResponse:
        runtime_state: DashboardRuntime = request.app.state.runtime
        return JSONResponse(runtime_state.latest_metrics)

    @app.websocket("/ws")
    async def websocket_metrics(websocket: WebSocket) -> None:
        await websocket.accept()
        runtime_state: DashboardRuntime = websocket.scope["app"].state.runtime

        try:
            while True:
                await websocket.send_json(runtime_state.latest_metrics)
                await asyncio.sleep(runtime_state.config.refresh_seconds)
        except WebSocketDisconnect:
            return

    return app


async def _refresh_loop(app: FastAPI) -> None:
    runtime_state: DashboardRuntime = app.state.runtime

    while True:
        try:
            runtime_state.refresh()
        except Exception as exc:
            runtime_state.latest_metrics["monitor_error"] = str(exc)
        await asyncio.sleep(runtime_state.config.refresh_seconds)


def _print_startup_banner(identity: ServerIdentity, port: int) -> None:
    divider = "=" * 68
    print(divider, flush=True)
    print("PC Monitor Server is running", flush=True)
    print(f"Hostname       : {identity.hostname}", flush=True)
    print(f"Local IP       : {identity.ip_address}", flush=True)
    print(f"Port           : {port}", flush=True)
    print("Bind Address   : 0.0.0.0", flush=True)
    print(f"Dashboard URL  : {identity.dashboard_url}", flush=True)
    print(divider, flush=True)
    print("Open this dashboard from another PC on the same network:", flush=True)
    print(identity.dashboard_url, flush=True)
    print("", flush=True)
    print("To stop the server, press Ctrl+C in this window.", flush=True)
    print("", flush=True)


app = create_app()


def main() -> None:
    config = app.state.runtime.config
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.port,
        access_log=False,
        log_level="warning",
        server_header=False,
        date_header=False,
    )


if __name__ == "__main__":
    main()
