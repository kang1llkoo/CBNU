import glob
import os
import pandas as pd
import geopandas as gpd


def load_csv_files(base_path):

    file_list = glob.glob(base_path, recursive=True)

    all_df = []

    for f in file_list:
        try:
            temp_df = pd.read_csv(f)

            if temp_df.empty or 'link_id' not in temp_df.columns:
                continue

            driver_id = os.path.basename(os.path.dirname(f))
            temp_df['Driver_ID'] = driver_id

            all_df.append(temp_df)

        except Exception:
            pass

    df = pd.concat(all_df, ignore_index=True)

    return df