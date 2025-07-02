import os
import sys
import math
import requests
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
LIGHT_API_KEY = os.getenv("LIGHT_API_KEY")
api_url = 'https://api.odcloud.kr/api/15107934/v1/uddi:20b10130-21ed-43f3-8e58-b8692fb8a2ff'

"""
전체 데이터 수 확인
"""
def get_total_pages(per_page: int = 1000) -> int:
    params = {
        "serviceKey": LIGHT_API_KEY,
        "returnType": "JSON",
        "page": 1,
        "perPage": per_page
    }
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    result_json = response.json()
    total_count = result_json.get('totalCount', 0)
    total_pages = math.ceil(total_count / per_page)
    return total_pages

"""
단일 페이지 데이터 수집
"""
def street_light(page: int, per_page: int = 1000):
    params = {
        "serviceKey": LIGHT_API_KEY,
        "returnType": "JSON",
        "page": page,
        "perPage": per_page,
    }
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    result_json = response.json()
    return result_json.get("data", [])

"""
병렬 수집
"""
def collect_all_data(per_page: int = 1000, max_workers: int = 10):
    total_pages = get_total_pages(per_page)
    all_data = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(street_light, page, per_page): page for page in range(1, total_pages + 1)}
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Collecting street light data"):
            try:
                data = future.result()
                all_data.extend(data)
            except Exception as e:
                print(f"Error on page {futures[future]}: {e}")

    return all_data


"""
CSV 저장
"""
def save_to_csv(data, filename="street_light__raw.csv"):
    df = pd.DataFrame(data)

    df = df[["위도", "경도"]]

    current_dir = os.path.dirname(__file__)  # 현재 스크립트 위치
    output_dir = os.path.abspath(os.path.join(current_dir, "../../data/raw"))
    output_file = os.path.join(output_dir, filename)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"CSV 저장 완료: {output_file}")

"""
메인 실행
"""
if __name__ == "__main__":
    data = collect_all_data()
#    print(data)
    save_to_csv(data)
