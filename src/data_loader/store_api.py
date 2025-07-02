import os
import math
import requests
from dotenv import load_dotenv
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

load_dotenv()
API_KEY = os.getenv("SEOUL_API_KEY")
API_BASE_URL = "http://openapi.seoul.go.kr:8088"
REQ_TYPE = "json"
SERVICE_NAME = "LOCALDATA_082501"
CHUNK_SIZE = 1000


# 단일 페이지 조회
def store_data_load(page: int, per_page: int, retries=3, delay=1):
    start = (page - 1) * per_page + 1
    end = page * per_page
    url = f"{API_BASE_URL}/{API_KEY}/{REQ_TYPE}/{SERVICE_NAME}/{start}/{end}"

    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            rows = data.get(SERVICE_NAME, {}).get("row", [])
            return rows
        except Exception as e:
            print(f"[ERROR] 페이지 {page} 요청 실패 (시도 {attempt+1}): {e}")
            time.sleep(delay)
    return []

# 모든 페이지 데이터 조회
def all_store_data(per_page=CHUNK_SIZE, max_workers=10):
    url = f"{API_BASE_URL}/{API_KEY}/{REQ_TYPE}/{SERVICE_NAME}/1/1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        total_count = int(data.get(SERVICE_NAME, {}).get("list_total_count", 0))
    except Exception as e:
        print(f"[ERROR] 전체 데이터 수 확인 실패: {e}")
        return []

    if total_count == 0:
        print("[WARNING] 데이터가 없습니다.")
        return []

    total_pages = math.ceil(total_count / per_page)
    print(f"[INFO] 총 데이터: {total_count}건, 페이지: {total_pages}")

    all_results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(store_data_load, page, per_page) for page in range(1, total_pages + 1)]

        for future in tqdm(as_completed(futures), total=total_pages, desc="데이터 수집 중"):
            try:
                result = future.result()
                if result:
                    all_results.extend(result)
            except Exception as e:
                print(f"[ERROR] 에러 발생: {e}")

    return all_results

def save_to_csv(data: list, output_path: str = "data/raw/store__raw.csv"):
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {output_path}")

# 실행
if __name__ == "__main__":
    store_data = all_store_data()
    save_to_csv(store_data)
    print("[종료] 작업 완료")