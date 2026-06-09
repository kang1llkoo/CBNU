# Multi-Objective Eco-Routing Framework

[cite_start]본 프로젝트는 TabNet 딥러닝 예측 모델과 GIS 공간 네트워크를 통합하여, 교통 효율성(최단 시간)과 환경적 지속가능성(최소 탄소 배출)을 동시에 고려하는 다목적 에코 라우팅(Eco-Routing) 시뮬레이터입니다.

## 📌 Project Overview
기존 내비게이션 시스템은 이동 시간 최소화에만 초점을 맞추어 탄소 배출을 간과하는 경향이 있습니다. 본 연구는 정형 교통 데이터에 특화된 딥러닝 아키텍처인 **TabNet**을 활용하여 도로 링크별 통행 시간과 탄소 배출량을 독립적으로 예측합니다. 예측된 결과는 국가 표준 노드-링크 데이터(MOCT_LINK) 기반의 방향성 그래프(DiGraph)에 동적 가중치로 할당되며, 다익스트라(Dijkstra) 알고리즘을 통해 사용자의 선호도에 따른 최적의 친환경 경로를 도출합니다.

## 📂 Repository Structure
코드는 기능별로 모듈화되어 있으며, 각 파일의 역할은 다음과 같습니다:

* `config.py`: 데이터 경로(`BASE_PATH`, `SHP_PATH`), 피처 변수 목록, 타겟 변수, 기종점(O-D) 링크 ID 등 전역 설정 변수를 관리합니다.
* `data_loader.py`: 디렉토리 내의 주행 궤적 CSV 파일들을 순회하며 하나의 데이터프레임으로 로드하고 병합합니다.
* `preprocessing.py`: Min-Max 스케일링, 범주형 변수 라벨 인코딩(Label Encoding), 그리고 학습/테스트 데이터 분할(Train-Test Split)을 수행합니다.
* `train_model.py`: PyTorch 기반의 `TabNetRegressor` 모델을 초기화하고 조기 종료(Early Stopping) 및 Adam 옵티마이저를 적용하여 학습시킵니다.
* `evaluation.py`: 예측 모델의 성능을 평가하기 위해 RMSE, MAE, R²(설명력) 지표를 산출합니다.
* `graph_builder.py`: 딥러닝 예측값(시간, 탄소)을 정규화하여 NetworkX 방향성 그래프(DiGraph)의 엣지 가중치로 통합하는 토폴로지 맵핑을 수행합니다.
* `routing.py`: 다익스트라(Dijkstra) 최단 경로 탐색 알고리즘을 사용하여 주어진 가중치(최단 시간 또는 최소 탄소)에 따른 최적 선형을 추출합니다.
* `visualization.py`: Folium과 AntPath 플러그인을 활용하여 최단 시간 경로(파란색)와 최소 탄소 경로(초록색)를 대화형 지도(HTML)로 렌더링합니다.
* `main.py`: 전체 파이프라인을 순차적으로 실행하는 메인 오케스트레이션 스크립트입니다 (데이터 로드 ▶ 전처리 ▶ 모델 학습 ▶ 그래프 구축 ▶ A/B 라우팅 시뮬레이션 ▶ 시각화).

## 🛠️ Environment Setup
프로젝트 실행을 위해 아래의 라이브러리 설치가 필요합니다. (Python 3.8 이상 권장)

```bash
pip install -r requirements.txt

🚀 How to Run
1. 경로 설정
실행 전 config.py 파일을 열어 로컬 데이터셋 환경에 맞게 다음 경로를 수정하십시오:

BASE_PATH: 주행 데이터(CSV)가 위치한 디렉토리 경로

SHP_PATH: 국가교통DB 노드-링크 데이터(MOCT_LINK.shp) 파일 경로

2. 메인 스크립트 실행
터미널에서 아래 명령어를 통해 전체 파이프라인을 실행합니다:
python main.py

3. 결과 확인
실행이 완료되면 평일 및 주말 조건에 대한 A/B 라우팅 비교 지도가 생성됩니다. outputs/ 디렉토리 내에 생성된 HTML 파일을 브라우저에서 열어 결과를 확인하십시오:
eco_routing_weekday.html
eco_routing_weekend.html

📊 Evaluation & Trade-off Analysis
본 프레임워크는 실제 도심-부도심 복합 구간(16.7km) 테스트베드에서 통행 시간과 환경적 영향 간의 뚜렷한 상호 상충(Trade-off) 관계를 실증했습니다.

최단 시간 경로 대비 에코 경로 성과: 에코 경로 선택 시 통행 시간은 약 22.3% 증가하지만, 우회 도로를 통한 연비 주행을 유도하여 탄소 배출량을 약 10.8% 절대 절감하는 데 성공했습니다.

공간 노이즈 트러블슈팅: main.py 내 GeoPandas 전처리 과정에서 EPSG:5181 투영 좌표계를 EPSG:4326으로 강제 보정(allow_override=True)하여 글로벌 맵 매핑 정합성을 완벽히 확보했습니다.