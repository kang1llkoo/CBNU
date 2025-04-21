from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__)
base_path = 'C:/Users/d/OneDrive - 충북대학교/바탕 화면/캡스톤디자인'
anomaly_detected = False

@app.route('/')
def index():
    return send_from_directory(base_path, 'draw_route_2.html')


@app.route('/anomaly_status')
def anomaly_status():
    return jsonify({'anomaly' : anomaly_detected})

@app.route('/set_anomaly', methods = ['POST'])
def set_anomaly():
    global anomaly_detected
    anomaly_detected = True
    return 'Anomaly flag set', 200

if __name__ == '__main__':
    app.run(host = '127.0.0.1', port = 5000)