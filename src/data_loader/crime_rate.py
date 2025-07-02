import requests
from dotenv import load_dotenv
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import math
import sys

# 경로 설정: geocoding 모듈 참조를 위해 상위 디렉토리 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 외부 함수 import
from geocoding import reverse_geocode
from geocoding import road_address_to_coordinates, coordinates_to_jibun_address, coordinates_to_road_address
from geocoding import extract_gu_and_dong, get_gu_dong_codes, get_gu_code

def calculate_percentages(file_path: str):
    # 원본 엑셀 파일 불러오기
    df_all = pd.read_excel(file_path, header=None)

    # '합계' 행에서 전체 발생 건수 추출
    total_row = df_all.iloc[4]
    raw_total = str(total_row.iloc[2]).replace(",", "")
    total_occurrence = pd.to_numeric(raw_total, errors='coerce')
    if pd.isna(total_occurrence):
        raise ValueError(f"Invalid total crime count: {total_row.iloc[2]}")

    # 자치구별 범죄 데이터는 6번째 줄부터 시작
    df = df_all.iloc[5:].copy()

    # 컬럼명 지정
    df.columns = [
        "district_category", "gu_name", "counts", "total_arrests",
        "murder_cases", "murder_arrests", "robbery_cases", "robbery_arrests",
        "sexual_cases", "sexual_arrests", "theft_cases", "theft_arrests",
        "violence_cases", "violence_arrests"
    ]

    # 필요 없는 컬럼 제거
    df.drop(columns=[
        "district_category", "total_arrests",
        "murder_arrests", "robbery_arrests",
        "sexual_arrests", "theft_arrests", "violence_arrests"
    ], inplace=True)

    # 숫자형 변환
    for col in ["counts", "murder_cases", "robbery_cases", "sexual_cases", "theft_cases", "violence_cases"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 범죄 유형별 발생률 계산
    crime_types = {
        "murder": "murder_cases",
        "robbery": "robbery_cases",
        "sexual": "sexual_cases",
        "theft": "theft_cases",
        "violence": "violence_cases"
    }

    for eng_name, case_col in crime_types.items():
        rate_col = f"{eng_name}_rate(%)"
        df[rate_col] = (df[case_col] / total_occurrence * 100).round(2)

    # 전체 발생률
    df["total_rate(%)"] = (df["counts"] / total_occurrence * 100).round(2)

    # (외부 파일에서 정의된 함수 사용)
    # geocoding/admin_mapper.py 에 정의된 get_gu_code() 함수를 사용해 자치구명을 코드(5자리)로 변환
    df["gu_code"] = df["gu_name"].apply(get_gu_code)

    # gu_code 컬럼을 맨 앞으로 이동
    cols = df.columns.tolist()
    cols.insert(0, cols.pop(cols.index("gu_code")))  # gu_code를 첫 번째로 이동
    df = df[cols]

    # CSV로 저장
    output_path_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed', 'crime_rate__processed.csv'))
    df.to_csv(output_path_abs, index=False, encoding="utf-8-sig")
    print(f"[Saved] → {output_path_abs}")

# 실행
if __name__ == "__main__":
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', '5대범죄발생현황.xlsx'))
    calculate_percentages(file_path)
