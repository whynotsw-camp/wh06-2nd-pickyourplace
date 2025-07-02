import pandas as pd
import os
import sys

"""
📄 '동' 칼럼만 존재하고 '구' 칼럼이 비어있는 매핑 자동 보완 스크립트

이 스크립트는
행정동 정보가 누락된 행(dong_name 기준)을 자동으로 채우는 역할을 합니다.

구체적으로는:
- gu_code, dong_code, gu_name 이 비어 있는 행에 대해
- src.geocoding.admin_mapper.get_gu_and_gu_codes() 를 사용해 자동으로 서울시 행정동 정보를 유사 매칭하고
- 서울특별시가 아닌 행정구역(예: 전주시, 수원시 등)은 제거한 후
- 최종적으로 같은 경로(OUTPUT_PATH)에 덮어쓰기 저장합니다.

⚠️ 주의: mix 기준 파일은 서울특별시로 필터링된 상태여야 하며,
입력 CSV에는 dong_name 컬럼이 반드시 존재해야 합니다.
"""

# 🔧 경로 설정
MIX_PATH = "data/reference/KIKmix.20250701.xlsx"
INPUT_PATH = "data/processed_counts/bell__counts.csv"
OUTPUT_PATH = "data/processed_counts/bell__counts.csv"

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# ✅ admin_mapper import
from src.geocoding.admin_mapper import get_gu_and_gu_codes

# 📥 데이터 불러오기
df = pd.read_csv(INPUT_PATH, dtype={"gu_code": str, "dong_code": str})
df["dong_name"] = df["dong_name"].astype(str).str.strip()

# ✅ gu_code가 비어 있는 행만 처리 대상
needs_fill = df["gu_code"].isna() | (df["gu_code"] == "")
print(f"🔍 매핑 대상 행 수: {needs_fill.sum()}")

# ✅ 매핑 수행
for i, row in df[needs_fill].iterrows():
    dong_name = row["dong_name"]
    gu_code, dong_code, gu_name = get_gu_and_gu_codes(dong_name)
    df.at[i, "gu_code"] = gu_code
    df.at[i, "dong_code"] = dong_code
    df.at[i, "gu_name"] = gu_name

# ✅ 서울 이외 지역 제거 (dong_code가 '11'로 시작하지 않으면 제외)
before = len(df)
df = df[df["dong_code"].astype(str).str.startswith("11")]
after = len(df)
print(f"🚫 서울 외 지역 제거됨: {before - after}건")

# 📤 저장
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print(f"✅ 최종 저장 완료: {OUTPUT_PATH} (행 개수: {len(df)})")
