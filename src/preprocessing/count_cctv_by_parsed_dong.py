import os
import sys
import re
import pandas as pd
from glob import glob
from tqdm import tqdm

# src 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.geocoding.admin_mapper import get_gu_dong_codes

# 경로 설정
INPUT_DIR = "data/raw/cctv"
OUTPUT_PATH = "data/processed_counts/cctv_parsed__counts.csv"
MIX_PATH = "data/reference/KIKmix.20250701.xlsx"

# 1. CCTV CSV 통합
csv_files = glob(os.path.join(INPUT_DIR, "*.csv"))
all_data = []

for file in csv_files:
    try:
        df = pd.read_csv(file)
        if 'ADDR' not in df.columns or 'SVCAREAID' not in df.columns:
            continue
        df = df[['SVCAREAID', 'ADDR']].dropna()
        all_data.append(df)
    except Exception as e:
        print(f"[ERROR] {file} - {e}")

df_all = pd.concat(all_data, ignore_index=True)
df_all.rename(columns={"SVCAREAID": "gu_name"}, inplace=True)

def extract_dong_name(addr):
    if isinstance(addr, str):
        # 1. "XX동" 명시된 경우 우선 사용
        match = re.search(r"([가-힣0-9]+동)", addr.strip())
        if match:
            return match.group(1)
        
        # 2. fallback: "개포2-212-00" → "개포2" 추출
        match = re.match(r"([가-힣0-9]+)[\s\-]", addr.strip())
        if match:
            return match.group(1) + "동"
    return ""


df_all["dong_name"] = df_all["ADDR"].apply(extract_dong_name)

# 3. 그룹별 개수 집계 (동 이름이 없어도 포함!)
result = (
    df_all.groupby(["gu_name", "dong_name"], dropna=False)
    .size()
    .reset_index(name="counts")
)

# 4. mix 파일에서 gu_code 딕셔너리 생성
mix_df = pd.read_excel(MIX_PATH, dtype=str)
mix_df.columns = mix_df.columns.str.strip()
dong_code_col = [col for col in mix_df.columns if "코드" in col][0]
gu_name_col = [col for col in mix_df.columns if "구" in col][0]
mix_df["gu_code"] = mix_df[dong_code_col].str[:5]
gu_map = dict(mix_df[[gu_name_col, "gu_code"]].drop_duplicates().values)

# 5. 매핑 함수 정의
def get_gu_and_dong_code(row):
    gu_name = row["gu_name"]
    dong_name = row["dong_name"]
    gu_code, dong_code = get_gu_dong_codes(gu_name, dong_name)
    if gu_code is None:
        gu_code = gu_map.get(gu_name)
    return pd.Series([gu_code, dong_code])

# 6. 적용
tqdm.pandas()
result[["gu_code", "dong_code"]] = result.progress_apply(get_gu_and_dong_code, axis=1)

# 7. 저장
result = result[["gu_code", "dong_code", "gu_name", "dong_name", "counts"]]
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
result.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print(f"[저장 완료] → {OUTPUT_PATH}")
