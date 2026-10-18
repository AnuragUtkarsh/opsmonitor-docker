import os
import socket
from datetime import datetime, timezone

import mysql.connector
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mysql"),
    "user": os.getenv("DB_USER", "opsmonitor"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "opsmonitor"),
    "connection_timeout": 3,
}

DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpsMonitor | Infrastructure Control Center</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0b1120; --panel: #151f32; --border: #2a3850;
  --text: #e5edf8; --muted: #92a3bc; --accent: #60a5fa;
  --green: #4ade80; --yellow: #fbbf24; --red: #fb7185;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font-family: Inter, system-ui, Arial, sans-serif;
}
header {
  padding: 22px 5%; border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
  gap: 15px; flex-wrap: wrap;
}
.brand { font-size: 23px; font-weight: 800; }
.brand span { color: var(--accent); }
.subtitle { color: var(--muted); font-size: 13px; margin-top: 5px; }
.live { color: var(--green); font-size: 13px; }
main { max-width: 1250px; margin: auto; padding: 28px 22px 50px; }
.section-title { font-size: 21px; margin: 0 0 6px; }
.muted { color: var(--muted); font-size: 13px; }
.metrics {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px; margin: 25px 0;
}
.metric, .panel {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 13px; padding: 20px;
}
.metric-label { color: var(--muted); font-size: 13px; }
.metric-value { font-size: 32px; font-weight: 750; margin-top: 12px; }
.green { color: var(--green); }
.yellow { color: var(--yellow); }
.blue { color: var(--accent); }
.toolbar {
  display: flex; gap: 10px; flex-wrap: wrap; margin: 20px 0;
}
input, select, button {
  background: #0e1728; border: 1px solid var(--border);
  color: var(--text); padding: 11px 13px; border-radius: 8px;
  font: inherit;
}
input { flex: 1; min-width: 190px; }
button { cursor: pointer; background: #1d4ed8; border-color: #2563eb; }
button:hover { filter: brightness(1.15); }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; white-space: nowrap; }
th, td {
  padding: 15px 12px; border-bottom: 1px solid var(--border);
  text-align: left; font-size: 13px;
}
th { color: var(--muted); font-weight: 600; }
tbody tr:hover { background: #1b2940; }
.badge {
  display: inline-block; padding: 5px 9px; border-radius: 20px;
  font-size: 11px; font-weight: 700;
}
.running { background: #123b2c; color: var(--green); }
.maintenance { background: #473617; color: var(--yellow); }
.unknown { background: #273449; color: #cbd5e1; }
.failed { background: #481f2b; color: var(--red); }
.message { padding: 18px 0; color: var(--muted); }
footer { margin-top: 20px; color: var(--muted); font-size: 12px; }

button:disabled { opacity: .5; cursor: not-allowed; }
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px; margin: 18px 0;
}
.form-grid input, .form-grid select { width: 100%; min-width: 0; }
.secondary { background: #334155; border-color: #475569; }
.danger { background: #7f1d1d; border-color: #991b1b; }
.row-actions { display: flex; align-items: center; gap: 7px; }
.row-actions select { max-width: 145px; padding: 7px; }
.row-actions button { padding: 7px 9px; }
.audit-panel { margin-top: 22px; }

@media (max-width: 760px) {
  .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  main { padding: 22px 14px; }
}
@media (max-width: 380px) {
  .metrics { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<header>
  <div>
    <div class="brand"><span>OPS</span>MONITOR</div>
    <div class="subtitle">Infrastructure inventory and service overview</div>
  </div>
  <div class="live">● Dashboard online</div>
</header>

<main>
  <h1 class="section-title">Infrastructure overview</h1>
  <div class="muted">Database-backed inventory · Refresh to fetch the latest records</div>

  <section class="metrics">
    <div class="metric">
      <div class="metric-label">TOTAL SERVERS</div>
      <div class="metric-value blue" id="total">—</div>
    </div>
    <div class="metric">
      <div class="metric-label">RUNNING</div>
      <div class="metric-value green" id="running">—</div>
    </div>
    <div class="metric">
      <div class="metric-label">MAINTENANCE</div>
      <div class="metric-value yellow" id="maintenance">—</div>
    </div>
    <div class="metric">
      <div class="metric-label">UNKNOWN STATUS</div>
      <div class="metric-value" id="unknown">—</div>
    </div>
  </section>

  <section class="panel">
    <h2 class="section-title">Server inventory</h2>
    <div class="muted" id="last-refresh">Waiting for data…</div>

    <div class="toolbar">
      <input id="search" type="search" placeholder="Search hostname or environment">
      <select id="environment">
        <option value="">All environments</option>
      </select>
      <select id="status">
        <option value="">All statuses</option>
        <option value="RUNNING">Running</option>
        <option value="MAINTENANCE">Maintenance</option>
        <option value="UNKNOWN">Unknown</option>
        <option value="FAILED">Failed</option>
      </select>
      <button id="refresh">Refresh data</button>
    </div>

    <h3>Add server</h3>
    <form id="add-form" class="form-grid">
      <input id="new-hostname" maxlength="100" required
             placeholder="Hostname, e.g. app-server-02">
      <select id="new-environment" required>
        <option value="development">Development</option>
        <option value="testing">Testing</option>
        <option value="staging">Staging</option>
        <option value="production">Production</option>
      </select>
      <select id="new-status">
        <option value="RUNNING">Running</option>
        <option value="MAINTENANCE">Maintenance</option>
        <option value="UNKNOWN">Unknown</option>
        <option value="FAILED">Failed</option>
      </select>
      <button type="submit">+ Add server</button>
    </form>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th><th>HOSTNAME</th><th>ENVIRONMENT</th>
            <th>SERVICE STATUS</th><th>CREATED AT (UTC)</th>
            <th>ACTIONS</th>
          </tr>
        </thead>
        <tbody id="servers">
          <tr><td colspan="5" class="message">Loading inventory…</td></tr>
        </tbody>
      </table>
    </div>
    <div class="message" id="message" role="status"></div>
  </section>

  <section class="panel audit-panel">
    <h2 class="section-title">Audit history</h2>
    <p class="muted">Latest database-recorded create, update and delete events.</p>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>ID</th><th>TIME</th><th>ACTION</th><th>HOSTNAME</th><th>DETAILS</th>
        </tr></thead>
        <tbody id="audit-events">
          <tr><td colspan="5" class="message">Loading audit history…</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <footer>
    OpsMonitor is a lab demonstration. Server status represents inventory data,
    not independently verified live host health.
    <br>Application container: <span id="hostname">loading…</span>
  </footer>
</main>

<script>
const $ = id => document.getElementById(id);
let inventory = [];

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;",
    '"': "&quot;", "'": "&#39;"
  }[ch]));
}

function statusClass(status) {
  const value = String(status || "UNKNOWN").toUpperCase();
  if (value === "RUNNING") return "running";
  if (value === "MAINTENANCE") return "maintenance";
  if (value === "FAILED") return "failed";
  return "unknown";
}

function renderTable() {
  const query = $("search").value.trim().toLowerCase();
  const environment = $("environment").value;
  const status = $("status").value;

  const filtered = inventory.filter(server => {
    const searchable = `${server.hostname} ${server.environment}`.toLowerCase();
    return searchable.includes(query)
      && (!environment || server.environment === environment)
      && (!status || String(server.service_status).toUpperCase() === status);
  });

  $("servers").innerHTML = filtered.length ? filtered.map(server => `
    <tr>
      <td>${server.id}</td>
      <td><strong>${escapeHtml(server.hostname)}</strong></td>
      <td>${escapeHtml(server.environment)}</td>
      <td><span class="badge ${statusClass(server.service_status)}">${escapeHtml(server.service_status)}</span></td>
      <td>${escapeHtml(server.created_at || "—")}</td>
      <td><div class="row-actions">
        <select id="status-${server.id}" aria-label="New status">
          ${["RUNNING","MAINTENANCE","UNKNOWN","FAILED"].map(s =>
            `<option value="${s}" ${s === server.service_status ? "selected" : ""}>${s}</option>`
          ).join("")}
        </select>
        <button class="secondary" onclick="updateServer(${server.id})">Save</button>
        <button class="danger" onclick="deleteServer(${server.id})">Delete</button>
      </div></td>
    </tr>
  `).join("") : '<tr><td colspan="6" class="message">No matching servers found.</td></tr>';

  $("message").textContent =
    `Showing ${filtered.length} of ${inventory.length} servers`;
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {"Content-Type": "application/json", ...(options.headers || {})}
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

async function addServer(event) {
  event.preventDefault();
  try {
    await apiRequest("/api/servers", {
      method: "POST",
      body: JSON.stringify({
        hostname: $("new-hostname").value.trim(),
        environment: $("new-environment").value,
        service_status: $("new-status").value
      })
    });
    $("add-form").reset();
    $("message").textContent = "Server added successfully.";
    await loadDashboard();
    await loadAudit();
  } catch (error) {
    $("message").textContent = error.message;
  }
}

async function updateServer(id) {
  try {
    await apiRequest(`/api/servers/${id}`, {
      method: "PATCH",
      body: JSON.stringify({service_status: $(`status-${id}`).value})
    });
    $("message").textContent = `Server ${id} updated.`;
    await loadDashboard();
    await loadAudit();
  } catch (error) {
    $("message").textContent = error.message;
  }
}

async function deleteServer(id) {
  const server = inventory.find(item => item.id === id);
  if (!server || !confirm(`Delete server "${server.hostname}"?`)) return;

  try {
    await apiRequest(`/api/servers/${id}`, {method: "DELETE"});
    $("message").textContent = `Server ${server.hostname} deleted.`;
    await loadDashboard();
    await loadAudit();
  } catch (error) {
    $("message").textContent = error.message;
  }
}

async function loadAudit() {
  const target = $("audit-events");
  try {
    const result = await apiRequest("/api/audit");
    target.innerHTML = result.events.length ? result.events.map(event => `
      <tr>
        <td>${event.id}</td>
        <td>${escapeHtml(event.event_time || "—")}</td>
        <td><span class="badge ${event.action === "DELETE" ? "failed" : "running"}">${escapeHtml(event.action)}</span></td>
        <td>${escapeHtml(event.hostname)}</td>
        <td>${escapeHtml(event.details)}</td>
      </tr>
    `).join("") : '<tr><td colspan="5" class="message">No audit events yet.</td></tr>';
  } catch (error) {
    target.innerHTML = '<tr><td colspan="5" class="message">Audit history unavailable.</td></tr>';
  }
}

async function loadDashboard() {
  $("refresh").disabled = true;
  $("refresh").textContent = "Loading…";
  $("message").textContent = "Fetching inventory from MySQL…";

  try {
    const [summaryResponse, serversResponse, healthResponse] = await Promise.all([
      fetch("/api/summary", {cache: "no-store"}),
      fetch("/api/servers", {cache: "no-store"}),
      fetch("/health", {cache: "no-store"})
    ]);

    if (!summaryResponse.ok || !serversResponse.ok || !healthResponse.ok) {
      throw new Error("One or more API requests failed");
    }

    const summary = await summaryResponse.json();
    const serverData = await serversResponse.json();
    const health = await healthResponse.json();

    inventory = serverData.servers;
    $("total").textContent = summary.total;
    $("running").textContent = summary.running;
    $("maintenance").textContent = summary.maintenance;
    $("unknown").textContent = summary.unknown;
    $("hostname").textContent = health.hostname;

    const selectedEnvironment = $("environment").value;
    const environments = [...new Set(inventory.map(s => s.environment))].sort();
    $("environment").innerHTML =
      '<option value="">All environments</option>' +
      environments.map(env =>
        `<option value="${escapeHtml(env)}">${escapeHtml(env)}</option>`
      ).join("");
    if (environments.includes(selectedEnvironment)) {
      $("environment").value = selectedEnvironment;
    }

    $("last-refresh").textContent =
      "Last refreshed: " + new Date().toLocaleString();
    renderTable();
  } catch (error) {
    $("message").textContent =
      "Unable to load dashboard data. Check API and database logs.";
    $("servers").innerHTML =
      '<tr><td colspan="5" class="message">Inventory unavailable.</td></tr>';
    console.error(error);
  } finally {
    $("refresh").disabled = false;
    $("refresh").textContent = "Refresh data";
  }
}

$("add-form").addEventListener("submit", addServer);
$("refresh").addEventListener("click", loadDashboard);
$("search").addEventListener("input", renderTable);
$("environment").addEventListener("change", renderTable);
$("status").addEventListener("change", renderTable);

loadDashboard();
loadAudit();
</script>
</body>
</html>
"""


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_servers():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, hostname, environment, service_status, created_at
            FROM servers
            ORDER BY id
        """)
        rows = cursor.fetchall()
        for row in rows:
            if row["created_at"]:
                row["created_at"] = row["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        cursor.close()
        return rows
    finally:
        connection.close()


@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD)


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "opsmonitor-api",
        "hostname": socket.gethostname(),
    }), 200


@app.route("/api/status")
def api_status():
    try:
        connection = get_connection()
        connection.close()
        db_status = "connected"
        http_status = 200
    except mysql.connector.Error:
        app.logger.exception("Database connectivity check failed")
        db_status = "unavailable"
        http_status = 503

    return jsonify({
        "application": "running",
        "database": db_status,
        "hostname": socket.gethostname(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }), http_status


@app.route("/api/servers")
def api_servers():
    try:
        servers = fetch_servers()
        return jsonify({"count": len(servers), "servers": servers}), 200
    except mysql.connector.Error:
        app.logger.exception("Unable to fetch server inventory")
        return jsonify({"error": "Database unavailable"}), 503


@app.route("/api/summary")
def api_summary():
    try:
        connection = get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(UPPER(service_status) = 'RUNNING'), 0) AS running,
                    COALESCE(SUM(UPPER(service_status) = 'MAINTENANCE'), 0) AS maintenance,
                    COALESCE(SUM(
                        UPPER(service_status) NOT IN
                        ('RUNNING', 'MAINTENANCE', 'FAILED')
                    ), 0) AS unknown
                FROM servers
            """)
            summary = cursor.fetchone()
            cursor.close()
        finally:
            connection.close()

        return jsonify({key: int(value) for key, value in summary.items()}), 200
    except mysql.connector.Error:
        app.logger.exception("Unable to fetch inventory summary")
        return jsonify({"error": "Database unavailable"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


ALLOWED_STATUSES = {"RUNNING", "MAINTENANCE", "UNKNOWN", "FAILED"}
ALLOWED_ENVIRONMENTS = {"development", "testing", "staging", "production"}


def write_audit(cursor, server_id, action, hostname, details):
    cursor.execute(
        """INSERT INTO audit_events
           (server_id, action, hostname, details)
           VALUES (%s, %s, %s, %s)""",
        (server_id, action, hostname, details),
    )


@app.route("/api/servers", methods=["POST"])
def create_server():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Send a JSON object"}), 400

    hostname = payload.get("hostname")
    environment = payload.get("environment")
    status = payload.get("service_status", "UNKNOWN")

    if not isinstance(hostname, str) or not hostname.strip() or len(hostname.strip()) > 100:
        return jsonify({"error": "hostname must be 1-100 characters"}), 400
    if not isinstance(environment, str) or environment not in ALLOWED_ENVIRONMENTS:
        return jsonify({"error": "Invalid environment"}), 400
    if not isinstance(status, str) or status not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid service_status"}), 400

    hostname = hostname.strip()
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO servers (hostname, environment, service_status)
               VALUES (%s, %s, %s)""",
            (hostname, environment, status),
        )
        server_id = cursor.lastrowid
        write_audit(cursor, server_id, "CREATE", hostname,
                    f"Created in {environment} with status {status}")
        connection.commit()
        cursor.close()
        return jsonify({"message": "Server created", "id": server_id}), 201
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({"error": "Hostname already exists"}), 409
    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Create server failed")
        return jsonify({"error": "Database operation failed"}), 503
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.route("/api/servers/<int:server_id>", methods=["PATCH"])
def update_server(server_id):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        return jsonify({"error": "Send a non-empty JSON object"}), 400

    allowed_fields = {"hostname", "environment", "service_status"}
    if set(payload) - allowed_fields:
        return jsonify({"error": "Unsupported field supplied"}), 400

    updates = {}
    if "hostname" in payload:
        value = payload["hostname"]
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 100:
            return jsonify({"error": "hostname must be 1-100 characters"}), 400
        updates["hostname"] = value.strip()
    if "environment" in payload:
        if not isinstance(payload["environment"], str) or payload["environment"] not in ALLOWED_ENVIRONMENTS:
            return jsonify({"error": "Invalid environment"}), 400
        updates["environment"] = payload["environment"]
    if "service_status" in payload:
        if not isinstance(payload["service_status"], str) or payload["service_status"] not in ALLOWED_STATUSES:
            return jsonify({"error": "Invalid service_status"}), 400
        updates["service_status"] = payload["service_status"]

    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, hostname, environment, service_status FROM servers WHERE id=%s",
            (server_id,),
        )
        current = cursor.fetchone()
        if not current:
            cursor.close()
            return jsonify({"error": "Server not found"}), 404

        values = {key: updates.get(key, current[key])
                  for key in ("hostname", "environment", "service_status")}

        cursor.execute(
            """UPDATE servers SET hostname=%s, environment=%s,
               service_status=%s WHERE id=%s""",
            (values["hostname"], values["environment"],
             values["service_status"], server_id),
        )
        write_audit(
            cursor, server_id, "UPDATE", values["hostname"],
            f"Updated {current['hostname']}: environment={values['environment']}, "
            f"status={values['service_status']}",
        )
        connection.commit()
        cursor.close()
        return jsonify({"message": "Server updated", "server": values}), 200
    except mysql.connector.IntegrityError:
        if connection:
            connection.rollback()
        return jsonify({"error": "Hostname already exists"}), 409
    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Update server failed")
        return jsonify({"error": "Database operation failed"}), 503
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.route("/api/servers/<int:server_id>", methods=["DELETE"])
def delete_server(server_id):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, hostname FROM servers WHERE id=%s", (server_id,))
        server = cursor.fetchone()
        if not server:
            cursor.close()
            return jsonify({"error": "Server not found"}), 404

        cursor.execute("DELETE FROM servers WHERE id=%s", (server_id,))
        write_audit(cursor, server_id, "DELETE", server["hostname"],
                    f"Deleted server {server['hostname']}")
        connection.commit()
        cursor.close()
        return jsonify({"message": "Server deleted", "id": server_id}), 200
    except mysql.connector.Error:
        if connection:
            connection.rollback()
        app.logger.exception("Delete server failed")
        return jsonify({"error": "Database operation failed"}), 503
    finally:
        if connection and connection.is_connected():
            connection.close()


@app.route("/api/audit")
def audit_events():
    try:
        connection = get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT id, server_id, action, hostname, details, event_time
                   FROM audit_events ORDER BY id DESC LIMIT 100"""
            )
            events = cursor.fetchall()
            for event in events:
                if event["event_time"]:
                    event["event_time"] = event["event_time"].strftime("%Y-%m-%d %H:%M:%S")
            cursor.close()
        finally:
            connection.close()
        return jsonify({"count": len(events), "events": events}), 200
    except mysql.connector.Error:
        app.logger.exception("Audit query failed")
        return jsonify({"error": "Database unavailable"}), 503
