from flask import Flask, jsonify
import sqlite3
from datetime import datetime
import json
import psutil

app = Flask(__name__)
DB_NAME = "system_health.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cpu REAL NOT NULL,
            memory REAL NOT NULL,
            disk REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_current_metrics():
    cpu = round(psutil.cpu_percent(interval=1), 1)
    memory = round(psutil.virtual_memory().percent, 1)
    disk = round(psutil.disk_usage("/").percent, 1)

    status = "Healthy"
    if cpu > 80 or memory > 80 or disk > 80:
        status = "Warning"
    if cpu > 90 or memory > 90 or disk > 90:
        status = "Critical"

    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "status": status
    }


def save_metrics(metrics):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO health_logs (timestamp, cpu, memory, disk, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metrics["cpu"],
        metrics["memory"],
        metrics["disk"],
        metrics["status"]
    ))
    conn.commit()
    conn.close()


def get_history(limit=50):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, cpu, memory, disk, status
        FROM health_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def base_styles():
    return """
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: white;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 1100px;
            margin: auto;
        }

        .card {
            background: #1e293b;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }

        h1 {
            color: #38bdf8;
            text-align: center;
            margin-bottom: 10px;
        }

        h2 {
            color: #e2e8f0;
            text-align: center;
            margin-top: 28px;
        }

        .subtitle {
            color: #94a3b8;
            text-align: center;
            margin-bottom: 30px;
        }

        .top-nav {
            text-align: center;
            margin-bottom: 25px;
        }

        .top-nav a {
            display: inline-block;
            margin: 6px 10px;
            color: #38bdf8;
            text-decoration: none;
            font-weight: bold;
        }

        .top-nav a:hover {
            text-decoration: underline;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        .summary-card {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px;
            text-align: center;
        }

        .summary-card h3 {
            margin: 0 0 8px 0;
            color: #94a3b8;
            font-size: 15px;
        }

        .summary-card p {
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }

        .panel {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 24px;
            color: #cbd5e1;
            line-height: 1.6;
        }

        .alerts-box {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 24px;
            color: #e2e8f0;
        }

        .alerts-box ul {
            text-align: left;
            margin: 10px 0 0 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: #0f172a;
            border-radius: 12px;
            overflow: hidden;
        }

        th, td {
            padding: 12px;
            border-bottom: 1px solid #334155;
            text-align: center;
        }

        th {
            background: #111827;
            color: #e2e8f0;
        }

        tr:hover {
            background: #1f2937;
        }

        .chart-box {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-top: 24px;
        }

        .muted {
            color: #94a3b8;
        }

        @media (max-width: 900px) {
            .summary-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 600px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """


