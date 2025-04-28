from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime
import os
import pandas as pd
import ast
import requests
import time

default_args = {
    'owner': 'airflow',
    'start_date': datetime.now()
}

labeled_data_path = "/opt/airflow/dags/user_labeled"
test_dataset_path = "/opt/airflow/dags/user_test/cell"
grid_info_file = "/opt/airflow/dags/grid_information_with_paths_2.csv"

dag = DAG(
    'cell_frequency_dag',
    default_args=default_args,
    description='graduation_cell_frequency',
    schedule_interval=None,  # 트리거 방식으로 실행
    catchup=False,
)

def compute_label_frequencies(**kwargs):
    frequency_dict = {}

    for file_name in os.listdir(labeled_data_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(labeled_data_path, file_name)
            df = pd.read_csv(file_path)
            labels = df['grid_label'].tolist()

            # Remove consecutive duplicates
            unique_labels = [labels[0]]
            for i in range(1, len(labels)):
                if labels[i] != labels[i-1]:
                    unique_labels.append(labels[i])
            df_ = pd.DataFrame(unique_labels, columns=['grid_label'])

            # Count label frequencies
            label_counts = df_['grid_label'].value_counts().to_dict()
            for label, count in label_counts.items():
                frequency_dict[label] = frequency_dict.get(label, 0) + count

    # Save frequency dictionary to CSV
    frequency_df = pd.DataFrame(list(frequency_dict.items()), columns=['Label', 'Frequency'])
    output_path = "/opt/airflow/dags/label_frequencies.csv"
    frequency_df.to_csv(output_path, index=False)

def filter_test_data(**kwargs):
    grid_info = pd.read_csv(grid_info_file)
    frequency_df = pd.read_csv('/opt/airflow/dags/label_frequencies.csv')
    threshold = 10.0

    def find_label_for_point(lat, lng, grid_info):
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
            previous_label = ""

            for _, row in df.iterrows():
                label = find_label_for_point(row['lat'], row['lng'], grid_info)
                if label and label != previous_label:
                    previous_label = label
                    if label in frequency_df['Label'].values:
                        frequency = frequency_df.loc[frequency_df['Label'] == label, 'Frequency'].values[0]
                        if frequency < threshold:
                            print(f"Label {label} does not meet threshold (Frequency: {frequency})")
                    else:
                        print(f"Label {label} not in frequency data")

def notify_anomaly_to_flask():
    url = 'http://host.docker.internal:5000/set_anomaly'
    response = requests.post(url)
    if response.status_code == 200:
        print("Flask 서버에 이상 탐지 완료!")
    else:
        print("알림 실패")


compute_frequencies_task = PythonOperator(
    task_id='compute_label_frequencies',
    python_callable=compute_label_frequencies,
    dag=dag
)

filter_test_data_task = PythonOperator(
    task_id='filter_test_data',
    python_callable=filter_test_data,
    dag=dag
)

anomaly_send_task = PythonOperator(
    task_id = 'notify_anomaly_to_flask',
    python_callable = notify_anomaly_to_flask,
    dag = dag
)

# 실행 순서
compute_frequencies_task >> filter_test_data_task >> anomaly_send_task
