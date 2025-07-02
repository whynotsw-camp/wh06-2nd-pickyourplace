"""
raw 데이터에서 아래 두개의 주소가 전처리 실패함
1. 서울종암경찰서,성북구 종암로 135,서울특별시경찰청,서울특별시
=> 현재 임시청사에서 신축으로 이전 중
서울종암경찰서 (신축)
도로명주소: 서울 성북구 종암로 137
지번주소: 서울특별시 성북구 종암동 3-1260

2. 서울구로경찰서,구로구 가마산로 235,서울특별시경찰청,서울특별시
=> 현재 신축중, 임시청사 사용중
서울구로경찰서 (임시청사)
도로명주소: 서울 구로구 새말로 97 신도림 테크노마트 5층
지번주소: 서울 구로구 구로동 3-25
"""

import os
import sys
import pandas as pd
from tqdm import tqdm

# 루트 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.geocoding.vworld_geocode import (
    road_address_to_coordinates,
    coordinates_to_jibun_address,
)
from src.geocoding.admin_mapper import (
    extract_gu_and_dong,
    get_gu_dong_codes,
)

# 파일 경로
INPUT_PATH = "data/raw/police_office__raw.csv"
OUTPUT_PATH = "data/processed/police_office__processed.csv"
FAILED_PATH = "data/processed/police_office__failed.csv"

# 도로명 주소 보정 목록
manual_address_corrections = {
    # "서울종암경찰서": "서울특별시 성북구 종암로 137", <= 처리안됨. 신축 건물이 아직 VWorld에 등록되지 않았을 수 있음
    "서울구로경찰서": "서울특별시 구로구 새말로 97",
}

# 지번 주소 보정 목록
manual_jibun_corrections = {
    "서울종암경찰서": "서울특별시 성북구 종암동 3-1260",
}


def preprocess_police_data(input_path: str, output_path: str):
    df = pd.read_csv(input_path)
    seoul_df = df[df["위치"] == "서울특별시"].copy()
    print(f"[INFO] 서울 경찰서 개수: {len(seoul_df)}")

    # 결과 저장용 리스트
    jibun_addresses, gu_names, dong_names = [], [], []
    gu_codes, dong_codes = [], []
    road_addresses = []
    failed_addresses = []

    for _, row in tqdm(seoul_df.iterrows(), total=len(seoul_df), desc="주소 전처리"):
        police_name = row["경찰서명칭"]
        jibun = None
        gu, dong = None, None
        gu_code, dong_code = None, None

        # 1. 지번 보정이 있다면 → 바로 사용
        if police_name in manual_jibun_corrections:
            jibun = manual_jibun_corrections[police_name]
            road_addresses.append(jibun)
            print(f"[🔁 지번주소 보정 적용] {police_name} → {jibun}")
        else:
            # 2. 도로명 보정 또는 기본 도로명 주소 사용
            if police_name in manual_address_corrections:
                full_address = manual_address_corrections[police_name]
                print(f"[🔁 도로명 주소 보정 적용] {police_name} → {full_address}")
            else:
                full_address = f"{row['위치']} {row['경찰서주소']}"

            road_addresses.append(full_address)

            try:
                lon, lat = road_address_to_coordinates(full_address)
                jibun = coordinates_to_jibun_address(lon, lat)
            except Exception as e:
                print(f"[❌ 주소 변환 실패] {full_address} → {e}")

        # 3. 지번 주소 → 구/동/코드
        if jibun:
            try:
                gu, dong = extract_gu_and_dong(jibun)
                gu_code, dong_code = get_gu_dong_codes(gu, dong)
            except Exception as e:
                print(f"[❌ 지번→코드 실패] {jibun} → {e}")
        else:
            failed_addresses.append({
                "경찰서명칭": police_name,
                "입력주소": row["경찰서주소"],
                "주소전처리": road_addresses[-1],
                "지번주소": jibun,
                "gu": gu,
                "dong": dong
            })

        # 결과 저장
        jibun_addresses.append(jibun)
        gu_names.append(gu)
        dong_names.append(dong)
        gu_codes.append(gu_code)
        dong_codes.append(dong_code)

        # 실패한 전체 주소 저장
        if not gu or not dong:
            failed_addresses.append({
                "경찰서명칭": police_name,
                "입력주소": full_address,
                "위도": lat,
                "경도": lon,
                "지번주소": jibun,
                "gu": gu,
                "dong": dong
            })

    # 컬럼 추가
    seoul_df["road_addresses"] = road_addresses
    seoul_df["jibun_address"] = jibun_addresses
    seoul_df["gu_name"] = gu_names
    seoul_df["dong_name"] = dong_names
    seoul_df["gu_code"] = gu_codes
    seoul_df["dong_code"] = dong_codes

    # 불필요 컬럼 제거
    seoul_df.drop(columns=["경찰서주소", "위치"], inplace=True, errors="ignore")
    
    # 저장
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    seoul_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[✅ 저장 완료] {output_path}")

    # 실패한 주소도 별도 저장
    if failed_addresses:
        pd.DataFrame(failed_addresses).to_csv(FAILED_PATH, index=False, encoding="utf-8-sig")
        print(f"[⚠️ 주소 처리 실패 {len(failed_addresses)}건 저장] → {FAILED_PATH}")

if __name__ == "__main__":
    preprocess_police_data(INPUT_PATH, OUTPUT_PATH)