@app.route("/")
def dashboard():
    metrics = get_current_metrics()
    save_metrics(metrics)

    alerts = []
    if metrics["cpu"] > 90:
        alerts.append(f"🚨 CPU critical at {metrics['cpu']}%")
    elif metrics["cpu"] > 80:
        alerts.append(f"⚠️ CPU high at {metrics['cpu']}%")

    if metrics["memory"] > 90:
        alerts.append(f"🚨 Memory critical at {metrics['memory']}%")
    elif metrics["memory"] > 80:
        alerts.append(f"⚠️ Memory high at {metrics['memory']}%")

    if metrics["disk"] > 90:
        alerts.append(f"🚨 Disk critical at {metrics['disk']}%")
    elif metrics["disk"] > 80:
        alerts.append(f"⚠️ Disk high at {metrics['disk']}%")

    if alerts:
        alerts_html = "<ul>" + "".join(f"<li>{a}</li>" for a in alerts) + "</ul>"
    else:
        alerts_html = "<p class='muted'>No active alerts right now.</p>"

    color = "#22c55e"
    if metrics["status"] == "Warning":
        color = "#f59e0b"
    elif metrics["status"] == "Critical":
        color = "#ef4444"

    return f"""
    <html>
    <head>
        <title>System Health Checker</title>
        <meta http-equiv="refresh" content="5">
        {base_styles()}
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="top-nav">
                    <a href="/">Dashboard</a>
                    <a href="/history">History</a>
                    <a href="/charts">Charts</a>
                    <a href="/api/metrics" target="_blank">API Metrics</a>
                    <a href="/api/history" target="_blank">API History</a>
                </div>

                <h1>System Health Checker</h1>
                <p class="subtitle">Single-node system monitoring for CPU, memory, and disk health</p>

                <div class="panel">
                    <strong>Overview:</strong> This application monitors a single system node, captures CPU,
                    memory, and disk usage, stores periodic snapshots in SQLite, exposes JSON APIs,
                    and visualizes historical performance trends through charts and history views.
                </div>

                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>CPU</h3>
                        <p style="color:{'#ef4444' if metrics['cpu'] > 90 else '#f59e0b' if metrics['cpu'] > 80 else '#22c55e'};">{metrics['cpu']}%</p>
                    </div>
                    <div class="summary-card">
                        <h3>Memory</h3>
                        <p style="color:{'#ef4444' if metrics['memory'] > 90 else '#f59e0b' if metrics['memory'] > 80 else '#22c55e'};">{metrics['memory']}%</p>
                    </div>
                    <div class="summary-card">
                        <h3>Disk</h3>
                        <p style="color:{'#ef4444' if metrics['disk'] > 90 else '#f59e0b' if metrics['disk'] > 80 else '#22c55e'};">{metrics['disk']}%</p>
                    </div>
                    <div class="summary-card">
                        <h3>Status</h3>
                        <p style="color:{color};">{metrics['status']}</p>
                    </div>
                </div>

                <div class="alerts-box">
                    <h2 style="margin-top:0;">Active Alerts</h2>
                    {alerts_html}
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/history")
def history_page():
    history = get_history(50)

    rows_html = ""
    for row in history:
        status_color = "#22c55e"
        if row["status"] == "Warning":
            status_color = "#f59e0b"
        elif row["status"] == "Critical":
            status_color = "#ef4444"

        rows_html += f"""
        <tr>
            <td>{row['timestamp']}</td>
            <td>{row['cpu']}%</td>
            <td>{row['memory']}%</td>
            <td>{row['disk']}%</td>
            <td style="color:{status_color}; font-weight:bold;">{row['status']}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>System Health History</title>
        {base_styles()}
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="top-nav">
                    <a href="/">Dashboard</a>
                    <a href="/history">History</a>
                    <a href="/charts">Charts</a>
                </div>

                <h1>System Health History</h1>
                <p class="subtitle">Stored health snapshots from SQLite database</p>

                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>CPU</th>
                            <th>Memory</th>
                            <th>Disk</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/charts")
def charts_page():
    history = get_history(50)
    history = list(reversed(history))

    labels = [row["timestamp"] for row in history]
    cpu_values = [row["cpu"] for row in history]
    memory_values = [row["memory"] for row in history]
    disk_values = [row["disk"] for row in history]

    return f"""
    <html>
    <head>
        <title>System Health Charts</title>
        {base_styles()}
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="top-nav">
                    <a href="/">Dashboard</a>
                    <a href="/history">History</a>
                    <a href="/charts">Charts</a>
                </div>

                <h1>System Health Charts</h1>
                <p class="subtitle">Visual performance history for CPU, memory, and disk</p>

                <div class="chart-box">
                    <h2>CPU Usage Over Time</h2>
                    <canvas id="cpuChart"></canvas>
                </div>

                <div class="chart-box">
                    <h2>Memory Usage Over Time</h2>
                    <canvas id="memoryChart"></canvas>
                </div>

                <div class="chart-box">
                    <h2>Disk Usage Over Time</h2>
                    <canvas id="diskChart"></canvas>
                </div>
            </div>
        </div>

        <script>
            const labels = {json.dumps(labels)};
            const cpuData = {json.dumps(cpu_values)};
            const memoryData = {json.dumps(memory_values)};
            const diskData = {json.dumps(disk_values)};

            const sharedOptions = {{
                responsive: true,
                plugins: {{
                    legend: {{
                        labels: {{ color: 'white' }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: 'white' }}
                    }},
                    y: {{
                        ticks: {{ color: 'white' }},
                        beginAtZero: true
                    }}
                }}
            }};

            new Chart(document.getElementById('cpuChart'), {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'CPU %',
                        data: cpuData,
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.2)',
                        tension: 0.3,
                        fill: true
                    }}]
                }},
                options: sharedOptions
            }});

            new Chart(document.getElementById('memoryChart'), {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Memory %',
                        data: memoryData,
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.2)',
                        tension: 0.3,
                        fill: true
                    }}]
                }},
                options: sharedOptions
            }});

            new Chart(document.getElementById('diskChart'), {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Disk %',
                        data: diskData,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.2)',
                        tension: 0.3,
                        fill: true
                    }}]
                }},
                options: sharedOptions
            }});
        </script>
    </body>
    </html>
    """


@app.route("/api/metrics")
def api_metrics():
    return jsonify(get_current_metrics())


@app.route("/api/history")
def api_history():
    return jsonify(get_history(50))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)