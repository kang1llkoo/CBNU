from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os, requests
import ast
import numpy as np
import pandas as pd
from collections import defaultdict
from scipy.stats import iqr
from sqlalchemy import create_engine

default_args = {
    'owner': 'airflow',
    'start_date': datetime.now()
}

test_dataset_path = '/opt/airflow/dags/user_test/pair'

dag = DAG(
    'pair_frequency_dag_final',
    default_args=default_args,
    description='graduation_pair_frequency',
    schedule_interval=None,
    catchup=False,
)

def CollapseRecurringLabels(original_list):
    result_list = [original_list[0]]
    for i in range(1, len(original_list)):
        if original_list[i] != original_list[i - 1]:
            result_list.append(original_list[i])
    return result_list

def compute_threshold(frequencies):
    median_value = np.median(frequencies)
    iqr_value = iqr(frequencies)
    k = 2
    threshold = median_value + k * iqr_value
    return threshold

def process_labeled_data(**kwargs):
    ti = kwargs['ti']
    engine = create_engine('postgresql+psycopg2://postgres:1933@host.docker.internal:5432/capstone_design')
    df = pd.read_sql('SELECT grid_label FROM labeled_paths', engine)

    labels = df['grid_label'].tolist()
    unique_labels = CollapseRecurringLabels(labels)

    pair_frequency = defaultdict(int)
    previous_label = None
    for label in unique_labels:
        if previous_label is not None:
            pair = (previous_label, label)
            pair_frequency[str(pair)] += 1  # str로 저장
        previous_label = label

    ti.xcom_push(key='pair_frequency', value=dict(pair_frequency))

def validate_test_data(**kwargs):
    ti = kwargs['ti']
    pair_frequency = ti.xcom_pull(task_ids='process_labeled_data', key='pair_frequency')
    frequency_values = list(pair_frequency.values())
    threshold = compute_threshold(frequency_values)

    # DB에서 grid 정보 불러오기
    engine = create_engine('postgresql+psycopg2://postgres:1933@host.docker.internal:5432/capstone_design')
    grid_info = pd.read_sql('SELECT * FROM grid_information', engine)

    def find_label_for_point(lat, lng):
        for _, row in grid_info.iterrows():
            min_lat, min_lng = ast.literal_eval(row['Min Latitude, Min Longitude'])
            max_lat, max_lng = ast.literal_eval(row['Max Latitude, Max Longitude'])
            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                return row['Grid Name']
        return None

    for filename in os.listdir(test_dataset_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(test_dataset_path, filename)
            df = pd.read_csv(file_path)

            previous_label = None
            recent_label = None

            for _, row in df.iterrows():
                lat, lng = row['lat'], row['lng']
                label = find_label_for_point(lat, lng)
                if label is None:
                    print(f"Point ({lat}, {lng}) not in any grid.")
                    continue

                if label != recent_label:
                    if previous_label is not None:
                        pair = (previous_label, label)
                        pair_str = str(pair)

                        frequency = pair_frequency.get(pair_str, 0)
                        if frequency < threshold:
                            print(f"Pair {pair} is below threshold (Freq: {frequency})")
                        else:
                            print(f"Pair {pair} is normal (Freq: {frequency})")
                    previous_label = label
                    recent_label = label

def notify_anomaly_to_flask():
    url = 'http://host.docker.internal:5000/set_anomaly'
    response = requests.post(url)
    if response.status_code == 200:
        print("Flask 서버에 이상 탐지 완료!")
    else:
        print("Flask 알림 실패")

# Task 정의
process_label_task = PythonOperator(
    task_id='process_labeled_data',
    python_callable=process_labeled_data,
    provide_context=True,
    dag=dag,
)

validate_test_task = PythonOperator(
    task_id='validate_test_data',
    python_callable=validate_test_data,
    provide_context=True,
    dag=dag,
)

anomaly_send_task = PythonOperator(
    task_id='notify_anomaly_to_flask',
    python_callable=notify_anomaly_to_flask,
    dag=dag,
)

# DAG 흐름
process_label_task >> validate_test_task >> anomaly_send_task
