import pandas as pd
import ast
import random
from math import hypot
import os

# -------------------------------
# Jaro Similarity Function
# -------------------------------
def jaro_similarity(s1, s2):
    """
    두 문자열 간 Jaro similarity 계산
    """
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    max_dist = int(max(len1, len2) / 2) - 1

    match = 0
    hash_s1 = [0] * len1
    hash_s2 = [0] * len2

    # 매칭 문자 수 계산
    for i in range(len1):
        for j in range(max(0, i - max_dist), min(len2, i + max_dist + 1)):
            if s1[i] == s2[j] and not hash_s2[j]:
                hash_s1[i] = 1
                hash_s2[j] = 1
                match += 1
                break

    if match == 0:
        return 0.0

    # 트랜스포지션 수 계산
    t = 0
    point = 0
    for i in range(len1):
        if hash_s1[i]:
            while not hash_s2[point]:
                point += 1
            if s1[i] != s2[point]:
                t += 1
            point += 1
    t /= 2

    return (match / len1 + match / len2 + (match - t) / match) / 3.0

def calculate_trace_similarity(route1, route2):
    """
    Jaro similarity를 이용하여 두 grid 라벨 시퀀스의 유사도를 계산합니다.
    각 route는 문자열 리스트 형태여야 합니다.
    """
    str1 = "".join(route1)
    str2 = "".join(route2)
    return jaro_similarity(str1, str2)

# -------------------------------
# 1) Load and parse grid information
# -------------------------------
grid_df = pd.read_csv("grid_information_with_paths.csv")
grid_df['Min_Lat_Lng'] = grid_df['Min Latitude, Min Longitude'].apply(ast.literal_eval)
grid_df['Max_Lat_Lng'] = grid_df['Max Latitude, Max Longitude'].apply(ast.literal_eval)
grid_df[['min_lat', 'min_lng']] = pd.DataFrame(grid_df['Min_Lat_Lng'].tolist(), index=grid_df.index)
grid_df[['max_lat', 'max_lng']] = pd.DataFrame(grid_df['Max_Lat_Lng'].tolist(), index=grid_df.index)
grid_df['center_lat'] = (grid_df['min_lat'] + grid_df['max_lat']) / 2
grid_df['center_lng'] = (grid_df['min_lng'] + grid_df['max_lng']) / 2
grid_centers = grid_df.set_index('Grid Name')[['center_lat','center_lng']].to_dict('index')

# -------------------------------
# 2) Build adjacency
# -------------------------------
threshold = 0.01
neighbors = {}
names = list(grid_centers.keys())
for i, a in enumerate(names):
    lat1, lng1 = grid_centers[a]['center_lat'], grid_centers[a]['center_lng']
    for b in names[i+1:]:
        lat2, lng2 = grid_centers[b]['center_lat'], grid_centers[b]['center_lng']
        if hypot(lat1-lat2, lng1-lng2) <= threshold:
            neighbors.setdefault(a, set()).add(b)
            neighbors.setdefault(b, set()).add(a)

# -------------------------------
# 3) Load frequencies
# -------------------------------
label_freq = pd.read_csv("label_frequencies.csv")
pair_freq = pd.read_csv("pair_frequencies.csv")
label_freq['Label'] = label_freq['Label'].astype(str)
pair_freq['pair'] = pair_freq['Label'].apply(ast.literal_eval)

CELL_THR = 10
normal_cells = set(label_freq[label_freq['Frequency'] >= CELL_THR]['Label'])
abnormal_cells = set(label_freq[label_freq['Frequency'] < CELL_THR]['Label'])

PAIR_THR = 4
normal_pairs = set(pair_freq[pair_freq['Frequency'] >= PAIR_THR]['pair'])
abnormal_pairs = set(pair_freq[pair_freq['Frequency'] < PAIR_THR]['pair'])

def coords_from_grid_list(grids):
    return [(grid_centers[g]['center_lat'], grid_centers[g]['center_lng']) for g in grids]

# -------------------------------
# 4) Sample cell-based route
# -------------------------------
def sample_cell_route():
    start = random.choice(list(normal_cells))
    route = [start]
    for _ in range(1):
        cands = neighbors.get(route[-1], set()) & normal_cells
        route.append(random.choice(list(cands)) if cands else random.choice(list(normal_cells)))
    ab_cands = neighbors.get(route[-1], set()) & abnormal_cells
    route.append(random.choice(list(ab_cands)) if ab_cands else random.choice(list(abnormal_cells)))
    for _ in range(2):
        cands = neighbors.get(route[-1], set()) & normal_cells
        route.append(random.choice(list(cands)) if cands else random.choice(list(normal_cells)))
    return route

cell_route = sample_cell_route()
pd.DataFrame(coords_from_grid_list(cell_route), columns=['lat','lng']).to_csv("test_cell.csv", index=False)

# -------------------------------
# 5) Sample pair-based route
# -------------------------------
def sample_pair_route():
    frm, to = random.choice(list(normal_pairs))
    route = [frm, to]
    ab_cands = [p for p in abnormal_pairs if p[0] == route[-1]]
    if ab_cands:
        frm2, to2 = random.choice(ab_cands)
    else:
        frm2, to2 = random.choice(list(abnormal_pairs))
    route += [to2]
    for _ in range(1):
        normal_next = [p for p in normal_pairs if p[0] == route[-1]]
        if normal_next:
            route.append(random.choice(normal_next)[1])
        else:
            nbs = neighbors.get(route[-1], set()) & normal_cells
            route.append(random.choice(list(nbs)) if nbs else random.choice(list(normal_cells)))
    return route

pair_route = sample_pair_route()
pd.DataFrame(coords_from_grid_list(pair_route), columns=['lat','lng']).to_csv("test_pair.csv", index=False)

# -------------------------------
# 6) Sample trace-based route
# -------------------------------
label_folder = "Label"
known_traces = []
for f in os.listdir(label_folder):
    if f.endswith('.csv'):
        df = pd.read_csv(os.path.join(label_folder, f))
        seq = df['grid_label'].drop_duplicates().astype(str).tolist()
        known_traces.append(seq)

def sample_trace_route(length=6):
    route = [random.choice(list(normal_cells))]
    while len(route) < length:
        cands = neighbors.get(route[-1], set())
        if len(route) == length // 2:
            cands = cands & abnormal_cells
        else:
            cands = cands & normal_cells
        if not cands:
            cands = neighbors.get(route[-1], set())
        route.append(random.choice(list(cands)) if cands else random.choice(list(grid_centers)))

    # 유사도 확인
    for known in known_traces:
        if calculate_trace_similarity(route, known) >= 0.80:
            return sample_trace_route(length)
    return route

trace_route = sample_trace_route(6)
pd.DataFrame(coords_from_grid_list(trace_route), columns=['lat','lng']).to_csv("test_similarity.csv", index=False)