import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
API_KEY = os.getenv("MARKET_API_KEY")
API_BASE_URL = "https://api.odcloud.kr/api/15052837/v1/uddi:8e90c34b-c086-422f-882a-d3c15efd101f"

# 단일 페이지 조회
def market_data_load(page=1, per_page=1000):
    params = {
        "page": page,
        "perPage": per_page,
        "returnType": "json",
        "serviceKey": API_KEY
        }
    
    try:
        response = requests.get(API_BASE_URL, params=params)
        print(f"[요청] URL: {response.url}")
        print(f"[응답] 상태 코드: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            items = data.get("data", [])
            print(f"[수신] {len(items)}건")
            return items
        else:
            print(f"[오류] 요청 실패 - 상태 코드: {response.status_code}")
            return []
        
    except Exception as e:
        print(f"[예외 발생] {e}")
        return []

# 모든 시장 데이터 조회
def all_market_data() -> list:
    all_data = []
    page = 1
    per_page = 1000

    while True:
        print(f"[진행중] 페이지 {page} 요청 중...")
        batch = market_data_load(page=page, per_page=per_page)

        if not batch:
            break

        all_data.extend(batch)

        if len(batch) < per_page:
            break

        page += 1

    print(f"[총 수신] {len(all_data)}건")
    return all_data

def save_to_csv(data: list, output_path: str = "data/raw/market__raw.csv"):
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {output_path}")

# 실행
if __name__ == "__main__":
    market_data = all_market_data()
    save_to_csv(market_data)