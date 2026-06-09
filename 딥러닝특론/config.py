BASE_PATH = r'\\10.255.77.176\netdb\999_개인폴더\강범구\위드라이브2026\데이터\new_matching\**\*.csv'

SHP_PATH = r'\\NetDB\netdb\001_프로젝트 자료\022_WEDRIVE(ORCAICT) & BOAS-SE\code\optPathModel\src\MOCT_LINK.shp'

NUM_COLS = [
    'LENGTH',
    'MAX_SPD',
    'avg_speed_kph',
    'link_dist_sum',
    'hard_accel_count',
    'hard_decel_count'
]

CAT_COLS = [
    'hour',
    'day_type',
    'ROAD_TYPE',
    'ROAD_RANK',
    'LANES'
]

FEATURES = NUM_COLS + CAT_COLS

TARGET_TIME = 'travel_time'
TARGET_CARBON = 'link_carbon_sum'

START_LINK = '3340018601'
END_LINK = '1750029000'