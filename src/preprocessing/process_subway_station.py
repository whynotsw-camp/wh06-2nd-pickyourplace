import os
import sys
import pandas as pd
from tqdm import tqdm

# src 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 내부 모듈 import
from src.geocoding.vworld_geocode import coordinates_to_jibun_address
from src.geocoding.admin_mapper import extract_gu_and_dong, get_gu_dong_codes

# 파일 경로 설정
INPUT_PATH = "data/raw/subway_station__raw.csv"
OUTPUT_PATH = "data/processed/subway_station__processed.csv"

# 데이터 로드
df = pd.read_csv(INPUT_PATH)

# tqdm 설정
tqdm.pandas()

# 1. 위도/경도로 지번주소 변환
df["jibun_address"] = df.progress_apply(
    lambda row: coordinates_to_jibun_address(row["longitude"], row["latitude"]), axis=1
)

# 2. 서울특별시만 필터링
df = df[df["jibun_address"].str.startswith("서울특별시", na=False)].copy()

# 3. 지번주소 → 구/동명 추출
df[["gu_name", "dong_name"]] = df["jibun_address"].progress_apply(
    lambda addr: pd.Series(extract_gu_and_dong(addr))
)

# 4. 구/동명 → 행정코드 매핑
df[["gu_code", "dong_code"]] = df.progress_apply(
    lambda row: pd.Series(get_gu_dong_codes(row["gu_name"], row["dong_name"])),
    axis=1
)

# 5. 결과 저장
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print(f"[완료] 서울시 지하철역 {len(df)}개 전처리 및 저장: {OUTPUT_PATH}")
