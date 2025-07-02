import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
API_KEY = os.getenv("SEOUL_API_KEY")

# 기본 설정
BASE_URL = "http://openapi.seoul.go.kr:8088"
SERVICE_NAME = "safeOpenCCTV"
REQ_TYPE = "json"
CHUNK_SIZE = 1000

# 자치구 리스트
SEOUL_DISTRICTS = [
    "종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구",
    "성북구", "강북구", "도봉구", "노원구", "은평구", "서대문구", "마포구",
    "양천구", "강서구", "구로구", "금천구", "영등포구", "동작구", "관악구",
    "서초구", "강남구", "송파구", "강동구"
]

# 저장 경로
SAVE_DIR = "data/raw/cctv"
os.makedirs(SAVE_DIR, exist_ok=True)

def fetch_cctv_by_district(district):
    """
    자치구별 CCTV 전체 데이터 수집
    """
    print(f"[INFO] 수집 시작: {district}")
    all_data = []
    start = 1

    while True:
        end = start + CHUNK_SIZE - 1
        url = f"{BASE_URL}/{API_KEY}/{REQ_TYPE}/{SERVICE_NAME}/{start}/{end}/{district}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"[ERROR] {district} 요청 실패 - 상태코드: {response.status_code}")
            break
        try:
            rows = response.json().get(SERVICE_NAME, {}).get("row", [])
            if not rows:
                break
            all_data.extend(rows)
        except Exception as e:
            print(f"[ERROR] 파싱 실패 - {district}: {e}")
            break

        if len(rows) < CHUNK_SIZE:
            break

        start += CHUNK_SIZE
        time.sleep(0.5)

    return pd.DataFrame(all_data)

# 전체 자치구 반복 수집 및 저장
for gu in SEOUL_DISTRICTS:
    df = fetch_cctv_by_district(gu)
    if not df.empty:
        filename = os.path.join(SAVE_DIR, f"cctv__{gu}.csv")
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"✅ 저장 완료: {filename}")
    else:
        print(f"[WARNING] {gu} 데이터 없음")

print("🎉 모든 자치구 CCTV 수집 및 저장 완료")
