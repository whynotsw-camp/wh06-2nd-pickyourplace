import os
import requests
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# .env에서 인증키 불러오기
load_dotenv()
API_KEY = os.getenv("SEOUL_API_KEY")

# API 구성 요소
API_TYPE = "json"
SERVICE_NAME = "SearchParkInfoService"
BASE_URL = f"http://openAPI.seoul.go.kr:8088/{API_KEY}/{API_TYPE}/{SERVICE_NAME}"

# 공원 데이터 수집 함수
def fetch_park_data(start_index: int, end_index: int) -> list:
    url = f"{BASE_URL}/{start_index}/{end_index}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"요청 실패: {response.status_code} - {response.text}")

    data = response.json()
    try:
        return data[SERVICE_NAME]["row"]
    except KeyError:
        print(f"[경고] 데이터 없음 (start={start_index}, end={end_index})")
        return []

# 전체 데이터 반복 수집
def collect_all_park_data(batch_size=1000, max_limit=10000):
    results = []
    for start in tqdm(range(1, max_limit + 1, batch_size)):
        end = start + batch_size - 1
        batch = fetch_park_data(start, end)
        if not batch:
            break
        results.extend(batch)
    return pd.DataFrame(results)

# 실행
if __name__ == "__main__":
    df = collect_all_park_data()
    
    os.makedirs("data/raw/", exist_ok=True)
    df.to_csv("data/raw/park__raw.csv", index=False, encoding="utf-8-sig")
    print("✅ 공원 데이터 저장 완료: data/raw/park__raw.csv")
