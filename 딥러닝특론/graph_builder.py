import pandas as pd
import networkx as nx


def bake_map(df, topology_df, X_scenario,
             time_model,
             carbon_model,
             scenario_name):

    print(f"[{scenario_name}] Road network construction...")

    pred_time = time_model.predict(X_scenario.values).flatten()
    pred_carbon = carbon_model.predict(X_scenario.values).flatten()

    temp_df = df[['link_id']].copy()
    temp_df['Predicted_Time'] = pred_time
    temp_df['Predicted_Carbon'] = pred_carbon

    map_df = pd.merge(
        topology_df,
        temp_df.drop_duplicates(subset=['link_id']),
        on='link_id',
        how='left'
    )

    map_df['Predicted_Time'] = (
        map_df['Predicted_Time']
        .fillna(map_df['Predicted_Time'].median())
    )

    map_df['Predicted_Carbon'] = (
        map_df['Predicted_Carbon']
        .fillna(map_df['Predicted_Carbon'].median())
    )

    map_df['Norm_Time'] = (
        map_df['Predicted_Time'] -
        map_df['Predicted_Time'].min()
    ) / (
        map_df['Predicted_Time'].max() -
        map_df['Predicted_Time'].min()
    )

    map_df['Norm_Carbon'] = (
        map_df['Predicted_Carbon'] -
        map_df['Predicted_Carbon'].min()
    ) / (
        map_df['Predicted_Carbon'].max() -
        map_df['Predicted_Carbon'].min()
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