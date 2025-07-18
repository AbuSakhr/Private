from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timedelta
import base64
import uuid

app = Flask(__name__, static_folder='static')

licenses = {}

@app.route('/')
def index():
    return send_from_directory('static', 'admin.html')

@app.route('/api/activate', methods=['POST'])
def activate():
    data = request.json
    code = data.get("code")
    device_id = data.get("device_id")

    if not code or not device_id:
        return jsonify({"error": "code and device_id required"}), 400

    if code not in licenses:
        return jsonify({"error": "license not found"}), 404

    license_data = licenses[code]

    if license_data.get("device_id") and license_data["device_id"] != device_id:
        return jsonify({"error": "license already used on another device"}), 403

    license_data["device_id"] = device_id
    return jsonify({"message": "License activated successfully", "code": code})

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    hours = int(data.get('hours', 0))
    days = int(data.get('days', 0))

    key = str(uuid.uuid4()).upper()
    start = datetime.now()
    end = start + timedelta(days=days, hours=hours)

    license_info = {
        "ActivationCode": key,
        "StartDate": start.strftime('%Y-%m-%d %H:%M:%S'),
        "EndDate": end.strftime('%Y-%m-%d %H:%M:%S'),
        "validDays": days + (hours / 24),
        "Item_id": str(uuid.uuid4())[:8],
        "purchasecode": base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf-8'),
        "device_id": None
    }

    encoded = base64.b64encode(str(license_info).encode()).decode()
    licenses[key] = license_info
    return jsonify({"license": encoded, "details": license_info})

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    encoded = data.get('license')
    device_id = data.get('device_id')

    try:
        decoded = base64.b64decode(encoded).decode()
        for key, value in licenses.items():
            if key in decoded:
                if value.get("device_id") and value["device_id"] != device_id:
                    return jsonify({"valid": False, "error": "Device mismatch"})
                return jsonify({"valid": True, "info": value})
        return jsonify({"valid": False, "error": "Invalid key"})
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
