import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import geopandas as gpd
import networkx as nx
import folium

from folium import plugins

from config import *
from preprocessing import load_csv_files
from preprocessing import preprocess_data
from train_model import train_tabnet_model

from routing import find_path
from visualization import visualize_route

print("===== DATA LOADING =====")

df, od_df = load_csv_files(BASE_PATH)

df = df.dropna(
    subset=FEATURES + [
        TARGET_TIME,
        TARGET_CARBON
    ]
)


(
    X,
    X_train,
    X_test,
    y_time_train,
    y_time_test,
    y_carbon_train,
    y_carbon_test,
    cat_idxs,
    cat_dims
) = preprocess_data(
    df,
    FEATURES,
    NUM_COLS,
    CAT_COLS
)


print("===== TRAIN TIME MODEL =====")

tabnet_time_model = train_tabnet_model(
    X_train,
    y_time_train,
    cat_idxs,
    cat_dims
)


print("===== TRAIN CARBON MODEL =====")

tabnet_carbon_model = train_tabnet_model(
    X_train,
    y_carbon_train,
    cat_idxs,
    cat_dims
)


print("===== LOAD SHAPEFILE =====")

gdf = gpd.read_file(
    SHP_PATH,
    encoding='utf-8'
)

gdf.set_crs(
    epsg=5181,
    inplace=True,
    allow_override=True
)

gdf_4326 = gdf.to_crs(
    epsg=4326
)


topology_df = pd.DataFrame(
    gdf_4326[
        ['LINK_ID', 'F_NODE', 'T_NODE']
    ]
).rename(
    columns={
        'LINK_ID': 'link_id'
    }
)


df['link_id'] = df['link_id'].astype(str)

topology_df['link_id'] = topology_df['link_id'].astype(str)


weekday_mask = df['day_type'].astype(str).str.contains(
    'Weekday|weekday',
    case=False
)

weekend_mask = df['day_type'].astype(str).str.contains(
    'Weekend|weekend',
    case=False
)


weekday_val = X.loc[
    weekday_mask,
    'day_type'
].iloc[0]

weekend_val = X.loc[
    weekend_mask,
    'day_type'
].iloc[0]


X_weekday = X.copy()
X_weekend = X.copy()

X_weekday['day_type'] = weekday_val
X_weekend['day_type'] = weekend_val


def build_graph(X_scenario):

    pred_time = (
        tabnet_time_model
        .predict(X_scenario.values)
        .flatten()
    )

    pred_carbon = (
        tabnet_carbon_model
        .predict(X_scenario.values)
        .flatten()
    )

    temp_df = df[['link_id']].copy()

    temp_df['Predicted_Time'] = pred_time

    temp_df['Predicted_Carbon'] = pred_carbon


    map_df = pd.merge(
        topology_df,
        temp_df.drop_duplicates(
            subset=['link_id']
        ),
        on='link_id',
        how='left'
    )


    map_df['Predicted_Time'] = (
        map_df['Predicted_Time']
        .fillna(
            map_df['Predicted_Time']
            .median()
        )
    )

    map_df['Predicted_Carbon'] = (
        map_df['Predicted_Carbon']
        .fillna(
            map_df['Predicted_Carbon']
            .median()
        )
    )


    map_df['Norm_Time'] = (
        map_df['Predicted_Time']
        - map_df['Predicted_Time'].min()
    ) / (
        map_df['Predicted_Time'].max()
        - map_df['Predicted_Time'].min()
    )


    map_df['Norm_Carbon'] = (
        map_df['Predicted_Carbon']
        - map_df['Predicted_Carbon'].min()
    ) / (
        map_df['Predicted_Carbon'].max()
        - map_df['Predicted_Carbon'].min()
    )


    G = nx.from_pandas_edgelist(
        map_df,
        source='F_NODE',
        target='T_NODE',
        edge_attr=[
            'link_id',
            'Predicted_Time',
            'Predicted_Carbon',
            'Norm_Time',
            'Norm_Carbon'
        ],
        create_using=nx.DiGraph()
    )

    return G


G_weekday = build_graph(X_weekday)

G_weekend = build_graph(X_weekend)


real_start_node = topology_df[
    topology_df['link_id'] == START_LINK
]['F_NODE'].iloc[0]

real_end_node = topology_df[
    topology_df['link_id'] == END_LINK
]['T_NODE'].iloc[0]


def find_path(
        G,
        weight_func
):

    path = nx.shortest_path(
        G,
        source=real_start_node,
        target=real_end_node,
        weight=weight_func
    )

    total_time = 0
    total_carbon = 0

    for i in range(len(path)-1):

        edge = G[path[i]][path[i+1]]

        total_time += edge['Predicted_Time']

        total_carbon += edge['Predicted_Carbon']

    return path, total_time, total_carbon

wd_time_path, wd_t_time, wd_t_carb = find_path(
    G_weekday,
    real_start_node,
    real_end_node,
    lambda u,v,d: d['Norm_Time'],
    "Weekday Fastest"
)

wd_carb_path, wd_c_time, wd_c_carb = find_path(
    G_weekday,
    real_start_node,
    real_end_node,
    lambda u,v,d: d['Norm_Carbon'],
    "Weekday Eco"
)

we_time_path, we_t_time, we_t_carb = find_path(
    G_weekend,
    real_start_node,
    real_end_node,
    lambda u,v,d: d['Norm_Time'],
    "Weekend Fastest"
)

we_carb_path, we_c_time, we_c_carb = find_path(
    G_weekend,
    real_start_node,
    real_end_node,
    lambda u,v,d: d['Norm_Carbon'],
    "Weekend Eco"
)

gdf_indexed = (
    gdf_4326
    .set_index(
        gdf_4326['LINK_ID'].astype(str)
    )
)

visualize_route(
    wd_time_path,
    wd_carb_path,
    G_weekday,
    gdf_indexed,
    wd_t_time/60,
    wd_c_time/60,
    'outputs/eco_routing_weekday.html'
)

visualize_route(
    we_time_path,
    we_carb_path,
    G_weekend,
    gdf_indexed,
    we_t_time/60,
    we_c_time/60,
    'outputs/eco_routing_weekend.html'
)