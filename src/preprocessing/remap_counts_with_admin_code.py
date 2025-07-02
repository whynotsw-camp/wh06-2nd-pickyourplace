"""
📌 data/processed_counts/ 디렉토리 내의 모든 *__counts.csv 파일을 대상으로,
    dong_name (법정동)을 행정동 기준으로 재매핑하여 gu_code, dong_code, dong_name으로 변환합니다.
    기존 파일은 *_before.csv로 백업하고, 새 파일을 기존 파일명 그대로 덮어씁니다.
"""

import pandas as pd
import os
import sys
from glob import glob
import shutil

# 📌 sys.path에 src 경로 추가
sys.path.append(os.path.abspath("src"))

# ✅ 매핑 함수 import
from geocoding.admin_mapper import get_gu_dong_codes

# 📁 디렉토리 및 패턴 설정
INPUT_DIR = "data/processed_counts"
file_list = glob(os.path.join(INPUT_DIR, "*__counts.csv"))

print(f"🔍 처리할 파일 수: {len(file_list)}개")

for file_path in file_list:
    file_name = os.path.basename(file_path)
    backup_path = os.path.join(INPUT_DIR, file_name.replace(".csv", "_before.csv"))

    print(f"\n📂 처리 중: {file_name}")

    # 1️⃣ 기존 파일 백업
    shutil.move(file_path, backup_path)
    print(f"🗃️ 백업 → {backup_path}")

    # 2️⃣ 데이터 불러오기 (백업된 파일에서)
    df = pd.read_csv(backup_path, dtype=str)
    df["dong_name"] = df["dong_name"].str.strip()
    df["gu_name"] = df["gu_name"].str.strip()

    # 🔍 매핑 함수 정의
    def map_codes(row):
        gu = row["gu_name"]
        dong = row["dong_name"]
        gu_code, dong_code, admin_dong = get_gu_dong_codes(gu, dong)
        return pd.Series([gu_code, dong_code, admin_dong])

    # 🧩 매핑 적용
    df[["gu_code", "dong_code", "dong_name"]] = df.apply(map_codes, axis=1)

    # 🧹 서울 외 지역 제거
    before = len(df)
    df = df[df["dong_code"].str.startswith("11", na=False)]
    after = len(df)
    print(f"🚫 서울 외 지역 제거됨: {before - after}건")

    # ✅ 컬럼 순서 재정렬
    first_cols = ["gu_code", "dong_code", "gu_name", "dong_name"]
    df = df[first_cols + [col for col in df.columns if col not in first_cols]]

    # 3️⃣ 매핑 결과를 원래 파일명으로 저장
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"✅ 새 파일 저장 완료: {file_path} (총 {len(df)}행)")
