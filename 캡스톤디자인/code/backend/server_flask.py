from flask import Flask, request, jsonify
import requests

app = Flask(
    __name__,
    static_folder='C:/Users/d/OneDrive - 충북대학교/바탕 화면/캡스톤디자인/static'
)

anomaly_detected = False
path_coords = []

def reset_path_data():
    global path_coords
    path_coords = []
    print("초기화 완료")

@app.route('/')
def index():
    return app.send_static_file('draw_route_2.html')

@app.route('/anomaly_status')
def anomaly_status():
    return jsonify({'anomaly': anomaly_detected})

@app.route('/set_anomaly', methods=['POST'])
def set_anomaly():
    global anomaly_detected
    anomaly_detected = True
    return 'Anomaly flag set', 200

@app.route('/start_dag', methods=['POST'])
def start_dag():
    global anomaly_detected
    technique = request.json.get('technique')
    reset = request.json.get('reset_path', True)

    if reset:
        reset_path_data()
        anomaly_detected = False

    if not technique:
        return 'Technique not provided', 400

    dag_id = 'web_input_dag'  # 단일 DAG에서 conf로 technique 처리
    response = requests.post(
        f'http://localhost:8080/api/v1/dags/{dag_id}/dagRuns',
        auth=('airflow', 'airflow'),
        json={'conf': {'technique': technique, 'reset_path': reset}}
    )

    if response.ok:
        return 'Dag Triggered', 200
    else:
        return f'Failed to trigger DAG: {response.text}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
