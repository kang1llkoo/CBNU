# visualization.py

import pandas as pd
import folium

from folium import plugins


def get_coords(
        path,
        graph,
        gdf_indexed
):

    coords = []

    for i in range(
            len(path)-1
    ):

        lid = graph[
            path[i]
        ][
            path[i+1]
        ][
            'link_id'
        ]

        if lid not in gdf_indexed.index:
            continue

        geom = gdf_indexed.loc[
            lid,
            'geometry'
        ]

        if isinstance(
                geom,
                pd.Series
        ):
            geom = geom.iloc[0]

        if geom.geom_type == 'LineString':

            coords.extend(
                [
                    [lat, lon]
                    for lon, lat
                    in geom.coords
                ]
            )

        elif geom.geom_type == 'MultiLineString':

            for line in geom.geoms:

                coords.extend(
                    [
                        [lat, lon]
                        for lon, lat
                        in line.coords
                    ]
                )

    return coords

def visualize_route(
        time_path,
        carbon_path,
        graph,
        gdf_indexed,
        time_minutes,
        carbon_minutes,
        output_file
):

    time_coords = get_coords(
        time_path,
        graph,
        gdf_indexed
    )

    carbon_coords = get_coords(
        carbon_path,
        graph,
        gdf_indexed
    )

    center_lat = (
        time_coords[
            len(time_coords)//2
        ][0]
    )

    center_lon = (
        time_coords[
            len(time_coords)//2
        ][1]
    )

    m = folium.Map(
        location=[
            center_lat,
            center_lon
        ],
        zoom_start=13,
        tiles='OpenStreetMap'
    )

    plugins.AntPath(
        locations=time_coords,
        color='#0078FF',
        weight=6,
        opacity=0.8,
        tooltip=f'Time ({time_minutes:.1f} min)'
    ).add_to(m)


    if time_path != carbon_path:

        plugins.AntPath(
            locations=carbon_coords,
            color='#00B849',
            weight=6,
            opacity=0.8,
            tooltip=f'Carbon ({carbon_minutes:.1f} min)'
        ).add_to(m)

    folium.Marker(
        location=time_coords[0],
        tooltip='Start',
        icon=folium.Icon(
            color='blue'
        )
    ).add_to(m)

    folium.Marker(
        location=time_coords[-1],
        tooltip='End',
        icon=folium.Icon(
            color='red'
        )
    ).add_to(m)

    m.save(
        output_file
    )

    print(
        f"Saved : {output_file}"
    )