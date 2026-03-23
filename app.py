from flask import Flask
import psutil

app = Flask(__name__)

@app.route("/")
def dashboard():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    def color(value):
        if value < 70:
            return "green"
        elif value < 85:
            return "orange"
        return "red"

    return f"""
    <html>
    <head>
        <title>System Health Checker</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ font-family: Arial; background:#f4f6f8; text-align:center; }}
            .card {{
                background:white;
                width:500px;
                margin:auto;
                padding:25px;
                border-radius:12px;
                box-shadow:0 4px 12px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>System Health Checker</h1>

            <p style="color:{color(cpu)}">CPU: {cpu}%</p>
            <p style="color:{color(memory)}">Memory: {memory}%</p>
            <p style="color:{color(disk)}">Disk: {disk}%</p>

        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)