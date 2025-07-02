import os
import sys
import pandas as pd
from glob import glob

# 파일 경로 설정
INPUT_DIR = "data/raw/cctv"
OUTPUT_PATH = "data/processed_counts/cctv_gu__counts.csv"

# 1. CCTV CSV 통합
csv_files = glob(os.path.join(INPUT_DIR, "*.csv"))
all_data = []

for file in csv_files:
    try:
        df = pd.read_csv(file)
        if 'SVCAREAID' not in df.columns:
            continue
        df = df[['SVCAREAID']].dropna()
        all_data.append(df)
    except Exception as e:
        print(f"[ERROR] {file} - {e}")

df_all = pd.concat(all_data, ignore_index=True)
df_all.rename(columns={"SVCAREAID": "gu_name"}, inplace=True)
df_all["gu_name"] = df_all["gu_name"].str.strip()

# 2. 구별 개수 집계
result = (
    df_all.groupby("gu_name")
    .size()
    .reset_index(name="counts")
)

# 3. gu_code 매핑 (KIKmix 기반)
MIX_PATH = "data/reference/KIKmix.20250701.xlsx"
mix_df = pd.read_excel(MIX_PATH, dtype=str)
mix_df.columns = mix_df.columns.str.strip()
dong_code_col = [col for col in mix_df.columns if "코드" in col][0]
gu_name_col = [col for col in mix_df.columns if "구" in col][0]
mix_df["gu_code"] = mix_df[dong_code_col].str[:5]
gu_map = dict(mix_df[[gu_name_col, "gu_code"]].drop_duplicates().values)

# 4. gu_code 매핑
result["gu_code"] = result["gu_name"].map(gu_map)

# 5. 컬럼 정리 및 저장
result = result[["gu_code", "gu_name", "counts"]]
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
result.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print(f"[저장 완료] → {OUTPUT_PATH}")
