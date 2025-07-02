import os
import glob
import pandas as pd

# 입력과 출력 디렉토리 설정
INPUT_DIR = "data/processed/"
OUTPUT_DIR = "data/processed_counts/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# file_paths = glob.glob(os.path.join(INPUT_DIR, "*__processed.csv"))
#file_paths = glob.glob(os.path.join(INPUT_DIR, "bus_stop__processed.csv"))

# ✅ 필요한 파일만 직접 지정
target_files = ["market__processed.csv", "pharmacy__processed.csv"]
file_paths = [os.path.join(INPUT_DIR, f) for f in target_files]

for file_path in file_paths:
    print(f"[처리 중] {file_path}")
    df = pd.read_csv(file_path)

    # gu_code, dong_code를 nullable 정수형으로 변환
    df["gu_code"] = pd.to_numeric(df["gu_code"], errors="coerce").astype("Int64")
    df["dong_code"] = pd.to_numeric(df["dong_code"], errors="coerce").astype("Int64")

    # 행정동 기준 개수 집계
    count_df = (
        df.groupby(["gu_code", "dong_code", "gu_name", "dong_name"])
        .size()
        .reset_index(name="counts")
    )

    # 저장 파일명 지정
    base_name = os.path.basename(file_path).replace("__processed.csv", "__counts.csv")
    save_path = os.path.join(OUTPUT_DIR, base_name)

    # 저장
    count_df.to_csv(save_path, index=False)
    print(f"[저장 완료] {save_path}")