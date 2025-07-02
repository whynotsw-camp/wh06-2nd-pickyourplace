import os
import sys
import pandas as pd
from tqdm import tqdm

# 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.geocoding.vworld_geocode import coordinates_to_jibun_address
from src.geocoding.admin_mapper import extract_gu_and_dong, get_gu_dong_codes

RAW_PATH = "data/raw/bus_stop__raw.csv"
OUTPUT_PATH = "data/processed/bus_stop__processed.csv"

def enrich_with_admin_info(df: pd.DataFrame) -> pd.DataFrame:
    gu_names = []
    dong_names = []
    gu_codes = []
    dong_codes = []
    jibun_addresses = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="📍 행정동 정보 추출 중"):
        try:
            lon = row["XCRD"]
            lat = row["YCRD"]

            jibun = coordinates_to_jibun_address(lon, lat)
            jibun_addresses.append(jibun)

            if jibun is None:
                gu_names.append(None)
                dong_names.append(None)
                gu_codes.append(None)
                dong_codes.append(None)
                continue

            gu, dong = extract_gu_and_dong(jibun)
            gu_code, dong_code = get_gu_dong_codes(gu, dong)

            gu_names.append(gu)
            dong_names.append(dong)
            gu_codes.append(gu_code)
            dong_codes.append(dong_code)

        except Exception as e:
            print(f"[❌ 에러] {e}")
            jibun_addresses.append(None)
            gu_names.append(None)
            dong_names.append(None)
            gu_codes.append(None)
            dong_codes.append(None)

    df["jibun_address"] = jibun_addresses
    df["gu_name"] = gu_names
    df["dong_name"] = dong_names
    df["gu_code"] = gu_codes
    df["dong_code"] = dong_codes

    return df


def load_and_process():
    if not os.path.exists(RAW_PATH):
        print(f"[❌ 파일 없음] {RAW_PATH}")
        return

    df = pd.read_csv(RAW_PATH)

    df = enrich_with_admin_info(df)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"[✅ 저장 완료] → {OUTPUT_PATH}")


if __name__ == "__main__":
    load_and_process()
