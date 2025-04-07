import os
import pandas as pd
import numpy as np
from scipy.stats import iqr
from collections import defaultdict

# Pair 빈도 저장 경로
labeled_data_path = "C:/Users/d/OneDrive - 충북대학교/바탕 화면/캡스톤디자인/label"

# 중복 연속 Label 제거 함수
def CollapseRecurringLabels(original_list):
    result_list = [original_list[0]]  
    for i in range(1, len(original_list)):
        if original_list[i] != original_list[i - 1]:
            result_list.append(original_list[i])
    return result_list

# Threshold 계산 함수
def compute_threshold(frequencies):
    median_value = np.median(frequencies)
    iqr_value = iqr(frequencies)
    k = 2
    threshold = median_value + k * iqr_value
    return threshold

# 1. Pair Frequency 계산
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

# 2. 결과 저장
frequency_df = pd.DataFrame(list(pair_frequency.items()), columns=['Label', 'Frequency'])
frequency_df.to_csv('pair_frequencies.csv', index=False)

# 3. Threshold 계산 및 출력
frequencies = frequency_df['Frequency'].tolist()
threshold = compute_threshold(frequencies)

print(f"Pair Frequency Threshold 값: {threshold}")