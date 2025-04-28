from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
}

with DAG(
    'web_input_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:

    # 1) 바로 dag_run.conf에서 technique 읽어서 XCom에 저장
    def grab_technique(**kwargs):
        ti = kwargs['ti']
        technique = kwargs['dag_run'].conf.get('technique', '')
        reset_path = kwargs['dag_run'].conf.get('reset_path', True)
        ti.xcom_push(key='technique', value=technique)
        ti.xcom_push(key='reset_path', value=reset_path)
        print(f"[web_input_dag] Selected technique: {technique}")

    save_tech = PythonOperator(
        task_id='grab_technique',
        python_callable=grab_technique,
        provide_context=True,
    )

    def reset_path_data():
        print("경로 데이터 초기화 완료")

    # 2) XCom에 저장된 technique 값으로 분기
    def choose_technique(**kwargs):
        ti = kwargs['ti']
        tech = ti.xcom_pull(key='technique', task_ids='grab_technique')
        reset_path = ti.xcom_pull(key='reset_path', task_ids = 'grab_technique')

        if not tech:
            raise ValueError("conf에 technique 전달 필요")
        
        if reset_path:
            reset_path_data()

        if tech == 'cell_frequency':
            return 'trigger_cell_frequency_dag'
        elif tech == 'pair_frequency':
            return 'trigger_pair_frequency_dag'
        elif tech == 'trace_similarity':
            return 'trigger_trace_similarity_dag'
        else:
            return 'end_task'

    branch = BranchPythonOperator(
        task_id='branch_on_technique',
        python_callable=choose_technique,
        provide_context=True,
    )

    # 3) 각 기법별 DAG 트리거
    trigger_cell = TriggerDagRunOperator(
        task_id='trigger_cell_frequency_dag',
        trigger_dag_id='cell_frequency_dag',
        conf={'technique':'cell_frequency'}
    )
    trigger_pair = TriggerDagRunOperator(
        task_id='trigger_pair_frequency_dag',
        trigger_dag_id='pair_frequency_dag',
        conf={'technique':'pair_frequency'}
    )
    trigger_trace = TriggerDagRunOperator(
        task_id='trigger_trace_similarity_dag',
        trigger_dag_id='trace_similarity_dag',
        conf={'technique':'trace_similarity'}
    )

    # 4) 잘못된 값 대비
    end_task = EmptyOperator(task_id='end_task')

    save_tech >> branch
    branch >> [trigger_cell, trigger_pair, trigger_trace, end_task]
