let markers = [];  // 경로 마커들을 저장할 배열
let anomalyDetected = false;  // 이상치 발견 여부를 추적하는 변수

// Flask 서버에서 이상 탐지 상태를 확인
function checkAnomalyStatus() {
    fetch('http://127.0.0.1:5000/anomaly_status')  // Flask의 anomaly_status 엔드포인트 호출
    .then(response => response.json())
    .then(data => {
        anomalyDetected = data.anomaly;  // Flask에서 받은 anomaly 상태

        if (anomalyDetected) {
            showAnomalyAlert();  // 이상 탐지 시 알림
        }
    })
    .catch(error => {
        console.error('Error fetching anomaly status:', error);
    });
}

function updateMapWithNewLocation() {
    if (anomalyDetected) return;  // 이상치 발견 후 탐지 중지

    fetch('Test/user_location.csv')  // CSV 파일 불러오기
    .then(response => response.text())
    .then(data => {
        const rows = data.trim().split("\n");
        const locations = [];

        for (let i = 1; i < rows.length; i++) { // 첫 번째 줄은 헤더
            const cols = rows[i].split(",");
            if (cols.length >= 3) {  // lat, lng, anomaly 여부 포함
                const lat = parseFloat(cols[0].trim());
                const lng = parseFloat(cols[1].trim());
                const isAnomaly = cols[2].trim() === "1";  // 이상치 여부 확인
                locations.push({ lat, lng, isAnomaly });
            }
        }

        locations.forEach(location => {
            let markerIcon = location.isAnomaly
                ? 'https://maps.google.com/mapfiles/ms/icons/red-dot.png'  // 이상치(빨간색)
                : 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png'; // 정상(파란색)

            let marker = L.marker([location.lat, location.lng], {
                icon: L.icon({ iconUrl: markerIcon })
            }).addTo(map)
              .bindPopup(location.isAnomaly ? "🚨 이상 탐지됨!" : "최근 위치");

            markers.push(marker);

            if (location.isAnomaly) {
                showAnomalyAlert(location);
                anomalyDetected = true;  // 이상치 발견 시 탐지 중단
            }
        });
    })
    .catch(error => {
        console.error('Error fetching location data:', error);
    });
}

// 2초마다 위치 업데이트 및 이상 탐지 상태 체크
setInterval(() => {
    updateMapWithNewLocation();
    checkAnomalyStatus();  // Flask 서버에서 이상 탐지 상태 확인
}, 2000);

function showAnomalyAlert(location = null) {
    if (location) {
        alert("🚨 이상치 발견: 위치 (" + location.lat + ", " + location.lng + ")");
    } else {
        alert("🚨 이상치가 탐지되었습니다!");
    }
}