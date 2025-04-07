import os
import pandas as pd
import numpy as np

# 반복된 라벨 제거 (연속된 동일 라벨은 하나로 간주)
def CollapseRecurringLabels(original_list):
    if not original_list:
        return []
    
    result_list = [original_list[0]]
    for i in range(1, len(original_list)):
        if original_list[i] != original_list[i - 1]:
            result_list.append(original_list[i])
    return result_list

# IQR 기반 threshold 계산 함수
def compute_threshold(frequencies):
    q1 = np.quantile(frequencies, 0.25)
    q3 = np.quantile(frequencies, 0.75)
    iqr = q3 - q1

    # 이상치 기준 upper/lower bound
    upper_bound = q3 + (1.5 * iqr)
    lower_bound = q1 - (1.5 * iqr)

    threshold = iqr + upper_bound - lower_bound
    return threshold

# 라벨 데이터 경로
labeled_data_path = "C:/Users/d/OneDrive - 충북대학교/바탕 화면/캡스톤디자인/label"

# 빈도 딕셔너리 초기화
frequency_dict = {}

# 모든 라벨 파일 순회하며 격자 빈도 계산
for file_name in os.listdir(labeled_data_path):
    if file_name.endswith('.csv'):
        file_path = os.path.join(labeled_data_path, file_name)
        df = pd.read_csv(file_path)

        # 'grid_label' 컬럼이 없을 경우 무시
        if 'grid_label' not in df.columns:
            continue

        labels = df['grid_label'].tolist()
        unique_labels = CollapseRecurringLabels(labels)
        df_unique = pd.DataFrame(unique_labels, columns=['grid_label'])

        # 라벨 빈도 계산
        label_counts = df_unique['grid_label'].value_counts().to_dict()

        # 전체 빈도 딕셔너리에 추가
        for label, count in label_counts.items():
            frequency_dict[label] = frequency_dict.get(label, 0) + count

# 결과를 DataFrame으로 변환
frequency_df = pd.DataFrame(list(frequency_dict.items()), columns=['Label', 'Frequency'])

# CSV로 저장
frequency_df.to_csv('label_frequencies.csv', index=False)

# threshold 계산 및 출력
frequencies = frequency_df['Frequency'].tolist()
threshold = compute_threshold(frequencies)
print(f"Computed threshold based on IQR: {threshold:.2f}")