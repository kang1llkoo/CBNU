# routing.py

import networkx as nx


def find_path(
        G,
        start_node,
        end_node,
        weight_func,
        name
):

    try:

        path = nx.shortest_path(
            G,
            source=start_node,
            target=end_node,
            weight=weight_func
        )

        total_time = 0
        total_carbon = 0

        for i in range(
                len(path) - 1
        ):

            edge = G[
                path[i]
            ][
                path[i+1]
            ]

            total_time += (
                edge[
                    'Predicted_Time'
                ]
            )

            total_carbon += (
                edge[
                    'Predicted_Carbon'
                ]
            )

        print(
            f"{name} | "
            f"Time : {total_time/60:.1f} min | "
            f"Carbon : {total_carbon:.1f} g"
        )

        return (
            path,
            total_time,
            total_carbon
        )

    except nx.NetworkXNoPath:

        print(
            f"{name} : No Path"
        )

        return None, 0, 0

    except Exception as e:

        print(e)

        return None, 0, 0