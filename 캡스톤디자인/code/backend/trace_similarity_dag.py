from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime
from flask import Flask, requests
import os
import pandas as pd

labeled_data_path = '/opt/airflow/dags/Label'
test_dataset_path = '/opt/airflow/dags/Test'
grid_info_file = '/opt/airflow/dags/grid_information_with_paths.csv'
user_selection_file = '/opt/airflow/dags/user_selection.txt'

default_args = {
    'owner': 'airflow',
    'start_date': datetime.now()
}

dag = DAG(
    'trace_similarity',
    default_args=default_args,
    description='Trace Similarity Anomaly Detection',
    schedule_interval=None
)

# 사용자 선택을 확인하는 함수
def check_user_selection():
    with open(user_selection_file, 'r') as f:
        selection = f.read().strip()
    return selection == "Trace"

# Jaro Similarity 계산 함수
def jaro_similarity(list1, list2):
    len_list1, len_list2 = len(list1), len(list2)
    max_len = max(len_list1, len_list2)
    match_count = 0
    matches_list1, matches_list2 = [False] * len_list1, [False] * len_list2
    
    for i in range(len_list1):
        start, end = max(0, i - max_len // 2), min(i + max_len // 2 + 1, len_list2)
        for j in range(start, end):
            if not matches_list2[j] and list1[i] == list2[j]:
                matches_list1[i] = matches_list2[j] = True
                match_count += 1
                break
    
    if match_count == 0:
        return 0.0
    
    transpositions = sum(list1[i] != list2[k] for i, k in enumerate(filter(lambda x: matches_list2[x], range(len_list2))))
    
    return ((match_count / len_list1 + match_count / len_list2 + (match_count - transpositions / 2) / match_count) / 3.0)

# 라벨 데이터 처리 및 유사도 계산
def process_label_data(**kwargs):
    if not check_user_selection():
        return
    
    geo_trace_pts, frequent_pattern, normal_pattern = {}, {}, {}
    csv_files = [f for f in os.listdir(labeled_data_path) if f.endswith('.csv')]
    
    for file in csv_files:
        file_path = os.path.join(labeled_data_path, file)
        df = pd.read_csv(file_path)['grid_label']
        geo_trace = list(dict.fromkeys(df.tolist()))
        geo_trace_pts[tuple(geo_trace)] = geo_trace_pts.get(tuple(geo_trace), 0) + 1
    
    sorted_geo_trace_pts = dict(sorted(geo_trace_pts.items(), key=lambda x: x[1], reverse=True))
    
    for key, value in sorted_geo_trace_pts.items():
        (frequent_pattern if value >= 2 else normal_pattern)[key] = value
    
    cell_list = [list2 for key1 in normal_pattern for key2 in frequent_pattern
                 if key1 != key2 and jaro_similarity(list(key1), list(key2)) > 0.80]
    kwargs['ti'].xcom_push(key='cell', value=list(set(cell_list)))

# 테스트 데이터 처리
def process_test_data(**kwargs):
    if not check_user_selection():
        return
    
    cell = kwargs['ti'].xcom_pull(task_ids='process_label_data', key='cell')
    grid_info = pd.read_csv(grid_info_file)
    
    for filename in os.listdir(test_dataset_path):
        if filename.endswith('.csv'):
            df = pd.read_csv(os.path.join(test_dataset_path, filename))
            for _, row in df.iterrows():
                label = find_label_for_point(row['lat'], row['lng'], grid_info)
                print(f"사용자 현재 위치: {label}")
                print('정상 경로' if label in cell else '비정상 경로')

# 특정 좌표에 대한 라벨 찾기
def find_label_for_point(lat, lng, grid_info):
    for _, row in grid_info.iterrows():
        min_lat, min_lng = eval(row['Min Latitude, Min Longitude'])
        max_lat, max_lng = eval(row['Max Latitude, Max Longitude'])
        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
            return row['Grid Name']
    return None

def notify_anomaly_to_flask():
    url = 'http://127.0.0.1:5000/set_anomaly'
    response = requests.post(url)
    if response.status_code == 200:
        print("Flask 서버에 이상 탐지 완료!")
    else:
        print("알림 실패!")

start_task = DummyOperator(task_id='start', dag=dag)
process_label_data_task = PythonOperator(task_id='process_label_data', python_callable=process_label_data, dag=dag)
process_test_data_task = PythonOperator(task_id='process_test_data', python_callable=process_test_data, dag=dag)
end_task = DummyOperator(task_id='end', dag=dag)

anomaly_send_task = PythonOperator(
    task_id = 'notify_anomaly_to_flask',
    python_callable = notify_anomaly_to_flask,
    dag = dag
)

start_task >> process_label_data_task >> process_test_data_task >> end_task >> anomaly_send_task