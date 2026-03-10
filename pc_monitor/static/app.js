const refreshSeconds = window.MONITOR_CONFIG?.refreshSeconds ?? 2;
const reconnectDelayMs = 3000;

let socket = null;
let reconnectTimer = null;

function byId(id) {
    return document.getElementById(id);
}

function setText(id, value) {
    const element = byId(id);
    if (element) {
        element.textContent = value;
    }
}

function formatNumber(value, digits = 1) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toFixed(digits) : "--";
}

function formatGigabytes(value) {
    const number = Number(value);
    return Number.isFinite(number) ? `${number.toFixed(1)} GB` : "--";
}

function formatInteger(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toLocaleString() : "--";
}

function formatBytes(value) {
    const units = ["B", "KB", "MB", "GB", "TB"];
    let number = Number(value);

    if (!Number.isFinite(number) || number < 0) {
        return "--";
    }

    let unitIndex = 0;
    while (number >= 1024 && unitIndex < units.length - 1) {
        number /= 1024;
        unitIndex += 1;
    }

    const digits = number >= 100 ? 0 : 1;
    return `${number.toFixed(digits)} ${units[unitIndex]}`;
}

function formatDate(value) {
    if (!value) {
        return "--";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}

function toneForPercent(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
        return "neutral";
    }
    if (number >= 85) {
        return "alert";
    }
    if (number >= 65) {
        return "warn";
    }
    return "good";
}

function setTone(id, tone) {
    const element = byId(id);
    if (element) {
        element.dataset.tone = tone;
    }
}

function renderDisks(disks) {
    const tbody = byId("disks_body");
    if (!tbody) {
        return;
    }

    if (!Array.isArray(disks) || disks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No accessible drives found.</td></tr>';
        return;
    }

    tbody.innerHTML = disks.map((disk) => {
        const usage = Number(disk.usage_percent) || 0;
        return `
            <tr>
                <td>${disk.mount}</td>
                <td>${formatGigabytes(disk.used_gb)} / ${formatGigabytes(disk.total_gb)}</td>
                <td>${formatGigabytes(disk.free_gb)}</td>
                <td class="usage-cell">
                    ${formatNumber(usage)}%
                    <div class="usage-bar">
                        <div class="usage-fill" style="width: ${Math.max(0, Math.min(usage, 100))}%"></div>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

function updateMetrics(data) {
    if (!data) {
        return;
    }

    const diskTotal = Number(data.disk_total_gb) || 0;
    const diskUsed = Number(data.disk_used_gb) || 0;
    const diskUsagePercent = diskTotal > 0 ? (diskUsed / diskTotal) * 100 : 0;

    setText("hostname", data.hostname || "Unknown PC");
    setText("pc_name", data.hostname || "--");
    setText("ip_address", data.ip_address || "--");
    setText("online_status", data.online ? "Online on LAN" : "Network limited");
    setText("cpu_percent", formatNumber(data.cpu_percent));
    setText("ram_percent", formatNumber(data.ram_percent));
    setText("disk_usage_percent", formatNumber(diskUsagePercent));
    setText("os_name", data.os_name || "--");
    setText("username", data.username || "--");
    setText("ram_used_total", `${formatGigabytes(data.ram_used_gb)} used / ${formatGigabytes(data.ram_total_gb)} total`);
    setText("ram_available", formatGigabytes(data.ram_available_gb));
    setText("disk_total_summary", `${formatGigabytes(data.disk_used_gb)} used / ${formatGigabytes(data.disk_free_gb)} free`);
    setText("download_mbps", formatNumber(data.network?.download_mbps, 2));
    setText("upload_mbps", formatNumber(data.network?.upload_mbps, 2));
    setText("bytes_recv", formatBytes(data.network?.bytes_recv));
    setText("bytes_sent", formatBytes(data.network?.bytes_sent));
    setText("interface_name", data.network?.interface_name || "--");
    setText("connection_type", data.network?.connection_type || "--");
    setText("connection_state", data.network?.connection_state || "--");
    setText("link_speed", data.network?.link_speed_mbps ? `${formatInteger(data.network.link_speed_mbps)} Mbps` : "Unknown");
    setText("subnet_mask", data.network?.subnet_mask || "--");
    setText("broadcast_ip", data.network?.broadcast_ip || "--");
    setText("mac_address", data.network?.mac_address || "--");
    setText("mtu_value", data.network?.mtu ? formatInteger(data.network.mtu) : "Unknown");
    setText("duplex_value", data.network?.duplex || "--");
    setText(
        "packets_summary",
        `Rx ${formatInteger(data.network?.packets_recv)} / Tx ${formatInteger(data.network?.packets_sent)}`
    );
    setText(
        "errors_summary",
        `Err ${formatInteger(data.network?.errin)}:${formatInteger(data.network?.errout)} | Drop ${formatInteger(data.network?.dropin)}:${formatInteger(data.network?.dropout)}`
    );
    setText("uptime_human", data.uptime_human || "--");
    setText("last_updated", formatDate(data.last_updated));
    setText(
        "network_scope",
        data.network?.counter_scope === "adapter" ? "Active adapter counters" : "All adapter counters"
    );
    setText("network_state_badge", data.network?.connection_state || "Adapter status");

    if (data.cpu_temperature_c === null || data.cpu_temperature_c === undefined) {
        setText("cpu_temp", "Temp: N/A");
    } else {
        setText("cpu_temp", `Temp: ${formatNumber(data.cpu_temperature_c)} C`);
    }

    const dashboardLink = byId("dashboard-link");
    if (dashboardLink && data.ip_address) {
        dashboardLink.href = `${window.location.protocol}//${data.ip_address}:${window.location.port || 5000}`;
        dashboardLink.textContent = `http://${data.ip_address}:${window.location.port || 5000}`;
    }

    setTone("cpu-card", toneForPercent(data.cpu_percent));
    setTone("ram-card", toneForPercent(data.ram_percent));
    setTone("disk-card", toneForPercent(diskUsagePercent));
    setTone("status-pill", data.network?.is_up ? "good" : "warn");

    renderDisks(data.disks);
}

async function fetchMetrics() {
    try {
        const response = await fetch("/api/metrics", { cache: "no-store" });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        updateMetrics(data);
        setText("connection_mode", "Live updates active");
    } catch (error) {
        setText("connection_mode", "Waiting for monitor data...");
        window.console.error("Metrics fetch failed:", error);
    }
}

function scheduleReconnect() {
    if (reconnectTimer) {
        return;
    }

    reconnectTimer = window.setTimeout(() => {
        reconnectTimer = null;
        connectWebSocket();
    }, reconnectDelayMs);
}

function connectWebSocket() {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        return;
    }

    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(`${wsProtocol}://${window.location.host}/ws`);

    socket.addEventListener("open", () => {
        setText("connection_mode", "Connected to live stream");
    });

    socket.addEventListener("message", (event) => {
        try {
            updateMetrics(JSON.parse(event.data));
        } catch (error) {
            window.console.error("Invalid WebSocket payload:", error);
        }
    });

    socket.addEventListener("error", () => {
        socket.close();
    });

    socket.addEventListener("close", () => {
        setText("connection_mode", "Reconnecting to live stream...");
        scheduleReconnect();
    });
}

document.addEventListener("DOMContentLoaded", () => {
    fetchMetrics();
    connectWebSocket();
    window.setInterval(fetchMetrics, Math.max(refreshSeconds * 15000, 15000));
});
