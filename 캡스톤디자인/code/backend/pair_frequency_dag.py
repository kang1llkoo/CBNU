from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
import os, requests
import ast
import numpy as np
import pandas as pd
from scipy.stats import iqr
from collections import defaultdict

default_args = {
    'owner': 'airflow',
    'start_date': datetime.now()
}

labeled_data_path = '/opt/airflow/dags/Label'
test_dataset_path = '/opt/airflow/dags/Test'
grid_info_file = '/opt/airflow/dags/grid_information_with_paths.csv'

dag = DAG(
    'pair_frequency',
    default_args=default_args,
    description='wedrive_pair_frequency',
    schedule_interval=None
)

def CollapseRecurringLabels(original_list):
    result_list = [original_list[0]]
    for i in range(1, len(original_list)):
        if original_list[i] != original_list[i - 1]:
            result_list.append(original_list[i])
    return result_list

def compute_threshold(frequencies):
    data = frequencies
    median_value = np.median(data)
    iqr_value = iqr(data)
    k = 2
    threshold = median_value + k * iqr_value
    return threshold

def find_label_for_point(lat, lng, grid_info):
    for index, row in grid_info.iterrows():
        min_lat, min_lng = ast.literal_eval(row['Min Latitude, Min Longitude'])
        max_lat, max_lng = ast.literal_eval(row['Max Latitude, Max Longitude'])
        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
            return row['Grid Name']
    return None

def process_labeled_data(**kwargs):
    pair_frequency = defaultdict(int) 
    for file_name in os.listdir(labeled_data_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(labeled_data_path, file_name)
            df = pd.read_csv(file_path)
            labels = df['grid_label'].tolist()
            unique_labels = CollapseRecurringLabels(labels)
            previous_label = None
            for label in unique_labels:
                if previous_label is not None:
                    pair = (previous_label, label)
                    pair_frequency[pair] += 1
                previous_label = label
    
    frequency_df = pd.DataFrame(list(pair_frequency.items()), columns=['Label', 'Frequency'])
    frequency_df.to_csv('/opt/airflow/dags/pair_frequencies.csv', index=False)

def validate_test_data(**kwargs):
    frequency_df = pd.read_csv('/opt/airflow/dags/pair_frequencies.csv')
    f_labels = frequency_df['Frequency'].tolist()
    threshold = compute_threshold(f_labels)
    grid_info = pd.read_csv(grid_info_file)
    for filename in os.listdir(test_dataset_path):
        if filename.endswith('.csv'):
            csv_file_path = os.path.join(test_dataset_path, filename)
            df = pd.read_csv(csv_file_path)
            previous_label = ""
            RecurringLabels = ""
            for index, row in df.iterrows():
                lat = row['lat']
                lng = row['lng']
                label = find_label_for_point(lat, lng, grid_info)
                if label == RecurringLabels:
                    pass
                else:
                    RecurringLabels = label
                    if previous_label == '' and pd.notna(label):
                        pass
                    elif pd.notna(label) and pd.notna(previous_label):
                        pair = (previous_label, label)
                        if frequency_df['Label'].isin([pair]).any():
                            frequency = frequency_df.loc[frequency_df['Label'] == pair, 'Frequency'].values[0]
                            if frequency >= threshold:
                                pass
                            else:
                                print(f"Pair: {pair} does not meet the frequency threshold (Frequency: {frequency})")
                        else:
                            print(f"Pair: {pair} is not in label_frequencies.csv")
                    else:
                        print(f'The point ({lat}, {lng}) is not in any grid.')
                    previous_label = label

def notify_anomaly_to_flask():
    url = 'http://127.0.0.1:5000/set_anomaly'
    response = requests.post(url)
    if response.status_code == 200:
        print("Flask 서버에 이상 탐지 완료!")
    else:
        print("알림 실패")

process_label_task = PythonOperator(
    task_id='process_labeled_data',
    python_callable=process_labeled_data,
    dag=dag
)

validate_test_task = PythonOperator(
    task_id='validate_test_data',
    python_callable=validate_test_data,
    dag=dag
)

anomaly_send_task = PythonOperator(
    task_id = 'notify_anomaly_to_flask',
    python_callable = notify_anomaly_to_flask,
    dag = dag
)

process_label_task >> validate_test_task >> anomaly_send_task