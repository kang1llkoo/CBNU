import os
import string
import datetime
import pandas as pd
import geopy.distance

# Paths of all the datasets
train_dataset_path = "C:/Users/d/OneDrive - 충북대학교/바탕 화면/캡스톤디자인/train"
labeled_data_path = "C:/Users/d/OneDrive - 충북대학교/바탕 화면/캡스톤디자인/label"

# Convert number to letter (A, B, ..., Z)
def num_to_letter(num):
    return string.ascii_uppercase[num]

# Check whether path passes through a grid
def is_path_in_grid(south, west, north, east, path_points):
    for lat, lng in path_points:
        if south <= lat <= north and west <= lng <= east:
            return True
    return False

# Return grid label for a specific point
def get_grid_label(lat, lng, final_grids):
    for south, west, north, east, grid_label in final_grids:
        if south <= lat <= north and west <= lng <= east:
            return grid_label
    return None

# 대한민국 대략적 경계
south_korea_bounds = [34, 125.5, 39, 130]

# train 데이터에서 모든 경로 읽기
path_points = []
path_dataframes = []

for filename in os.listdir(train_dataset_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(train_dataset_path, filename)
        data = pd.read_csv(file_path, encoding='utf-8')
        path_dataframes.append(data)
        points = data[['lat', 'lng']].values.tolist()
        path_points.extend(points)

# 초기 26x26 격자 생성
grid_queue = []
final_grids = []

initial_lat_step = (south_korea_bounds[2] - south_korea_bounds[0]) / 26
initial_lon_step = (south_korea_bounds[3] - south_korea_bounds[1]) / 26

for i in range(26):
    for j in range(26):
        south = south_korea_bounds[0] + i * initial_lat_step
        north = south_korea_bounds[0] + (i + 1) * initial_lat_step
        west = south_korea_bounds[1] + j * initial_lon_step
        east = south_korea_bounds[1] + (j + 1) * initial_lon_step
        grid_queue.append((south, west, north, east, num_to_letter(i) + num_to_letter(j)))

# 격자 세분화
min_size_km = 1
subdivisions = ['A', 'B', 'C', 'D']

while grid_queue:
    south, west, north, east, grid_label = grid_queue.pop(0)
    grid_size_km = min(
        geopy.distance.distance((south, west), (south, east)).km,
        geopy.distance.distance((south, west), (north, west)).km
    )

    if grid_size_km > min_size_km and is_path_in_grid(south, west, north, east, path_points):
        mid_lat = (south + north) / 2
        mid_lon = (west + east) / 2
        grid_queue.append((south, west, mid_lat, mid_lon, grid_label + 'C'))
        grid_queue.append((mid_lat, west, north, mid_lon, grid_label + 'A'))
        grid_queue.append((south, mid_lon, mid_lat, east, grid_label + 'D'))
        grid_queue.append((mid_lat, mid_lon, north, east, grid_label + 'B'))
    else:
        final_grids.append((south, west, north, east, grid_label))

# grid 정보 CSV로 저장
grid_data = {
    'Grid Name': [label for _, _, _, _, label in final_grids],
    'Min Latitude, Min Longitude': [(south, west) for south, west, _, _, _ in final_grids],
    'Max Latitude, Max Longitude': [(north, east) for _, _, north, east, _ in final_grids]
}

grid_df = pd.DataFrame(grid_data)
grid_df.to_csv('grid_information_with_paths.csv', index=False)

# 각 경로 데이터에 grid_label 컬럼 추가
for data in path_dataframes:
    data['grid_label'] = data.apply(lambda row: get_grid_label(row['lat'], row['lng'], final_grids), axis=1)

# Label 폴더 생성 및 라벨된 경로 저장
if not os.path.exists(labeled_data_path):
    os.makedirs(labeled_data_path)

for idx, df in enumerate(path_dataframes):
    labeled_file = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    df.to_csv(f'{labeled_data_path}/{labeled_file}.csv', index=False)
