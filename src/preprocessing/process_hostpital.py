import os
import sys
import pandas as pd
from tqdm import tqdm

# 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.geocoding.vworld_geocode import coordinates_to_jibun_address
from src.geocoding.admin_mapper import (
    smart2_parse_gu_and_dong,
    extract_gu_and_dong,
    get_gu_dong_codes
)

INPUT_PATH = "data/raw/hospital__raw.csv"
OUTPUT_PATH = "data/processed/hospital__processed.csv"

KEY_COLUMNS = [
    "기관ID", "주소", "기관명", "대표전화1", "응급의료기관코드명",
    "병원경도", "병원위도"
]

def enrich_with_admin_info(df: pd.DataFrame) -> pd.DataFrame:
    gu_names, dong_names, gu_codes, dong_codes = [], [], [], []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="📍 행정동 추출 중"):
        try:
            addr = row["주소"]
            lon = row["병원경도"]
            lat = row["병원위도"]

            # 1. 주소 기반 시도 (괄호 안에 동/가 있을 경우)
            gu, dong = smart2_parse_gu_and_dong(addr)

            # 2. 실패 시 좌표 → 지번주소 기반
            if not gu or not dong:
                jibun = coordinates_to_jibun_address(lon, lat)
                if not jibun:
                    raise ValueError("지번주소 없음")
                gu, dong = extract_gu_and_dong(jibun)

            if not gu or not dong:
                raise ValueError("구/동 추출 실패")

            gu_code, dong_code = get_gu_dong_codes(gu, dong)

            gu_names.append(gu)
            dong_names.append(dong)
            gu_codes.append(gu_code)
            dong_codes.append(dong_code)

        except Exception as e:
            print(f"[❌ 에러] {addr} → {e}")
            gu_names.append(None)
            dong_names.append(None)
            gu_codes.append(None)
            dong_codes.append(None)

    df["gu_name"] = gu_names
    df["dong_name"] = dong_names
    df["gu_code"] = gu_codes
    df["dong_code"] = dong_codes
    return df


def load_and_process():
    if not os.path.exists(INPUT_PATH):
        print(f"[❌ 입력 파일 없음] {INPUT_PATH}")
        return

    df = pd.read_csv(INPUT_PATH, encoding="cp949")

    keep = [col for col in KEY_COLUMNS if col in df.columns]
    df = df[keep].copy()

    df = enrich_with_admin_info(df)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"[✅ 저장 완료] → {OUTPUT_PATH}")


if __name__ == "__main__":
    load_and_process()
