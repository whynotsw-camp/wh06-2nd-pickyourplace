import requests
from dotenv import load_dotenv
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm       
import math
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from geocoding import reverse_geocode
from geocoding import road_address_to_coordinates, coordinates_to_jibun_address, coordinates_to_road_address
from geocoding import extract_gu_and_dong, get_gu_dong_codes


"""소재지지번주소 -> 구, 동으로 분리"""
def safety_bell_processed(file_path: str, output_path: str):
    df = pd.read_csv(file_path)
    processed_list = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        address = row.get("소재지지번주소")
        
        # 문자열이 아니면 건너뛰기
        if not isinstance(address, str):
            continue
        
        try:
            gu, dong = extract_gu_and_dong(address)
            row["gu_name"] = gu
            row["dong_name"] = dong
            processed_list.append(row)
        except Exception as e:
            print(f"주소 추출 오류: {address}, 에러: {e}")
            continue

    result_df = pd.DataFrame(processed_list)
     # 자치구별 개수 집계
    gu_counts = result_df['dong_name'].value_counts().reset_index()
    gu_counts.columns = ['dong_name', 'count']

    gu_counts_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed', 'bell_dong__counts.csv'))
    
    # 코드 돌리고 주석 처리할 것 
    # 경로 디렉토리 없으면 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(gu_counts_path), exist_ok=True)

    gu_counts.to_csv(gu_counts_path,index=False, encoding="utf-8-sig")  
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    return result_df, gu_counts

# 절대 경로 설정 및 실행
file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'safety_bell__raw.csv'))
print("절대경로로 확인:", file_path)

safety_bell_processed(
    file_path,
    "../../data/processed/safety_bell__processed.csv"
)
