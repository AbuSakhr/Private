from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime, timedelta
import uuid
import os

app = Flask(__name__, static_folder="static")

# قاعدة بيانات مؤقتة في الذاكرة
licenses = {}

# الصفحة الرئيسية تعرض واجهة HTML
@app.route('/')
def index():
    return send_from_directory('static', 'admin.html')

# توليد كود ترخيص جديد
@app.route('/api/generate', methods=['POST'])
def generate_license():
    data = request.json
    duration_days = data.get('days', 7)  # المدة الافتراضية 7 أيام

    code = str(uuid.uuid4()).upper()
    licenses[code] = {
        'start_date': datetime.utcnow(),
        'end_date': datetime.utcnow() + timedelta(days=duration_days),
        'activated': False,
        'device_id': None
    }

    return jsonify({
        'license_code': code,
        'valid_until': licenses[code]['end_date'].isoformat()
    })

# التحقق من كود التفعيل
@app.route('/api/validate', methods=['POST'])
def validate_license():
    data = request.json
    code = data.get('code')
    device = data.get('device_id')

    if code not in licenses:
        return jsonify({'status': 'invalid', 'message': 'License not found'}), 404

    license = licenses[code]

    if license['end_date'] < datetime.utcnow():
        return jsonify({'status': 'expired', 'message': 'License expired'}), 403

    if license['device_id'] and license['device_id'] != device:
        return jsonify({'status': 'denied', 'message': 'License already used on another device'}), 403

    return jsonify({
        'status': 'valid',
        'expires_at': license['end_date'].isoformat(),
        'days_left': (license['end_date'] - datetime.utcnow()).days
    })

# تفعيل الكود
@app.route('/api/activate', methods=['POST'])
def activate_license():
    data = request.json
    code = data.get('code')
    device = data.get('device_id')

    if code not in licenses:
        return jsonify({'status': 'invalid', 'message': 'License not found'}), 404

    license = licenses[code]

    if license['activated'] and license['device_id'] != device:
        return jsonify({'status': 'used', 'message': 'Code already used on another device'}), 403

    license['activated'] = True
    license['device_id'] = device

    return jsonify({'status': 'activated', 'code': code})

# عرض حالة كود
@app.route('/api/status/<code>', methods=['GET'])
def status(code):
    if code not in licenses:
        return jsonify({'status': 'invalid'}), 404

    lic = licenses[code]
    return jsonify({
        'code': code,
        'start_date': lic['start_date'].isoformat(),
        'end_date': lic['end_date'].isoformat(),
        'activated': lic['activated'],
        'device_id': lic['device_id']
    })

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000)
