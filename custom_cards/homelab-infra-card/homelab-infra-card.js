class HomelabInfraCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = config || {};
    this._columns = config?.columns ?? 3;
  }

  _getStat(device, suffix) {
    return this._hass?.states[`sensor.${device}_${suffix}`]?.state ?? null;
  }

  _colorForPercent(val) {
    const n = parseFloat(val);
    if (isNaN(n)) return "#888";
    if (n > 90) return "#ef4444";
    if (n > 70) return "#f59e0b";
    return "#10b981";
  }

  _tile(device, online) {
    const cpu = this._getStat(device, "cpu_percent");
    const ram = this._getStat(device, "ram_percent");
    const disk = this._getStat(device, "disk_percent");
    const load = this._getStat(device, "load_avg");
    const dockerRunning = this._getStat(device, "docker_running");
    const dockerStopped = this._getStat(device, "docker_stopped");
    const uptime = this._hass?.states[`sensor.${device}_uptime_seconds`]?.state;

    const borderColor = !online ? "#ef4444"
      : [cpu, ram, disk].some(v => parseFloat(v) > 90) ? "#ef4444"
      : [cpu, ram, disk].some(v => parseFloat(v) > 70) ? "#f59e0b"
      : "#10b981";

    const stat = (label, val, suffix = "%") => {
      if (val === null || val === "unavailable" || val === "unknown") return "";
      const color = suffix === "%" ? this._colorForPercent(val) : "inherit";
      return `<div class="stat"><span>${label}</span><span style="color:${color}">${parseFloat(val).toFixed(1)}${suffix}</span></div>`;
    };

    const dockerRow = dockerRunning !== null && dockerRunning !== "unavailable"
      ? `<div class="stat"><span>Docker</span><span>🟢 ${dockerRunning}▲  🔴 ${dockerStopped ?? 0}▼</span></div>` : "";

    const uptimeRow = uptime && uptime !== "unavailable"
      ? (() => { const d = Math.floor(uptime/86400); const h = Math.floor((uptime%86400)/3600);
          return `<div class="stat"><span>Uptime</span><span>${d}d ${h}h</span></div>`; })() : "";

    const onlineBadge = online
      ? `<span class="badge online">● Online</span>`
      : `<span class="badge offline">● Offline</span>`;

    return `
      <div class="tile" style="border-top:3px solid ${borderColor}">
        <div class="tile-name">${device.replace(/_/g," ")}</div>
        ${onlineBadge}
        ${stat("CPU", cpu)}
        ${stat("RAM", ram)}
        ${stat("Disk", disk)}
        ${load !== null && load !== "unavailable" ? `<div class="stat"><span>Load</span><span>${parseFloat(load).toFixed(2)}</span></div>` : ""}
        ${dockerRow}
        ${uptimeRow}
      </div>`;
  }

  _render() {
    if (!this._hass) return;

    const infraDevices = [];
    for (const [entityId, state] of Object.entries(this._hass.states)) {
      if (!entityId.startsWith("binary_sensor.") || !entityId.endsWith("_online")) continue;
      const device = entityId.replace("binary_sensor.", "").replace("_online", "");
      if (!this._hass.states[`sensor.${device}_cpu_percent`]) continue;
      infraDevices.push([device, state.state === "on"]);
    }

    infraDevices.sort((a, b) => a[0].localeCompare(b[0]));
    const tiles = infraDevices.map(([d, online]) => this._tile(d, online)).join("");

    this.innerHTML = `
      <ha-card header="Infrastructure">
        <style>
          ha-card { padding: 12px 16px 16px; }
          .grid { display: grid; grid-template-columns: repeat(${this._columns}, 1fr); gap: 12px; margin-top: 8px; }
          .tile { background: rgba(var(--rgb-primary-text-color, 0,0,0),0.04); border-radius: 8px; padding: 10px; font-size: 0.85em; }
          .tile-name { font-weight: 600; font-size: 0.95em; margin-bottom: 4px; text-transform: capitalize; }
          .stat { display: flex; justify-content: space-between; padding: 2px 0; }
          .badge { font-size: 0.75em; padding: 2px 6px; border-radius: 10px; display: inline-block; margin-bottom: 6px; }
          .badge.online { color: #10b981; }
          .badge.offline { color: #ef4444; }
        </style>
        <div class="grid">${tiles || "<p style='padding:8px'>No homelab_infra devices found.</p>"}</div>
      </ha-card>`;
  }

  getCardSize() { return 4; }
  static getStubConfig() { return { columns: 3 }; }
}

customElements.define("homelab-infra-card", HomelabInfraCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "homelab-infra-card",
  name: "Homelab Infra Card",
  description: "Auto-discovering tile grid for all homelab_infra monitored machines",
});
