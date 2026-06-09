# preprocessing.py

import glob
import os
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


def load_csv_files(base_path):

    file_list = glob.glob(base_path, recursive=True)

    all_df = []
    od_records = []

    for f in file_list:

        try:

            temp_df = pd.read_csv(f)

            if temp_df.empty:
                continue

            if 'link_id' not in temp_df.columns:
                continue

            driver_id = os.path.basename(os.path.dirname(f))

            day_type = (
                temp_df['day_type'].iloc[0]
                if 'day_type' in temp_df.columns
                else 'Unknown'
            )

            od_records.append({
                'Driver_ID': driver_id,
                'Start_Link': str(temp_df['link_id'].iloc[0]),
                'End_Link': str(temp_df['link_id'].iloc[-1]),
                'Day_Type': day_type
            })

            temp_df['Driver_ID'] = driver_id

            all_df.append(temp_df)

        except:
            pass

    df = pd.concat(all_df, ignore_index=True)

    od_df = pd.DataFrame(od_records)

    return df, od_df


def minmax_set_norm(arr, set_min, set_max):

    arr = np.array(arr)

    set_range = set_max - set_min

    if set_range == 0:
        return np.zeros_like(arr)

    return np.clip(
        (arr - set_min) / set_range,
        0,
        1
    )


def preprocess_data(df, features, num_cols, cat_cols):

    X = df[features].copy()

    y_time = df['travel_time']

    y_carbon = df['link_carbon_sum']

    for col in num_cols:

        X[col] = minmax_set_norm(
            X[col],
            X[col].min(),
            X[col].max()
        )

    cat_idxs = []
    cat_dims = []

    for idx, col in enumerate(features):

        if col in cat_cols:

            le = LabelEncoder()

            X[col] = le.fit_transform(
                X[col].astype(str)
            )

            cat_idxs.append(idx)

            cat_dims.append(
                len(le.classes_)
            )

    (
        X_train,
        X_test,
        y_time_train,
        y_time_test
    ) = train_test_split(
        X,
        y_time,
        test_size=0.2,
        random_state=42
    )

    y_carbon_train = y_carbon.loc[y_time_train.index]

    y_carbon_test = y_carbon.loc[y_time_test.index]

    return (
        X,
        X_train,
        X_test,
        y_time_train,
        y_time_test,
        y_carbon_train,
        y_carbon_test,
        cat_idxs,
        cat_dims
    )