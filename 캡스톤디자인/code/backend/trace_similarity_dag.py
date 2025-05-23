from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from sqlalchemy import create_engine
import pandas as pd
import ast
import os
import requests

# PostgreSQL 연결 설정
engine = create_engine('postgresql+psycopg2://postgres:1933@host.docker.internal:5432/capstone_design')

# 테스트 데이터 경로
test_dataset_path = '/opt/airflow/dags/user_test/trace/'

# DAG 설정
default_args = {
    'owner': 'airflow',
    'start_date': datetime.now()
}

dag = DAG(
    'trace_similarity_dag_final',
    default_args=default_args,
    description='graduation_trace_similarity',
    schedule_interval=None
)

# Jaro Similarity 함수
def jaro_similarity(list1, list2):
    len1, len2 = len(list1), len(list2)
    max_dist = max(len1, len2) // 2
    match1 = [False]*len1
    match2 = [False]*len2
    matches = 0
    for i in range(len1):
        start = max(0, i-max_dist)
        end = min(i+max_dist+1, len2)
        for j in range(start, end):
            if not match2[j] and list1[i] == list2[j]:
                match1[i] = match2[j] = True
                matches += 1
                break
    if matches == 0:
        return 0.0
    transpositions = 0
    k = 0
    for i in range(len1):
        if match1[i]:
            while not match2[k]:
                k += 1
            if list1[i] != list2[k]:
                transpositions += 1
            k += 1
    transpositions /= 2
    return ((matches/len1 + matches/len2 + (matches-transpositions)/matches) / 3)

# 라벨 데이터 처리 및 유사도 계산
def process_label_data(**kwargs):
    geo_trace_pts = {}
    frequent_pattern = {}
    normal_pattern = {}

    for i in range(20):
        table_name = f"labeled_paths_{i}"
        df = pd.read_sql(f"SELECT grid_label FROM {table_name}", engine)
        
        # 중복을 제거하고 순서를 유지하는 방법 (dict 직접 사용)
        seen = {}
        current_trace = []
        for label in df['grid_label']:
            if label not in seen:
                seen[label] = True
                current_trace.append(label)

        geo_trace_pts[tuple(current_trace)] = geo_trace_pts.get(tuple(current_trace), 0) + 1

    # frequent_pattern과 normal_pattern으로 나누기
    for trace, cnt in geo_trace_pts.items():
        (frequent_pattern if cnt >= 2 else normal_pattern)[trace] = cnt

    # 유사도 기반 이상 cell 수집
    cell = set()
    for n in normal_pattern:
        for f in frequent_pattern:
            if jaro_similarity(list(n), list(f)) <= 0.80:
                cell.update(f)
    
    kwargs['ti'].xcom_push(key='cell', value=list(cell))

# 테스트 데이터 처리
def process_test_data(**kwargs):
    cell = kwargs['ti'].xcom_pull(task_ids='process_label_data', key='cell')

    # PostgreSQL에서 grid 정보 조회
    grid_df = pd.read_sql("SELECT * FROM grid_information", engine)

    # 좌표 → Grid Name 매핑 함수
    def find_label(lat, lng):
        for _, r in grid_df.iterrows():
            min_lat, min_lng = ast.literal_eval(r['Min Latitude, Min Longitude'])
            max_lat, max_lng = ast.literal_eval(r['Max Latitude, Max Longitude'])
            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                return r['Grid Name']
        return None

    # 테스트 데이터 경로 처리
    for fname in os.listdir(test_dataset_path):
        if not fname.endswith('.csv'):
            continue
        df = pd.read_csv(os.path.join(test_dataset_path, fname))
        for _, row in df.iterrows():
            label = find_label(row['lat'], row['lng'])
            status = '정상 경로' if label in cell else '비정상 경로'
            print(f"사용자 현재 위치: {label} -> {status}")

# 이상 감지 시 Flask 알림
def notify_anomaly_to_flask():
    url = 'http://host.docker.internal:5000/set_anomaly'
    resp = requests.post(url)
    if resp.ok:
        print("Flask 서버에 이상 탐지 완료!")
    else:
        print("알림 실패!", resp.status_code)

# DAG 태스크 구성
label_task = PythonOperator(task_id='process_label_data', python_callable=process_label_data, dag=dag)
test_task = PythonOperator(task_id='process_test_data', python_callable=process_test_data, dag=dag)
anom_task = PythonOperator(task_id='notify_anomaly_to_flask', python_callable=notify_anomaly_to_flask, dag=dag)

# 태스크 순서 정의
label_task >> test_task >> anom_task
