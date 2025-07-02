from dotenv import load_dotenv
import os
import requests
import pandas as pd

# 환경 변수 로딩
load_dotenv()

try:
    API_KEY = os.getenv("POLICE_OFFICE_DECODING_API_KEY")
    if API_KEY is None:
        raise ValueError("'.env' 파일에 'POLICE_OFFICE_DECODING_API_KEY'가 정의되어 있지 않습니다.")
except Exception as e:
    print(f"[환경 변수 오류] {e}")
    API_KEY = None

API_BASE_URL = "https://api.odcloud.kr/api/15124966/v1/uddi:345a2432-5fee-4c49-a353-80b62496a43b"

def fetch_police_station_data(page: int = 1, per_page: int = 1000) -> list:
    params = {
        "page": page,
        "perPage": per_page,
        "returnType": "json",
        "serviceKey": API_KEY
    }

    response = requests.get(API_BASE_URL, params=params)

    print(f"[DEBUG] 요청 URL: {response.url}")
    print(f"[DEBUG] 응답 코드: {response.status_code}")

    if response.status_code == 200:
        try:
            data = response.json()
            if 'data' not in data:
                print("[❌ 오류] 'data' 키가 응답에 없습니다.")
                return []
            print(f"[✅ 성공] {len(data['data'])}건 수신")
            return data['data']
        except Exception as e:
            print(f"[❌ 파싱 실패] {e}")
            return []
    else:
        print(f"[❌ 요청 실패] 응답 코드: {response.status_code}")
        return []

def fetch_police_station_data_all() -> list:
    all_data = []
    page = 1
    per_page = 1000

    while True:
        print(f"[INFO] 페이지 요청: {page}")
        chunk = fetch_police_station_data(page, per_page)
        if not chunk:
            break
        all_data.extend(chunk)
        if len(chunk) < per_page:
            break
        page += 1

    return all_data

def save_to_csv(data: list, output_path: str = "data/raw/police_office__raw.csv"):
    if not data:
        print("[❌ 저장 실패] 저장할 데이터가 없습니다.")
        return
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[✅ 저장 완료] {output_path}")

# 실행
if __name__ == "__main__":
    print("[TEST] 전국 경찰서 데이터를 수집하고 CSV로 저장합니다...")
    police_data = fetch_police_station_data_all()
    save_to_csv(police_data)
