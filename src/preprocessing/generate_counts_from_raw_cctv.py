# import os
# import sys
# import pandas as pd
# from glob import glob
# from tqdm import tqdm

# # src 경로 추가
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# from src.geocoding.admin_mapper import extract_gu_and_dong, get_gu_dong_codes
# from src.geocoding.vworld_geocode import coordinates_to_jibun_address

# # 경로 설정
# INPUT_DIR = "data/raw/cctv"
# OUTPUT_PATH = "data/processed_counts/cctv__counts.csv"

# # CSV 파일 목록 수집
# csv_files = glob(os.path.join(INPUT_DIR, "*.csv"))
# all_data = []

# for file in csv_files:
#     try:
#         df = pd.read_csv(file)
#         if 'WGSXPT' not in df.columns or 'WGSYPT' not in df.columns:
#             continue
#         df = df[['WGSXPT', 'WGSYPT']].dropna()
#         df.columns = ['latitude', 'longitude']
#         all_data.append(df)
#     except Exception as e:
#         print(f"[ERROR] {file} - {e}")

# # 통합
# df_all = pd.concat(all_data, ignore_index=True)

# # tqdm 적용
# tqdm.pandas()

# # 위경도 → 지번주소
# df_all["jibun_address"] = df_all.progress_apply(
#     lambda row: coordinates_to_jibun_address(row["longitude"], row["latitude"]),
#     axis=1
# )

# # 주소 → 구, 동
# df_all[["gu_name", "dong_name"]] = df_all["jibun_address"].progress_apply(
#     lambda x: pd.Series(extract_gu_and_dong(x) if isinstance(x, str) else ("", "")),
# )

# # 구, 동 → 행정동 코드
# df_all[["gu_code", "dong_code"]] = df_all.progress_apply(
#     lambda row: pd.Series(get_gu_dong_codes(row["gu_name"], row["dong_name"])),
#     axis=1
# )

# # NaN 제거 및 형변환
# df_all = df_all.dropna(subset=["gu_code", "dong_code"])
# df_all["gu_code"] = df_all["gu_code"].astype(int)
# df_all["dong_code"] = df_all["dong_code"].astype(int)

# # 집계
# result = (
#     df_all.groupby(["gu_code", "dong_code", "gu_name", "dong_name"])
#     .size()
#     .reset_index(name="counts")
# )

# # 저장
# os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
# result.to_csv(OUTPUT_PATH, index=False)
# print(f"[저장 완료] → {OUTPUT_PATH}")
#####################################################################
"""
Geocoder API 사용횟수를 초과하였습니다. 이슈 발생
Windows PowerShell >  taskkill /F /IM python.exe
입력하여 python 강제종료 필요
"""
import os
import sys
import pandas as pd
from glob import glob
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

# 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.geocoding.admin_mapper import extract_gu_and_dong, get_gu_dong_codes
from src.geocoding.vworld_geocode import coordinates_to_jibun_address

# 파일 경로 설정
INPUT_DIR = "data/raw/cctv"
OUTPUT_PATH = "data/processed_counts/cctv__counts.csv"

# ---------- 1. CCTV 원본 CSV 통합 ----------
csv_files = glob(os.path.join(INPUT_DIR, "*.csv"))
all_data = []

for file in csv_files:
    try:
        df = pd.read_csv(file)
        if 'WGSXPT' not in df.columns or 'WGSYPT' not in df.columns:
            continue
        df = df[['WGSYPT', 'WGSXPT']].dropna()
        df.columns = ['longitude', 'latitude']  # 순서 주의
        all_data.append(df)
    except Exception as e:
        print(f"[ERROR] {file} - {e}")

df_all = pd.concat(all_data, ignore_index=True)

# ---------- 2. 중복 좌표 캐싱 ----------
coordinate_cache = {}

def get_jibun_with_cache(coord):
    lon, lat = coord
    key = (round(lon, 6), round(lat, 6))  # 소수점 6자리까지 캐싱
    if key in coordinate_cache:
        return coordinate_cache[key]

    jibun = coordinates_to_jibun_address(lon, lat)
    coordinate_cache[key] = jibun
    return jibun

# ---------- 3. 병렬 처리로 지번주소 수집 ----------
def fetch_jibun(coord):
    try:
        return get_jibun_with_cache(coord)
    except Exception as e:
        print(f"[ERROR] 좌표 변환 실패: {coord} - {e}")
        return None

if __name__ == "__main__":
    tqdm.pandas()

    coords = df_all[["longitude", "latitude"]].values.tolist()

    print(f"[INFO] 병렬 처리 시작 (총 {len(coords)}건)...")
    with Pool(processes=cpu_count()) as pool:
        jibun_list = list(tqdm(pool.imap(fetch_jibun, coords), total=len(coords)))

    df_all["jibun_address"] = jibun_list

    # ---------- 4. 구/동 추출 및 행정동 코드 매핑 ----------
    df_all[["gu_name", "dong_name"]] = df_all["jibun_address"].progress_apply(
        lambda x: pd.Series(extract_gu_and_dong(x) if isinstance(x, str) else ("", "")),
    )

    df_all[["gu_code", "dong_code"]] = df_all.progress_apply(
        lambda row: pd.Series(get_gu_dong_codes(row["gu_name"], row["dong_name"])),
        axis=1
    )

    df_all = df_all.dropna(subset=["gu_code", "dong_code"])
    df_all["gu_code"] = df_all["gu_code"].astype(int)
    df_all["dong_code"] = df_all["dong_code"].astype(int)

    # ---------- 5. 집계 및 저장 ----------
    result = (
        df_all.groupby(["gu_code", "dong_code", "gu_name", "dong_name"])
        .size()
        .reset_index(name="counts")
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"[저장 완료] → {OUTPUT_PATH}")
