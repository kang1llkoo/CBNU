from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import ast
import os
import requests
from sqlalchemy import create_engine

default_args = {
    'owner': 'airflow',
    'start_date': datetime.now()
}

dag = DAG(
    'cell_frequency_dag_final',
    default_args=default_args,
    description='graduation_cell_frequency',
    schedule=None,
    catchup=False,
)

# Task 1: Label 빈도 계산 후 XCom으로 전달
def compute_label_frequencies_from_db(**kwargs):
    engine = create_engine('postgresql+psycopg2://postgres:1933@host.docker.internal:5432/capstone_design')
    df = pd.read_sql('SELECT grid_label FROM labeled_paths', engine)

    labels = df['grid_label'].tolist()

    # 연속 중복 제거
    unique_labels = [labels[0]]
    for i in range(1, len(labels)):
        if labels[i] != labels[i - 1]:
            unique_labels.append(labels[i])

    # 빈도 계산 후 반환
    label_counts = pd.Series(unique_labels).value_counts().to_dict()
    return label_counts  # XCom으로 전달됨

# Task 2: test 데이터 필터링 + 이상 탐지 판단
def filter_test_data(**kwargs):
    ti = kwargs['ti']
    label_counts = ti.xcom_pull(task_ids='compute_label_frequencies')
    threshold = 10.0

    # DB에서 grid 정보 가져오기
    engine = create_engine('postgresql+psycopg2://postgres:1933@host.docker.internal:5432/capstone_design')
    grid_info = pd.read_sql('SELECT * FROM grid_information', engine)

    def find_label_for_point(lat, lng):
        for _, row in grid_info.iterrows():
            min_lat, min_lng = ast.literal_eval(row['Min Latitude, Min Longitude'])
            max_lat, max_lng = ast.literal_eval(row['Max Latitude, Max Longitude'])
            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                return row['Grid Name']
        return None

    test_dataset_path = "/opt/airflow/dags/user_test/cell"

    for filename in os.listdir(test_dataset_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(test_dataset_path, filename)
            df = pd.read_csv(file_path)

            previous_label = ""
            for _, row in df.iterrows():
                label = find_label_for_point(row['lat'], row['lng'])
                if label and label != previous_label:
                    previous_label = label
                    frequency = label_counts.get(label, 0)
                    if frequency < threshold:
                        print(f"Label {label} is below threshold (Frequency: {frequency})")
                        # 이상치 발생 시 다음 단계에서 Flask 알림 수행

# Task 3: Flask 서버에 이상 탐지 알림 전송
def notify_anomaly_to_flask():
    url = 'http://host.docker.internal:5000/set_anomaly'
    response = requests.post(url)
    if response.status_code == 200:
        print("Flask 서버에 이상 탐지 완료!")
    else:
        print("Flask 알림 실패")

# Task 정의
compute_frequencies_task = PythonOperator(
    task_id='compute_label_frequencies',
    python_callable=compute_label_frequencies_from_db,
    provide_context=True,
    dag=dag
)

filter_test_data_task = PythonOperator(
    task_id='filter_test_data',
    python_callable=filter_test_data,
    provide_context=True,
    dag=dag
)

anomaly_send_task = PythonOperator(
    task_id='notify_anomaly_to_flask',
    python_callable=notify_anomaly_to_flask,
    dag=dag
)

# DAG 순서 정의
compute_frequencies_task >> filter_test_data_task >> anomaly_send_task
