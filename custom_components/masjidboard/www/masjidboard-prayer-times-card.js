/**
 * MasjidBoard Prayer Times Card
 * A custom Lovelace card for Home Assistant that displays salaah times
 * from the MasjidBoard integration.
 */

const CARD_VERSION = "1.1.0";

const JUMUAH_KEYS = [
  { key: "jumuah_1", label: "Jumuah 1" },
  { key: "jumuah_2", label: "Jumuah 2" },
  { key: "jumuah_3", label: "Jumuah 3" },
];

const PRAYERS = [
  {
    name: "Fajr",
    athanKey: "fajr_athan",
    jamaahKey: "fajr_jamaah",
    icon: "M12 2L2 7v1h20V7L12 2z",
    gradient: ["#1a1a2e", "#16213e"],
  },
  {
    name: "Dhuhr",
    athanKey: "dhuhr_athan",
    jamaahKey: "dhuhr_jamaah",
    icon: "M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5z",
    gradient: ["#f6d365", "#fda085"],
  },
  {
    name: "Asr",
    athanKey: "asr_athan",
    jamaahKey: "asr_jamaah",
    icon: "M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5z",
    gradient: ["#fa709a", "#fee140"],
  },
  {
    name: "Maghrib",
    athanKey: "maghrib_athan",
    jamaahKey: "maghrib_jamaah",
    icon: "M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5z",
    gradient: ["#a18cd1", "#fbc2eb"],
  },
  {
    name: "Esha",
    athanKey: "esha_athan",
    jamaahKey: "esha_jamaah",
    icon: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z",
    gradient: ["#0c1445", "#1a237e"],
  },
];

class MasjidBoardPrayerTimesCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
  }

  static getConfigElement() {
    return document.createElement("masjidboard-prayer-times-card-editor");
  }

  static getStubConfig() {
    return { entity: "" };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define a 'next_prayer' entity");
    }
    this._config = {
      show_header: true,
      show_athan: true,
      show_extra: true,
      highlight_next: true,
      show_jumuah: "friday",
      theme: "vibrant",
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _getDeviceEntities() {
    const entity = this._hass.states[this._config.entity];
    if (!entity) return {};

    // Find all entities that share the same prefix (device)
    // The next_prayer entity is like: sensor.<device>_next_prayer
    const entityId = this._config.entity;
    const prefix = entityId.replace(/_next_prayer$/, "");

    const entities = {};
    for (const [id, state] of Object.entries(this._hass.states)) {
      if (id.startsWith(prefix + "_")) {
        const suffix = id.replace(prefix + "_", "");
        entities[suffix] = state;
      }
    }
    return entities;
  }

  _getNextPrayerName() {
    const entity = this._hass.states[this._config.entity];
    if (!entity) return null;
    return entity.state;
  }

  _getNextPrayerTime() {
    const entity = this._hass.states[this._config.entity];
    if (!entity) return null;
    return entity.attributes.time || null;
  }

  _getMasjidName() {
    const entity = this._hass.states[this._config.entity];
    if (!entity) return "Masjid";
    return entity.attributes.friendly_name?.replace(" Next Prayer", "") || "Masjid";
  }

  _formatTime(timeStr) {
    if (!timeStr || timeStr === "unavailable" || timeStr === "unknown") return "--:--";

    // timeStr is in HH:MM 24h format, convert to 12h
    const parts = timeStr.trim().split(":");
    if (parts.length < 2) return timeStr;
    let hour = parseInt(parts[0], 10);
    const minute = parts[1];
    const ampm = hour >= 12 ? "PM" : "AM";
    hour = hour % 12 || 12;
    return `${hour}:${minute} ${ampm}`;
  }

  _getTimeUntil(timeStr) {
    if (!timeStr || timeStr === "unavailable" || timeStr === "unknown") return null;
    const parts = timeStr.trim().split(":");
    if (parts.length < 2) return null;
    const now = new Date();
    const target = new Date();
    target.setHours(parseInt(parts[0], 10), parseInt(parts[1], 10), 0, 0);
    let diff = target - now;
    if (diff < 0) return null;
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  }

  _isSubtle() {
    return this._config.theme === "subtle";
  }

  _render() {
    if (!this._hass || !this._config.entity) return;

    const subtle = this._isSubtle();
    const entities = this._getDeviceEntities();
    const nextPrayer = this._getNextPrayerName();
    const nextPrayerTime = this._getNextPrayerTime();
    const masjidName = this._getMasjidName();
    const timeUntil = this._getTimeUntil(nextPrayerTime);

    // Jumuah times — only those with valid values
    const isFriday = new Date().getDay() === 5;
    const showJumuah = this._config.show_jumuah === "always" ||
      (this._config.show_jumuah !== "never" && isFriday);
    const jumuahTimes = showJumuah
      ? JUMUAH_KEYS
          .map((j) => ({ label: j.label, time: entities[j.key]?.state }))
          .filter((j) => j.time && j.time !== "unavailable" && j.time !== "unknown" && j.time.trim() !== "" && j.time.trim() !== "&nbsp;")
      : [];

    // Extra times
    const sehriEnds = entities["sehri_ends"]?.state;
    const sunrise = entities["sunrise"]?.state;
    const ishraaq = entities["ishraaq"]?.state;
    const sunset = entities["sunset"]?.state;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --card-bg: var(--ha-card-background, var(--card-background-color, #fff));
          --primary-text: var(--primary-text-color, #212121);
          --secondary-text: var(--secondary-text-color, #727272);
          --accent: var(--accent-color, #03a9f4);
          --divider: var(--divider-color, rgba(0,0,0,0.12));
        }

        ha-card {
          overflow: hidden;
          font-family: var(--ha-card-header-font-family, inherit);
        }

        .header {
          background: linear-gradient(135deg, #1b5e20, #2e7d32, #43a047);
          color: #fff;
          padding: 20px 24px;
          position: relative;
          overflow: hidden;
        }

        .header::before {
          content: '';
          position: absolute;
          top: -30%;
          right: -10%;
          width: 200px;
          height: 200px;
          background: rgba(255,255,255,0.06);
          border-radius: 50%;
        }

        .header::after {
          content: '';
          position: absolute;
          bottom: -40%;
          right: 10%;
          width: 150px;
          height: 150px;
          background: rgba(255,255,255,0.04);
          border-radius: 50%;
        }

        .header-top {
          display: flex;
          align-items: center;
          gap: 12px;
          position: relative;
          z-index: 1;
        }

        .mosque-icon {
          width: 36px;
          height: 36px;
          opacity: 0.9;
        }

        .header-text h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          letter-spacing: 0.3px;
        }

        .header-text .subtitle {
          margin: 2px 0 0;
          font-size: 12px;
          opacity: 0.8;
          font-weight: 400;
        }

        .next-prayer-banner {
          margin-top: 16px;
          background: rgba(255,255,255,0.15);
          border-radius: 12px;
          padding: 12px 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          position: relative;
          z-index: 1;
          backdrop-filter: blur(4px);
        }

        .next-label {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 1.5px;
          opacity: 0.85;
          margin-bottom: 2px;
        }

        .next-name {
          font-size: 22px;
          font-weight: 700;
        }

        .next-time-block {
          text-align: right;
        }

        .next-time {
          font-size: 22px;
          font-weight: 700;
          font-variant-numeric: tabular-nums;
        }

        .next-countdown {
          font-size: 12px;
          opacity: 0.85;
          margin-top: 2px;
        }

        .prayers-container {
          padding: 8px 16px 12px;
        }

        .prayer-row {
          display: flex;
          align-items: center;
          padding: 12px 8px;
          border-radius: 10px;
          transition: background 0.2s ease;
          position: relative;
        }

        .prayer-row:not(:last-child) {
          border-bottom: 1px solid var(--divider);
        }

        .prayer-row.active {
          background: var(--accent);
          color: #fff;
          border-bottom-color: transparent;
          box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }

        .prayer-row.active + .prayer-row {
          border-top-color: transparent;
        }

        .prayer-row.active .prayer-name {
          color: #fff;
        }

        .prayer-row.active .time-athan,
        .prayer-row.active .time-jamaah {
          color: rgba(255,255,255,0.9);
        }

        .prayer-row.active .time-jamaah {
          color: #fff;
          font-weight: 700;
        }

        .prayer-row.active .label {
          color: rgba(255,255,255,0.7);
        }

        .prayer-icon-wrapper {
          width: 36px;
          height: 36px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 12px;
          flex-shrink: 0;
        }

        .prayer-row:nth-child(1) .prayer-icon-wrapper { background: rgba(26,26,46,0.1); }
        .prayer-row:nth-child(2) .prayer-icon-wrapper { background: rgba(246,211,101,0.15); }
        .prayer-row:nth-child(3) .prayer-icon-wrapper { background: rgba(250,112,154,0.12); }
        .prayer-row:nth-child(4) .prayer-icon-wrapper { background: rgba(161,140,209,0.15); }
        .prayer-row:nth-child(5) .prayer-icon-wrapper { background: rgba(26,35,126,0.1); }

        .prayer-row.active .prayer-icon-wrapper {
          background: rgba(255,255,255,0.2);
        }

        .prayer-icon {
          width: 20px;
          height: 20px;
        }

        .prayer-name {
          font-size: 15px;
          font-weight: 600;
          color: var(--primary-text);
          flex: 1;
          min-width: 0;
        }

        .times-block {
          display: flex;
          gap: 20px;
          align-items: center;
          text-align: right;
        }

        .time-col {
          min-width: 70px;
        }

        .label {
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--secondary-text);
          margin-bottom: 1px;
        }

        .time-athan {
          font-size: 13px;
          color: var(--secondary-text);
          font-variant-numeric: tabular-nums;
        }

        .time-jamaah {
          font-size: 15px;
          font-weight: 600;
          color: var(--primary-text);
          font-variant-numeric: tabular-nums;
        }

        .extras {
          display: flex;
          justify-content: space-around;
          padding: 10px 16px 14px;
          border-top: 1px solid var(--divider);
        }

        .extra-item {
          text-align: center;
        }

        .extra-label {
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--secondary-text);
          margin-bottom: 2px;
        }

        .extra-time {
          font-size: 13px;
          font-weight: 500;
          color: var(--primary-text);
          font-variant-numeric: tabular-nums;
        }

        .jumuah-section {
          border-top: 1px solid var(--divider);
          padding: 10px 16px 12px;
        }

        .jumuah-header {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: var(--secondary-text);
          margin-bottom: 8px;
          padding-left: 8px;
        }

        .jumuah-times {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          padding-left: 8px;
        }

        .jumuah-chip {
          background: rgba(46, 125, 50, 0.1);
          color: var(--primary-text);
          padding: 6px 14px;
          border-radius: 20px;
          font-size: 13px;
          font-weight: 500;
          font-variant-numeric: tabular-nums;
        }

        /* Subtle theme overrides */
        .subtle .header {
          background: var(--card-bg);
          color: var(--primary-text);
          border-bottom: 1px solid var(--divider);
        }

        .subtle .header::before,
        .subtle .header::after {
          display: none;
        }

        .subtle .mosque-icon {
          color: var(--secondary-text);
        }

        .subtle .header-text .subtitle {
          color: var(--secondary-text);
          opacity: 1;
        }

        .subtle .next-prayer-banner {
          background: var(--divider);
          backdrop-filter: none;
          color: var(--primary-text);
        }

        .subtle .next-label {
          opacity: 1;
          color: var(--secondary-text);
        }

        .subtle .next-countdown {
          opacity: 1;
          color: var(--secondary-text);
        }

        .subtle .prayer-row.active {
          background: var(--divider);
          color: var(--primary-text);
          box-shadow: none;
        }

        .subtle .prayer-row.active .prayer-name {
          color: var(--primary-text);
        }

        .subtle .prayer-row.active .time-athan {
          color: var(--secondary-text);
        }

        .subtle .prayer-row.active .time-jamaah {
          color: var(--primary-text);
        }

        .subtle .prayer-row.active .label {
          color: var(--secondary-text);
        }

        .subtle .prayer-row.active .prayer-icon-wrapper {
          background: rgba(128,128,128,0.15);
        }

        .subtle .prayer-row:nth-child(1) .prayer-icon-wrapper,
        .subtle .prayer-row:nth-child(2) .prayer-icon-wrapper,
        .subtle .prayer-row:nth-child(3) .prayer-icon-wrapper,
        .subtle .prayer-row:nth-child(4) .prayer-icon-wrapper,
        .subtle .prayer-row:nth-child(5) .prayer-icon-wrapper {
          background: rgba(128,128,128,0.1);
        }

        .subtle .jumuah-chip {
          background: var(--divider);
        }

        .no-entity {
          padding: 24px;
          text-align: center;
          color: var(--secondary-text);
          font-size: 14px;
        }

        .no-entity code {
          display: block;
          margin-top: 8px;
          font-size: 12px;
          color: var(--primary-text);
          background: var(--divider);
          padding: 8px;
          border-radius: 6px;
        }
      </style>

      <ha-card class="${subtle ? "subtle" : ""}">
        ${this._hass.states[this._config.entity] ? `
          ${this._config.show_header !== false ? `
            <div class="header">
              <div class="header-top">
                <svg class="mosque-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C8 2 6 5 6 7c0 1.5.5 2.5 1 3.5V12H5l-3 9h20l-3-9h-2v-1.5c.5-1 1-2 1-3.5 0-2-2-5-6-5zm0 2c2.5 0 4 2 4 3 0 1-.5 2-1 3h-6c-.5-1-1-2-1-3 0-1 1.5-3 4-3zm-2 8h4v1h-4v-1z"/>
                </svg>
                <div class="header-text">
                  <h2>${masjidName}</h2>
                  <div class="subtitle">Prayer Times</div>
                </div>
              </div>

              ${nextPrayer ? `
                <div class="next-prayer-banner">
                  <div>
                    <div class="next-label">Next Prayer</div>
                    <div class="next-name">${nextPrayer}</div>
                  </div>
                  <div class="next-time-block">
                    <div class="next-time">${this._formatTime(nextPrayerTime)}</div>
                    ${timeUntil ? `<div class="next-countdown">in ${timeUntil}</div>` : ""}
                  </div>
                </div>
              ` : ""}
            </div>
          ` : ""}

          <div class="prayers-container">
            ${PRAYERS.map((prayer) => {
              const athanState = entities[prayer.athanKey]?.state;
              const jamaahState = entities[prayer.jamaahKey]?.state;
              const isActive = this._config.highlight_next !== false &&
                nextPrayer && nextPrayer.toLowerCase().startsWith(prayer.name.toLowerCase());

              return `
                <div class="prayer-row ${isActive ? "active" : ""}">
                  <div class="prayer-icon-wrapper">
                    <svg class="prayer-icon" viewBox="0 0 24 24" fill="currentColor">
                      ${this._getPrayerSvg(prayer.name)}
                    </svg>
                  </div>
                  <div class="prayer-name">${prayer.name}</div>
                  <div class="times-block">
                    ${this._config.show_athan !== false ? `
                      <div class="time-col">
                        <div class="label">Athan</div>
                        <div class="time-athan">${this._formatTime(athanState)}</div>
                      </div>
                    ` : ""}
                    <div class="time-col">
                      <div class="label">Jamaah</div>
                      <div class="time-jamaah">${this._formatTime(jamaahState)}</div>
                    </div>
                  </div>
                </div>
              `;
            }).join("")}
          </div>

          ${jumuahTimes.length > 0 ? `
            <div class="jumuah-section">
              <div class="jumuah-header">Jumuah</div>
              <div class="jumuah-times">
                ${jumuahTimes.map((j) => `
                  <div class="jumuah-chip">${this._formatTime(j.time)}</div>
                `).join("")}
              </div>
            </div>
          ` : ""}

          ${this._config.show_extra !== false && (sehriEnds || sunrise || sunset) ? `
            <div class="extras">
              ${sehriEnds ? `
                <div class="extra-item">
                  <div class="extra-label">Sehri Ends</div>
                  <div class="extra-time">${this._formatTime(sehriEnds)}</div>
                </div>
              ` : ""}
              ${sunrise ? `
                <div class="extra-item">
                  <div class="extra-label">Sunrise</div>
                  <div class="extra-time">${this._formatTime(sunrise)}</div>
                </div>
              ` : ""}
              ${ishraaq ? `
                <div class="extra-item">
                  <div class="extra-label">Ishraaq</div>
                  <div class="extra-time">${this._formatTime(ishraaq)}</div>
                </div>
              ` : ""}
              ${sunset ? `
                <div class="extra-item">
                  <div class="extra-label">Sunset</div>
                  <div class="extra-time">${this._formatTime(sunset)}</div>
                </div>
              ` : ""}
            </div>
          ` : ""}
        ` : `
          <div class="no-entity">
            Entity not found: <strong>${this._config.entity}</strong>
            <code>
              type: custom:masjidboard-prayer-times-card<br>
              entity: sensor.&lt;your_masjid&gt;_next_prayer
            </code>
          </div>
        `}
      </ha-card>
    `;
  }

  _getPrayerSvg(name) {
    switch (name) {
      case "Fajr":
        return `<path d="M3 15h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V9H3v2zm4 8h14v-2H7v2zm0-4h14v-2H7v2zm0-6v2h14V9H7z" opacity="0.3"/>
                <path d="M12 2L4 5v2h16V5l-8-3zm0 2.26L16.47 6H7.53L12 4.26z"/>
                <path d="M3 21h2v-2H3v2zm0-4h2v-2H3v2zm0-4h2v-2H3v2zm4 8h14v-2H7v2zm0-4h14v-2H7v2zm0-4h14v-2H7v2z"/>`;
      case "Dhuhr":
        return `<circle cx="12" cy="12" r="5" fill="currentColor"/>
                <path d="M12 1v3M12 20v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M1 12h3M20 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"
                  stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/>`;
      case "Asr":
        return `<circle cx="14" cy="12" r="4" fill="currentColor"/>
                <path d="M14 5v2M14 19v2M8.34 7.34l1.42 1.42M18.24 17.24l1.42 1.42M5 12h2M21 12h2M8.34 16.66l1.42-1.42M18.24 6.76l1.42-1.42"
                  stroke="currentColor" stroke-width="1.2" stroke-linecap="round" fill="none"/>
                <path d="M2 18h6l2-3H2z" fill="currentColor" opacity="0.3"/>`;
      case "Maghrib":
        return `<path d="M3 17h18v2H3z" fill="currentColor"/>
                <circle cx="12" cy="14" r="5" fill="currentColor"/>
                <path d="M1 17h22" stroke="currentColor" stroke-width="2"/>
                <path d="M12 6v3M7.05 8.05l2.12 2.12M16.95 8.05l-2.12 2.12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/>`;
      case "Esha":
        return `<path d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9c.83 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-1 0-.83.67-1.5 1.5-1.5H16c2.76 0 5-2.24 5-5 0-4.42-4.03-8-9-8z" fill="none" stroke="currentColor" stroke-width="1.5"/>
                <circle cx="9" cy="9" r="1.2" fill="currentColor"/>
                <circle cx="14.5" cy="8" r="1" fill="currentColor"/>
                <circle cx="7.5" cy="13" r="1" fill="currentColor"/>`;
      default:
        return `<circle cx="12" cy="12" r="8" fill="currentColor"/>`;
    }
  }

  getCardSize() {
    return 5;
  }
}

// Card editor for the UI config
class MasjidBoardPrayerTimesCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) return;

    // Find all "next_prayer" entities
    const nextPrayerEntities = Object.keys(this._hass.states)
      .filter((e) => e.endsWith("_next_prayer") && e.startsWith("sensor."))
      .sort();

    this.shadowRoot.innerHTML = `
      <style>
        .editor {
          padding: 16px;
        }
        .row {
          margin-bottom: 12px;
        }
        label {
          display: block;
          font-weight: 500;
          margin-bottom: 4px;
          font-size: 14px;
          color: var(--primary-text-color);
        }
        select, input {
          width: 100%;
          padding: 8px;
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 6px;
          background: var(--card-background-color, #fff);
          color: var(--primary-text-color);
          font-size: 14px;
          box-sizing: border-box;
        }
        .checkbox-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        .checkbox-row input {
          width: auto;
        }
      </style>
      <div class="editor">
        <div class="row">
          <label>Next Prayer Entity</label>
          <select id="entity">
            <option value="">-- Select --</option>
            ${nextPrayerEntities.map((e) => `
              <option value="${e}" ${this._config.entity === e ? "selected" : ""}>${e}</option>
            `).join("")}
          </select>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="show_header" ${this._config.show_header !== false ? "checked" : ""}>
          <label for="show_header">Show header</label>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="show_athan" ${this._config.show_athan !== false ? "checked" : ""}>
          <label for="show_athan">Show athan times</label>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="show_extra" ${this._config.show_extra !== false ? "checked" : ""}>
          <label for="show_extra">Show extra times (Sehri, Sunrise, etc.)</label>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="highlight_next" ${this._config.highlight_next !== false ? "checked" : ""}>
          <label for="highlight_next">Highlight next prayer</label>
        </div>
        <div class="row">
          <label>Style</label>
          <select id="theme">
            <option value="vibrant" ${(this._config.theme || "vibrant") === "vibrant" ? "selected" : ""}>Vibrant</option>
            <option value="subtle" ${this._config.theme === "subtle" ? "selected" : ""}>Subtle</option>
          </select>
        </div>
        <div class="row">
          <label>Show Jumuah times</label>
          <select id="show_jumuah">
            <option value="friday" ${(this._config.show_jumuah || "friday") === "friday" ? "selected" : ""}>Fridays only</option>
            <option value="always" ${this._config.show_jumuah === "always" ? "selected" : ""}>Always</option>
            <option value="never" ${this._config.show_jumuah === "never" ? "selected" : ""}>Never</option>
          </select>
        </div>
      </div>
    `;

    this.shadowRoot.getElementById("entity").addEventListener("change", (e) => {
      this._updateConfig("entity", e.target.value);
    });

    this.shadowRoot.getElementById("theme").addEventListener("change", (e) => {
      this._updateConfig("theme", e.target.value);
    });

    this.shadowRoot.getElementById("show_jumuah").addEventListener("change", (e) => {
      this._updateConfig("show_jumuah", e.target.value);
    });

    for (const id of ["show_header", "show_athan", "show_extra", "highlight_next"]) {
      this.shadowRoot.getElementById(id).addEventListener("change", (e) => {
        this._updateConfig(id, e.target.checked);
      });
    }
  }

  _updateConfig(key, value) {
    this._config = { ...this._config, [key]: value };
    const event = new CustomEvent("config-changed", {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

customElements.define("masjidboard-prayer-times-card", MasjidBoardPrayerTimesCard);
customElements.define("masjidboard-prayer-times-card-editor", MasjidBoardPrayerTimesCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "masjidboard-prayer-times-card",
  name: "MasjidBoard Prayer Times",
  description: "A visual card showing salaah times from MasjidBoard Live",
  preview: true,
  documentationURL: "https://github.com/lockhaty/masjidboard-hass",
});

console.info(
  `%c MASJIDBOARD PRAYER TIMES CARD %c v${CARD_VERSION} `,
  "color: white; background: #1b5e20; font-weight: bold; padding: 2px 6px; border-radius: 4px 0 0 4px;",
  "color: #1b5e20; background: #e8f5e9; font-weight: bold; padding: 2px 6px; border-radius: 0 4px 4px 0;"
);
