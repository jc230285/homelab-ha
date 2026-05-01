class ArrMediaCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    if (!config.device) throw new Error("'device' is required");
    this._config = config;
    this._device = config.device.toLowerCase().replace(/\s+/g, "_");
  }

  _getEntity(suffix) {
    const key = `sensor.${this._device}_${suffix}`;
    return this._hass?.states[key];
  }

  _getBinaryEntity(suffix) {
    const key = `binary_sensor.${this._device}_${suffix}`;
    return this._hass?.states[key];
  }

  _render() {
    if (!this._hass || !this._config) return;

    const status = this._getEntity("status")?.state ?? "unknown";
    const queue = this._getEntity("queue_count")?.state ?? "—";
    const wanted = this._getEntity("wanted_count")?.state ?? "—";
    const missing = this._getEntity("missing_count")?.state ?? "—";
    const healthProblem = this._getBinaryEntity("health")?.state === "on";
    const healthMsg = this._getEntity("health_message");
    const issues = healthMsg?.attributes?.issues ?? [];

    const isOnline = status !== "unknown" && status !== "unavailable";
    const statusColor = isOnline ? (healthProblem ? "#f59e0b" : "#10b981") : "#ef4444";
    const statusDot = `<span style="color:${statusColor}">●</span>`;

    const calNote = `<em style="color:#888">See HA Calendar for upcoming items</em>`;

    const issueRows = issues.length
      ? issues.map(i => `<div class="issue">⚠ ${i.message}</div>`).join("")
      : `<div class="issue ok">✓ No health issues</div>`;

    this.innerHTML = `
      <ha-card>
        <style>
          ha-card { padding: 16px; font-family: var(--primary-font-family); }
          .header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
          .title { font-size: 1.1em; font-weight: 600; }
          .badges { display: flex; gap: 8px; margin-left: auto; font-size: 0.85em; }
          .badge { background: rgba(0,0,0,0.1); border-radius: 12px; padding: 2px 8px; }
          .section-title { font-size: 0.8em; font-weight: 600; color: #888; text-transform: uppercase; margin: 12px 0 4px; }
          .issue { padding: 4px 0; font-size: 0.9em; }
          .issue.ok { color: #10b981; }
          .calendar-note { font-size: 0.85em; padding: 4px 0; }
        </style>
        <div class="header">
          <div class="title">${statusDot} ${this._config.device}</div>
          <div class="badges">
            <span class="badge" title="Queue">⬇ ${queue}</span>
            <span class="badge" title="Wanted">🎯 ${wanted}</span>
            <span class="badge" title="Missing cutoff">✂ ${missing}</span>
          </div>
        </div>
        <div class="section-title">Upcoming</div>
        <div class="calendar-note">${calNote}</div>
        <div class="section-title">Health</div>
        ${issueRows}
      </ha-card>
    `;
  }

  getCardSize() { return 3; }

  static getConfigElement() {
    return document.createElement("arr-media-card-editor");
  }

  static getStubConfig() {
    return { device: "Sonarr" };
  }
}

customElements.define("arr-media-card", ArrMediaCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "arr-media-card",
  name: "Arr Media Card",
  description: "Shows status, queue, wanted, and health for a Sonarr/Radarr/Lidarr/Prowlarr instance",
});
