let markers = [], polylines = [], pathCoords = [];
let updateTimer = null, anomalyDetected = false;
let csvFile = null, csvRows = [], currentRowIndex = 0;
const hasHeader = true;
const initialZoom = 7;
const detectionZoom = 16;

// 이상 상태 확인
function checkAnomalyStatus() {
  fetch('/anomaly_status')
    .then(res => res.json())
    .then(data => {
      anomalyDetected = data.anomaly;
      if (anomalyDetected) {
        showAnomalyAlert();
        clearInterval(updateTimer);
      }
    })
    .catch(console.error);
}

// 지도 초기화
function clearMap() {
  markers.forEach(m => map.removeLayer(m));
  polylines.forEach(l => map.removeLayer(l));
  markers = [];
  polylines = [];
  pathCoords = [];
}

// CSV 한 번 읽어서 배열에 저장
function loadCsvData(callback) {
  fetch(csvFile)
    .then(r => r.text())
    .then(text => {
      const rows = text.trim().split('\n');
      csvRows = rows.slice(hasHeader ? 1 : 0);
      currentRowIndex = 0;
      callback();
    })
    .catch(console.error);
}

// 다음 한 줄(위치)만 꺼내서 그리기
function addNextPoint() {
  if (currentRowIndex >= csvRows.length) {
    clearInterval(updateTimer);
    return;
  }

  const cols = csvRows[currentRowIndex].split(',');
  const lat = parseFloat(cols[0]), lng = parseFloat(cols[1]);
  const isAnom = cols[2]?.trim() === '1';

  const iconUrl = isAnom
    ? 'https://maps.google.com/mapfiles/ms/icons/red-dot.png'
    : 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png'

  // 마커 추가
  const marker = L.marker([lat, lng], {
    icon: L.icon({ iconUrl, iconSize: [32,32] })
  }).addTo(map).bindPopup(isAnom ? '🚨 이상 탐지됨!' : '최근 위치');

  if (isAnom){
    marker.setIcon(L.icon({iconUrl: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png', iconSize: [32, 32]}))
  }
  markers.push(marker);

  // 폴리라인 추가
  pathCoords.push([lat, lng]);
  if (pathCoords.length >= 2) {
    const seg = pathCoords.slice(-2);
    const line = L.polyline(seg, { color: 'blue', weight: 3, opacity: 0.5 }).addTo(map);
    polylines.push(line);
  }

  if (isAnom) {
    // 이상치 탐지 마커가 뜨기 전에 아이콘을 빨간색으로
    alert(`🚨 이상치: (${lat}, ${lng})`);
  }

  map.flyTo([lat, lng], detectionZoom, { animate: true, duration: 1.5 });
  currentRowIndex++;
}

// 기법 선택 후 업데이트 시작
function startUpdating(tech) {
  clearInterval(updateTimer);
  clearMap();
  anomalyDetected = false;

  const fileMap = {
    cell_frequency:   '/static/test_cell.csv',
    pair_frequency:   '/static/test_pair.csv',
    trace_similarity: '/static/test_similarity.csv'
  };
  csvFile = fileMap[tech];

  loadCsvData(() => {
    // 1) CSV 첫 줄(출발지)에서 lat,lng 뽑아오기
    const firstCols = csvRows[0].split(',');
    const startLat = parseFloat(firstCols[0]);
    const startLng = parseFloat(firstCols[1]);

    // 2) 시작 위치로 줌업 (detectionZoom)
    map.setView([startLat, startLng], detectionZoom);

    // 3) 2초마다 한 줄씩 추가
    updateTimer = setInterval(() => {
      addNextPoint();
      checkAnomalyStatus();
    }, 2000);
  });
}

// 모달에서 확인 버튼 클릭
function onTechniqueConfirm() {
  const tech = document.querySelector('input[name=tech]:checked').value;
  document.getElementById('techniqueModal').style.display = 'none';

  fetch('/start_dag', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ technique: tech, reset_path: true })
  })
    .then(res => {
      if (!res.ok) console.error('DAG Trigger 실패:', res.status);
      else startUpdating(tech);
    })
    .catch(console.error);
}

// 이상 알림
function showAnomalyAlert(location = null) {
  alert(location
    ? `🚨 이상치 발견: 위치 (${location.lat}, ${location.lng})`
    : '🚨 평소 자주 가지 않은 경로입니다!');
  clearMap();
}

// 페이지 로드 시 초기화
window.onload = () => {
  clearMap();
  map.setView([36.5, 127.5], initialZoom);
};
